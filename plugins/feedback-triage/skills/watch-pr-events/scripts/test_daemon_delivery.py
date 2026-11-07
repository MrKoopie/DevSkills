"""Host delivery contracts with controlled daemon responses; no model or GitHub calls."""

import copy
import json
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import daemon_delivery as d
from host_rpc import RPC

CONTEXT = {
    "cwd": "/workspace",
    "model": "gpt-6.1-sol",
    "effort": "high",
    "approval_policy": "on-request",
    "approvals_reviewer": "auto_review",
    "permission_profile": {
        "type": "managed",
        "network": "restricted",
        "file_system": {
            "type": "restricted",
            "entries": [
                {
                    "path": {"type": "special", "value": {"kind": "root"}},
                    "access": "read",
                },
                {"path": {"type": "path", "path": "/workspace"}, "access": "write"},
                {"path": {"type": "path", "path": "/workspace/.git"}, "access": "read"},
            ],
        },
    },
}


class DaemonTest(unittest.TestCase):
    def test_saved_policy_keeps_protected_paths_and_sol_high(self):
        p = d.resume_params("abc", CONTEXT)
        self.assertEqual(p["model"], "gpt-6.1-sol")
        self.assertEqual(p["config"]["model_reasoning_effort"], "high")
        profile = p["config"]["permissions"]["watch_abc"]
        self.assertFalse(profile["network"]["enabled"])
        self.assertEqual(
            profile["filesystem"],
            {":root": "read", "/workspace": "write", "/workspace/.git": "read"},
        )
        self.assertEqual(p["approvalPolicy"], "on-request")
        self.assertEqual(p["approvalsReviewer"], "auto_review")

    def test_unknown_or_unrestricted_policy_is_not_silently_relaxed(self):
        for change in [{"type": "legacy"}, {"network": "enabled"}]:
            c = copy.deepcopy(CONTEXT)
            c["permission_profile"].update(change)
            with self.assertRaises(RuntimeError):
                d.resume_params("abc", c)

    def test_history_waits_for_task_completion(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "rollout.jsonl"
            lines = [
                {"type": "turn_context", "payload": CONTEXT},
                {
                    "type": "event_msg",
                    "payload": {"type": "task_started", "turn_id": "one"},
                },
            ]
            p.write_text("\n".join(map(json.dumps, lines)) + "\n")
            self.assertEqual(d.history(p)[1], "one")
            lines.append(
                {
                    "type": "event_msg",
                    "payload": {"type": "task_complete", "turn_id": "one"},
                }
            )
            p.write_text("\n".join(map(json.dumps, lines)) + "\n")
            self.assertIsNone(d.history(p)[1])

    def delivery(self, kind):
        with tempfile.TemporaryDirectory() as root:
            state = {
                "thread": "abc",
                "state_path": str(Path(root) / "state.json"),
                "daemon_socket": "local",
                "deadline": 99999999999,
            }
            thread = {"id": "abc", "path": "rollout", "status": {"type": "notLoaded"}}
            resumed = {
                "thread": thread,
                "model": CONTEXT["model"],
                "reasoningEffort": "high",
                "cwd": "/workspace",
                "approvalPolicy": "on-request",
                "approvalsReviewer": "auto_review",
                "activePermissionProfile": {"id": "watch_abc"},
            }
            if kind == "policy_changed":
                resumed["model"] = "wrong"
            replies = [{"thread": thread}, resumed, {"turn": {"id": "owned"}}, {}]
            if kind == "writer_busy":
                replies.insert(
                    1,
                    d.RPCError(
                        {
                            "code": -32600,
                            "message": "thread already has an active writer",
                        }
                    ),
                )
            events = [
                {
                    "method": "turn/completed",
                    "params": {"turn": {"id": "other", "status": "completed"}},
                },
                {"method": "turn/started", "params": {"turn": {"id": "owned"}}},
                {
                    "method": "turn/completed",
                    "params": {"turn": {"id": "owned", "status": "completed"}},
                },
            ]
            if kind == "input":
                events = [{"id": 99, "method": "item/tool/requestUserInput"}]
            if kind == "disconnect":
                events = [EOFError("Disconnected")]
            if kind == "shutdown":
                events = [SystemExit(0)]
            with (
                patch.object(d, "RPC") as rpc,
                patch.object(d, "history", return_value=(CONTEXT, None)),
                patch.object(d.time, "sleep") as sleep,
            ):
                responses = iter(replies)

                def respond(*args):
                    if kind == "expired_during_handoff" and args[0] == "thread/resume":
                        state["deadline"] = 1
                    response = next(responses, {})
                    if isinstance(response, Exception):
                        raise response
                    return response

                rpc.return_value.call.side_effect = respond
                rpc.return_value.recv.side_effect = events
                if kind in ("complete", "writer_busy"):
                    self.assertIn("owned", d.deliver(state, "fixed metadata"))
                else:
                    with self.assertRaises(
                        SystemExit
                        if kind == "shutdown"
                        else EOFError
                        if kind == "disconnect"
                        else d.NeedsInput
                        if kind == "input"
                        else RuntimeError
                    ):
                        d.deliver(state, "fixed metadata")
                receipt = json.loads(
                    Path(state["state_path"]).with_suffix(".delivery.json").read_text()
                )
                if kind in ("complete", "writer_busy"):
                    self.assertEqual(receipt["status"], "completed")
                    self.assertIn("started_at", receipt)
                    self.assertIn("completed_at", receipt)
                    starts = [
                        call
                        for call in rpc.return_value.call.call_args_list
                        if call.args[0] == "turn/start"
                    ]
                    self.assertEqual(len(starts), 1)
                    self.assertEqual(
                        sleep.call_count, 1 if kind == "writer_busy" else 0
                    )
                elif kind in ("policy_changed", "expired_during_handoff"):
                    self.assertEqual(receipt["status"], "failed_before_start")
                    self.assertNotIn(
                        "turn/start",
                        [c.args[0] for c in rpc.return_value.call.call_args_list],
                    )
                elif kind in ("disconnect", "shutdown"):
                    self.assertEqual(receipt["status"], "delivery_uncertain")
                    if kind == "shutdown":
                        self.assertEqual(receipt["error_type"], "SystemExit")
                        self.assertIn(
                            "turn/interrupt",
                            [c.args[0] for c in rpc.return_value.call.call_args_list],
                        )
                elif kind == "input":
                    self.assertEqual(receipt["status"], "needs_input")

    def test_writer_lock_waits_without_duplicate_turns(self):
        self.delivery("writer_busy")

    def test_actual_matching_turn_completion_is_required(self):
        self.delivery("complete")

    def test_policy_mismatch_refuses_turn_start(self):
        self.delivery("policy_changed")

    def test_disconnect_after_start_is_uncertain_without_retry(self):
        self.delivery("disconnect")

    def test_interactive_request_stops_owned_turn(self):
        self.delivery("input")

    def test_shutdown_records_uncertainty_before_interrupting_owned_turn(self):
        self.delivery("shutdown")

    def test_deadline_expiring_during_handoff_refuses_turn_start(self):
        self.delivery("expired_during_handoff")

    def test_expired_watch_refuses_delivery_before_loading_or_starting_a_turn(self):
        with tempfile.TemporaryDirectory() as root:
            state = dict(
                thread="abc",
                state_path=str(Path(root) / "state.json"),
                daemon_socket="local",
                deadline=1,
            )
            with (
                patch.object(d, "RPC") as rpc,
                self.assertRaisesRegex(RuntimeError, "deadline expired"),
            ):
                d.deliver(state, "expired")
            rpc.assert_not_called()
            record = json.loads(
                Path(state["state_path"]).with_suffix(".delivery.json").read_text()
            )
            self.assertEqual(record["status"], "failed_before_start")

    def test_websocket_fragmentation_ping_and_extended_payload(self):
        a, b = socket.socketpair()
        r = RPC.__new__(RPC)
        r.s = a
        r.buf = b""
        r.pending = []
        try:
            b.sendall(b'\x01\x05{"res' + b"\x89\x01p" + b'\x80\x08ult":1}\n')
            self.assertEqual(r.recv(), {"result": 1})
            payload = json.dumps({"result": "x" * 200}).encode()
            b.sendall(b"\x81\x7e" + len(payload).to_bytes(2, "big") + payload)
            self.assertEqual(r.recv(), {"result": "x" * 200})
        finally:
            a.close()
            b.close()


if __name__ == "__main__":
    unittest.main()
