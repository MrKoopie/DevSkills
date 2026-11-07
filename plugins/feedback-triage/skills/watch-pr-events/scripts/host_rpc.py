"""Local-only App Server JSON-RPC over its documented Unix WebSocket transport."""

import base64
import hashlib
import json
import os
import socket
import struct
from pathlib import Path


class RPCError(RuntimeError):
    def __init__(self, error):
        self.code = error.get("code")
        self.message = error.get("message", "")
        super().__init__(f"App Server request rejected ({self.code})")


class RPC:
    def __init__(self, path):
        path = Path(path)
        if path.stat().st_uid != os.getuid():
            raise RuntimeError("Socket is not owned by this user")
        self.s = socket.socket(socket.AF_UNIX)
        self.s.settimeout(30)
        self.s.connect(str(path))
        self.buf = b""
        self.seq = 0
        self.pending = []
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(
            (
                f"GET / HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        while b"\r\n\r\n" not in self.buf:
            data = self.s.recv(65536)
            if not data:
                raise EOFError("Daemon closed during WebSocket handshake")
            self.buf += data
            if len(self.buf) > 65536:
                raise RuntimeError("Oversized WebSocket handshake")
        header, self.buf = self.buf.split(b"\r\n\r\n", 1)
        accept = base64.b64encode(
            hashlib.sha1(
                (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()
            ).digest()
        )
        if not header.startswith(b"HTTP/1.1 101") or accept not in header:
            raise RuntimeError("Invalid local WebSocket handshake")
        self.call(
            "initialize",
            {
                "clientInfo": {"name": "watch_pr_events", "version": "2.0"},
                "capabilities": {"experimentalApi": True},
            },
        )
        self.send({"method": "initialized"})

    def take(self, n):
        while len(self.buf) < n:
            data = self.s.recv(65536)
            if not data:
                raise EOFError("Daemon connection closed")
            self.buf += data
        data, self.buf = self.buf[:n], self.buf[n:]
        return data

    def frame(self, payload, opcode=1):
        n = len(payload)
        head = bytes([128 | opcode])
        head += (
            bytes([128 | n])
            if n < 126
            else bytes([128 | 126]) + struct.pack("!H", n)
            if n < 65536
            else bytes([128 | 127]) + struct.pack("!Q", n)
        )
        mask = os.urandom(4)
        self.s.sendall(
            head + mask + bytes(x ^ mask[i % 4] for i, x in enumerate(payload))
        )

    def send(self, value):
        self.frame(json.dumps(value).encode())

    def _recv(self):
        fragments = b""
        while True:
            a, b = self.take(2)
            n = b & 127
            if n == 126:
                n = struct.unpack("!H", self.take(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", self.take(8))[0]
            if n > 16 * 1024 * 1024:
                raise RuntimeError("Oversized local message")
            mask = self.take(4) if b & 128 else None
            data = self.take(n)
            if mask:
                data = bytes(x ^ mask[i % 4] for i, x in enumerate(data))
            opcode = a & 15
            if opcode == 8:
                raise EOFError("Daemon WebSocket closed")
            if opcode == 9:
                self.frame(data, 10)
                continue
            if opcode == 10:
                continue
            if opcode not in [0, 1]:
                raise RuntimeError("Unsupported WebSocket message")
            fragments += data
            if a & 128:
                return json.loads(fragments)

    def call(self, method, params):
        self.seq += 1
        i = self.seq
        self.send({"id": i, "method": method, "params": params})
        while True:
            r = self._recv()
            if r.get("id") == i and "method" not in r:
                if "error" in r:
                    raise RPCError(r["error"])
                return r["result"]
            if "id" in r and "method" in r:
                raise RuntimeError("Daemon requires interactive input")
            self.pending.append(r)

    def recv(self):
        return self.pending.pop(0) if self.pending else self._recv()

    def close(self):
        self.s.close()
