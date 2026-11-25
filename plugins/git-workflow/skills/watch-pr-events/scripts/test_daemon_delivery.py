"""Host delivery contracts with controlled daemon responses; no model or GitHub calls."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import daemon_delivery as d

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

    def test_project_root_rules_keep_each_saved_scope(self):
        c = copy.deepcopy(CONTEXT)
        c["permission_profile"]["file_system"]["entries"].extend(
            {
                "path": {
                    "type": "special",
                    "value": {"kind": "project_roots", "subpath": subpath},
                },
                "access": access,
            }
            for subpath, access in (
                (None, "read"),
                ("src", "write"),
                ("src/private", "deny"),
            )
        )
        p = d.resume_params("abc", c)["config"]["permissions"]["watch_abc"]
        self.assertEqual(
            p["filesystem"],
            {
                ":root": "read",
                "/workspace": "write",
                "/workspace/.git": "read",
                ":workspace_roots": {".": "read", "src": "write", "src/private": "deny"},
            },
        )

    def test_unrepresentable_saved_special_scope_is_rejected(self):
        for subpath in (
            "",
            "../elsewhere",
            "/elsewhere",
            "./src",
            "~/elsewhere",
            "src/*",
        ):
            with self.subTest(subpath=subpath):
                c = copy.deepcopy(CONTEXT)
                c["permission_profile"]["file_system"]["entries"].append(
                    {
                        "path": {
                            "type": "special",
                            "value": {"kind": "project_roots", "subpath": subpath},
                        },
                        "access": "write",
                    }
                )
                with self.assertRaisesRegex(RuntimeError, "saved filesystem scope"):
                    d.resume_params("abc", c)

    def test_conflicting_saved_project_scopes_are_rejected(self):
        c = copy.deepcopy(CONTEXT)
        c["permission_profile"]["file_system"]["entries"].extend(
            {
                "path": {
                    "type": "special",
                    "value": {"kind": "project_roots", "subpath": "private"},
                },
                "access": access,
            }
            for access in ("deny", "write")
        )
        with self.assertRaisesRegex(RuntimeError, "saved filesystem scope"):
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
                    "params": {
                        "threadId": "abc",
                        "turn": {"id": "other", "status": "completed"},
                    },
                },
                {
                    "method": "turn/started",
                    "params": {"threadId": "abc", "turn": {"id": "owned"}},
                },
                {
                    "method": "turn/completed",
                    "params": {
                        "threadId": "abc",
                        "turn": {"id": "owned", "status": "completed"},
                    },
                },
            ]
            if kind == "input":
                events = [{"id": 99, "method": "item/tool/requestUserInput"}]
            if kind == "disconnect":
                events = [EOFError("Disconnected")]
            if kind == "missing_start":
                events.pop(1)
            if kind == "other_thread_start":
                events[1]["params"]["threadId"] = "different-chat"
            if kind in ("canary", "other_turn_canary"):
                state["canary"] = True
                events.insert(
                    -1,
                    {
                        "method": "item/completed",
                        "params": {
                            "threadId": "abc",
                            "turnId": "owned" if kind == "canary" else "other",
                            "completedAtMs": 1000,
                            "item": {
                                "type": "agentMessage",
                                "text": "HOST_CONTINUATION_OK",
                            },
                        },
                    },
                )
            with (
                patch.object(d, "RPC") as rpc,
                patch.object(d, "history", return_value=(CONTEXT, None)),
            ):
                rpc.return_value.call.side_effect = replies
                rpc.return_value.recv.side_effect = events
                if kind in ("complete", "writer_busy", "canary"):
                    self.assertIn("owned", d.deliver(state, "fixed metadata"))
                else:
                    with self.assertRaises(Exception):
                        d.deliver(state, "fixed metadata")
                receipt = json.loads(
                    Path(state["state_path"]).with_suffix(".delivery.json").read_text()
                )
                if kind in ("complete", "writer_busy", "canary"):
                    self.assertEqual(receipt["status"], "completed")
                    self.assertIn("started_at", receipt)
                    self.assertIn("completed_at", receipt)
                    if kind == "canary":
                        self.assertTrue(receipt["canary_verified"])
                elif kind == "policy_changed":
                    self.assertEqual(receipt["status"], "failed_before_start")
                    self.assertNotIn(
                        "turn/start",
                        [c.args[0] for c in rpc.return_value.call.call_args_list],
                    )
                elif kind == "disconnect":
                    self.assertEqual(receipt["status"], "delivery_uncertain")
                elif kind in (
                    "input",
                    "missing_start",
                    "other_thread_start",
                    "other_turn_canary",
                ):
                    self.assertEqual(receipt["status"], "needs_input")
                    self.assertNotIn("completed_at", receipt)
                    if kind != "input":
                        self.assertNotIn(
                            "turn/interrupt",
                            [c.args[0] for c in rpc.return_value.call.call_args_list],
                        )

    def test_writer_lock_hands_off_once_without_starting_a_second_writer(self):
        with tempfile.TemporaryDirectory() as root:
            state = {
                "thread": "abc",
                "state_path": str(Path(root) / "state.json"),
                "daemon_socket": "local",
                "deadline": 99999999999,
            }
            thread = {"id": "abc", "path": "rollout", "status": {"type": "notLoaded"}}
            with (
                patch.object(d, "RPC") as rpc,
                patch.object(d, "history", return_value=(CONTEXT, None)),
                patch(
                    "owner_delivery.deliver", return_value="owner completed"
                ) as owner,
            ):
                rpc.return_value.call.side_effect = [
                    {"thread": thread},
                    d.RPCError(
                        {
                            "code": -32600,
                            "message": "thread already has an active writer",
                        }
                    ),
                    {},
                ]
                self.assertEqual(d.deliver(state, "fixed metadata"), "owner completed")
                owner.assert_called_once()
                methods = [c.args[0] for c in rpc.return_value.call.call_args_list]
                self.assertEqual(methods.count("thread/resume"), 1)
                self.assertNotIn("turn/start", methods)

    def test_active_turn_is_queued_for_owner_without_interrupting_it(self):
        with tempfile.TemporaryDirectory() as root:
            state = {
                "thread": "abc",
                "state_path": str(Path(root) / "state.json"),
                "daemon_socket": "local",
                "deadline": 99999999999,
            }
            thread = {"id": "abc", "path": "rollout", "status": {"type": "notLoaded"}}
            with (
                patch.object(d, "RPC") as rpc,
                patch.object(
                    d, "history", return_value=(CONTEXT, "existing-user-turn")
                ),
                patch(
                    "owner_delivery.deliver", return_value="owner completed"
                ) as owner,
            ):
                rpc.return_value.call.side_effect = [{"thread": thread}, {}]
                self.assertEqual(d.deliver(state, "fixed metadata"), "owner completed")
                owner.assert_called_once()
                methods = [c.args[0] for c in rpc.return_value.call.call_args_list]
                self.assertNotIn("turn/interrupt", methods)
                self.assertNotIn("thread/resume", methods)
                self.assertNotIn("turn/start", methods)

    def test_actual_matching_turn_completion_is_required(self):
        self.delivery("complete")

    def test_completion_without_start_stops_for_inspection(self):
        self.delivery("missing_start")

    def test_start_from_different_chat_cannot_confirm_delivery(self):
        self.delivery("other_thread_start")

    def test_canary_requires_marker_from_the_matching_turn(self):
        self.delivery("canary")
        self.delivery("other_turn_canary")

    def test_policy_mismatch_refuses_turn_start(self):
        self.delivery("policy_changed")

    def test_disconnect_after_start_is_uncertain_without_retry(self):
        self.delivery("disconnect")

    def test_interactive_request_stops_owned_turn(self):
        self.delivery("input")

    def check_deadline_during_handoff(self, elapsed_during, expected_status):
        with tempfile.TemporaryDirectory() as root:
            state = {
                "thread": "abc",
                "state_path": str(Path(root) / "state.json"),
                "daemon_socket": "local",
                "deadline": 1000,
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
            now = 999

            def call(method, _params):
                nonlocal now
                if method == "thread/read":
                    return {"thread": thread}
                if method == "thread/resume":
                    if elapsed_during == "load":
                        now = 1000
                    return resumed
                if method == "thread/unsubscribe":
                    return {}
                raise AssertionError(method)

            original_receipt = d.receipt

            def write_receipt(path, record):
                nonlocal now
                original_receipt(path, record)
                if elapsed_during == "receipt" and record["status"] == "start_pending":
                    now = 1000

            with (
                patch.object(d, "RPC") as rpc,
                patch.object(d, "history", return_value=(CONTEXT, None)),
                patch.object(d.time, "time", side_effect=lambda: now),
                patch.object(d, "receipt", side_effect=write_receipt),
            ):
                rpc.return_value.call.side_effect = call
                with self.assertRaisesRegex(
                    RuntimeError, "deadline expired before turn start"
                ):
                    d.deliver(state, "fixed metadata")
            receipt = json.loads(
                Path(state["state_path"]).with_suffix(".delivery.json").read_text()
            )
            self.assertEqual(receipt["status"], expected_status)

    def test_daemon_does_not_start_turn_when_loading_crosses_the_deadline(self):
        self.check_deadline_during_handoff("load", "failed_before_start")

    def test_daemon_does_not_start_turn_when_intent_receipt_crosses_the_deadline(self):
        self.check_deadline_during_handoff("receipt", "needs_input")


if __name__ == "__main__":
    unittest.main()
