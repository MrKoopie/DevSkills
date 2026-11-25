import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import owner_delivery as o
from daemon_delivery import receipt


def rows(marker, done=True):
    items = [
        {
            "type": "event_msg",
            "timestamp": "start",
            "payload": {"type": "task_started", "turn_id": "owned"},
        },
        {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": marker}],
            },
        },
        {
            "type": "event_msg",
            "timestamp": "unrelated",
            "payload": {"type": "task_complete", "turn_id": "different"},
        },
    ]
    if done:
        items.append(
            {
                "type": "event_msg",
                "timestamp": "end",
                "payload": {
                    "type": "task_complete",
                    "turn_id": "owned",
                    "last_agent_message": "HOST_CONTINUATION_OK",
                },
            }
        )
    return "\n".join(map(json.dumps, items)) + "\n"


class Tests(unittest.TestCase):
    def test_completion_requires_matching_message_and_turn(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "rollout"
            p.write_text(rows("unique", False))
            self.assertNotIn("completed_at", o.observe(p, "unique"))
            self.assertIsNone(o.observe(p, "other"))
            p.write_text(rows("unique"))
            self.assertEqual(o.observe(p, "unique")["turn_id"], "owned")
            self.assertEqual(o.observe(p, "unique")["completed_at"], "end")

    def test_owner_queue_canary_requires_actual_completed_turn(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root)
            rpc = Mock()
            record = {}
            state = {"thread": "abc", "deadline": time.time() + 10, "canary": True}

            def call(method, args):
                if method == "thread/queue/add":
                    (p / "rollout").write_text(rows(args["input"][0]["text"]))
                    return {"queuedSubmission": {"id": "queued"}}
                if method == "thread/read":
                    return {"thread": {"id": "abc", "path": str(p / "rollout")}}
                self.fail("Unexpected request: " + method)

            rpc.call.side_effect = call
            result = o.deliver(rpc, state, "test", record, p / "receipt.json", receipt)
            self.assertIn("owned", result)
            saved = json.loads((p / "receipt.json").read_text())
            self.assertEqual(saved["status"], "completed")
            self.assertTrue(saved["canary_verified"])
            self.assertEqual(
                [c.args[0] for c in rpc.call.call_args_list].count("thread/queue/add"),
                1,
            )
            self.assertNotIn(
                "thread/resume", [c.args[0] for c in rpc.call.call_args_list]
            )

    def test_queue_acknowledgement_alone_is_not_success(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "receipt.json"
            record = {}
            rpc = Mock()
            rpc.call.return_value = {"queuedSubmission": {"id": "queued"}}
            with patch.object(o.time, "time", side_effect=[999, 999, 1000]):
                with self.assertRaisesRegex(RuntimeError, "owner message pending"):
                    o.deliver(
                        rpc,
                        {"thread": "abc", "deadline": 1000},
                        "test",
                        record,
                        p,
                        receipt,
                    )
            self.assertEqual(json.loads(p.read_text())["status"], "queued_for_owner")
            self.assertNotIn("completed_at", record)

    def test_expired_delivery_never_adds_an_owner_queue_message(self):
        with tempfile.TemporaryDirectory() as root:
            rpc = Mock()
            with self.assertRaisesRegex(
                RuntimeError, "deadline expired before owner queueing"
            ):
                o.deliver(
                    rpc,
                    {"thread": "abc", "deadline": 0},
                    "test",
                    {},
                    Path(root) / "receipt.json",
                    receipt,
                )
            rpc.call.assert_not_called()

    def test_queue_disconnect_is_not_retried(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "receipt.json"
            rpc = Mock()
            rpc.call.side_effect = EOFError("closed")
            with self.assertRaises(EOFError):
                o.deliver(
                    rpc,
                    {"thread": "abc", "deadline": time.time() + 10},
                    "test",
                    {},
                    p,
                    receipt,
                )
            self.assertEqual(rpc.call.call_count, 1)
            self.assertEqual(json.loads(p.read_text())["status"], "queue_pending")


if __name__ == "__main__":
    unittest.main()
