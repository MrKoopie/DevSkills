"""Explicitly migrate one authorized watch to host delivery without extending its deadline."""

import argparse
import json
import os
import signal
import time
from pathlib import Path

import watch
from host_rpc import RPC

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--state", type=Path, required=True)
p.add_argument("--canary", action="store_true")
p.add_argument(
    "--daemon-socket",
    default=str(Path.home() / ".codex/app-server-control/app-server-control.sock"),
)
a = p.parse_args()
path = a.state.resolve()
state = json.loads(path.read_text())
if not state.get("until_ready") or state["status"] in (
    "delivery_pending",
    "delivery_uncertain",
    "cancelled",
    "expired",
    "complete",
    "closed",
    "merged",
):
    raise RuntimeError(
        "Watch is not an eligible waiting/delivered ongoing watch; inspect it before migration"
    )
if time.time() >= state["deadline"]:
    raise RuntimeError("Original deadline expired")
rpc = RPC(a.daemon_socket)
try:
    thread = rpc.call(
        "thread/read", {"threadId": state["thread"], "includeTurns": False}
    )["thread"]
    if thread["id"] != state["thread"] or not thread.get("path"):
        raise RuntimeError("Wrong daemon thread")
finally:
    rpc.close()
# Stop only the verified model-free waiter. Never terminate a pending/active delivery.
if watch.alive(state):
    os.kill(state["pid"], signal.SIGTERM)
    deadline = time.monotonic() + 8
    while watch.alive(state) and time.monotonic() < deadline:
        time.sleep(0.1)
    if watch.alive(state):
        raise RuntimeError("Old waiter did not exit; no replacement started")
state = json.loads(path.read_text())
state.setdefault("delivery_migrations", []).append(
    {
        "at": time.time(),
        "from": state.get("delivery", "queue"),
        "to": "daemon",
        "deadline": state["deadline"],
    }
)
state.update(status="queued", delivery="daemon", daemon_socket=a.daemon_socket)
if a.canary:
    state["canary"] = True
watch.atomic(path, state)
os.execv(
    os.sys.executable,
    [
        os.sys.executable,
        str(Path(__file__).with_name("watch.py")),
        "resume",
        "--state",
        str(path),
    ],
)
