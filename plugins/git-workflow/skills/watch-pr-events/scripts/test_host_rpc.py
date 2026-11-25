"""Local WebSocket receive tests with scripted socket reads."""

import json
import socket
import unittest
from collections import deque

from host_rpc import RPC


class ScriptedSocket:
    def __init__(self, reads):
        self.reads = deque(reads)
        self.sent = []

    def recv(self, size):
        if not self.reads:
            return b""
        result = self.reads.popleft()
        if isinstance(result, Exception):
            raise result
        if len(result) > size:
            self.reads.appendleft(result[size:])
        return result[:size]

    def sendall(self, data):
        self.sent.append(data)


class HostRPCTest(unittest.TestCase):
    def connect(self, *reads):
        rpc = RPC.__new__(RPC)
        rpc.s = ScriptedSocket(reads)
        rpc.buf = bytearray()
        rpc.fragments = bytearray()
        rpc.pending = []
        return rpc

    def test_resumes_frame_after_partial_read_times_out(self):
        expected = {"result": "x" * 200}
        payload = json.dumps(expected).encode()
        mask = b"abcd"
        masked_payload = bytes(value ^ mask[i % 4] for i, value in enumerate(payload))
        frame = b"\x81\xfe" + len(payload).to_bytes(2, "big") + mask + masked_payload

        for field, offset in (
            ("header", 1),
            ("extended length", 3),
            ("mask", 6),
            ("payload", 9),
        ):
            with self.subTest(field=field):
                rpc = self.connect(frame[:offset], socket.timeout(), frame[offset:])
                with self.assertRaises(socket.timeout):
                    rpc.recv()
                self.assertEqual(rpc.recv(), expected)

    def test_resumes_fragmented_message_after_timeout_with_intervening_ping(self):
        rpc = self.connect(
            b'\x01\x05{"res' + b"\x89\x01p",
            socket.timeout(),
            b'\x80\x08ult":1}\n' + b'\x81\x02{}',
        )
        with self.assertRaises(socket.timeout):
            rpc.recv()

        (pong,) = rpc.s.sent
        self.assertEqual(pong[:2], b"\x8a\x81")
        self.assertEqual(pong[6] ^ pong[2], ord("p"))
        self.assertEqual(rpc.recv(), {"result": 1})
        self.assertEqual(rpc.recv(), {})

    def test_idle_timeout_allows_next_read(self):
        rpc = self.connect(socket.timeout(), b'\x81\x02{}')
        with self.assertRaises(socket.timeout):
            rpc.recv()

        self.assertEqual(rpc.recv(), {})

    def test_rejects_oversized_frame_from_header(self):
        rpc = self.connect(b"\x81\x7f" + (16 * 1024 * 1024 + 1).to_bytes(8, "big"))
        with self.assertRaisesRegex(RuntimeError, "Oversized local message"):
            rpc.recv()


if __name__ == "__main__":
    unittest.main()
