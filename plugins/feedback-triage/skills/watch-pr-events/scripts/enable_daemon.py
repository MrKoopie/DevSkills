"""Explicitly migrate one authorized watch without racing an active delivery."""

import argparse
import fcntl
import json
import os
import signal
import time
from pathlib import Path

import watch
from host_rpc import RPC
from state_io import delivery_guard


def eligible(state):
    if not state.get("until_ready") or state["status"] not in (
        "starting",
        "watching",
        "queued",
    ):
        raise RuntimeError(
            "Watch is not a model-free waiter or inspected delivered watch"
        )
    if time.time() >= state["deadline"]:
        raise RuntimeError("Original deadline expired")


def prepare(path, daemon_socket, canary=False):
    path = Path(path).resolve()
    state = json.loads(path.read_text())
    eligible(state)
    rpc = RPC(daemon_socket)
    try:
        thread = rpc.call(
            "thread/read", {"threadId": state["thread"], "includeTurns": False}
        )["thread"]
        if thread["id"] != state["thread"] or not thread.get("path"):
            raise RuntimeError("Wrong daemon thread")
    finally:
        rpc.close()
    # The capability check can take time. Revalidate under both control and
    # delivery locks; the watcher holds the latter through notify and receipt.
    with path.with_suffix(".lock").open("a") as control:
        fcntl.flock(control, fcntl.LOCK_EX)
        with delivery_guard(path, blocking=False):
            current = json.loads(path.read_text())
            eligible(current)
            if any(
                current.get(key) != state.get(key)
                for key in ("repo", "number", "thread", "deadline")
            ):
                raise RuntimeError("Watch changed during migration")
            if watch.alive(current):
                if current.get("handoff_protocol") != 1:
                    raise RuntimeError(
                        "Old waiter lacks delivery synchronization; stop and inspect it first"
                    )
                os.kill(current["pid"], signal.SIGTERM)
                deadline = time.monotonic() + 8
                while watch.alive(current) and time.monotonic() < deadline:
                    time.sleep(0.1)
                if watch.alive(current):
                    raise RuntimeError(
                        "Old waiter did not exit; no replacement started"
                    )
                # Only our verified model-free waiter's cancellation is eligible.
                state = json.loads(path.read_text())
                if state["status"] == "cancelled":
                    state["status"] = "watching"
            else:
                state = current
            eligible(state)
            state.setdefault("delivery_migrations", []).append(
                {
                    "at": time.time(),
                    "from": state.get("delivery", "queue"),
                    "to": "daemon",
                    "deadline": state["deadline"],
                }
            )
            state.update(
                status="queued", delivery="daemon", daemon_socket=daemon_socket
            )
            if canary:
                state["canary"] = True
            watch.atomic(path, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--canary", action="store_true")
    parser.add_argument(
        "--daemon-socket",
        default=str(
            Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
            / "app-server-control/app-server-control.sock"
        ),
    )
    args = parser.parse_args()
    path = args.state.resolve()
    prepare(path, args.daemon_socket, args.canary)
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


if __name__ == "__main__":
    main()
