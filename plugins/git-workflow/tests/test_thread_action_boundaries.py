"""Verify rejected or uncertain review-thread actions cannot lead to extra writes."""

import contextlib
import copy
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import process_threads


class ThreadActionBoundaryTests(unittest.TestCase):
    def test_rejected_thread_actions_cannot_be_prepared_for_writes(self):
        baseline_data = {"head_sha": "abc", "records": [
            {"source": "inline", "id": "10", "thread_id": "T", "author": "reviewer", "created_at": "1"}
        ]}
        baseline_plan = {"provider": "github", "head_sha": "abc", "actions": [
            {"thread_id": "T", "last_comment_id": "10", "action": "reply", "body": "Reason"}
        ]}

        for case in ("missing", "empty", "duplicate", "unknown", "resolved", "outdated", "blank", "unsupported"):
            with self.subTest(case=case):
                plan = copy.deepcopy(baseline_plan)
                data = copy.deepcopy(baseline_data)

                if case == "missing":
                    plan.pop("actions")
                elif case == "empty":
                    plan["actions"] = []
                elif case == "duplicate":
                    plan["actions"].append(copy.deepcopy(plan["actions"][0]))
                elif case == "unknown":
                    plan["actions"][0]["thread_id"] = "other"
                elif case in ("resolved", "outdated"):
                    data["records"][0][case] = True
                elif case == "blank":
                    plan["actions"][0]["body"] = "   "
                else:
                    plan["actions"][0]["action"] = "delete"

                with self.assertRaises(ValueError):
                    process_threads.validate_plan(plan, data, "me")

    def test_non_object_thread_action_is_rejected_as_invalid_plan(self):
        data = {"head_sha": "abc", "records": [
            {"source": "inline", "id": "10", "thread_id": "T", "author": "reviewer", "created_at": "1"}
        ]}
        valid_action = {"thread_id": "T", "last_comment_id": "10", "action": "reply", "body": "Reason"}

        for malformed_action in (None, "reply", [], 7, True):
            with self.subTest(action=malformed_action):
                plan = {"provider": "github", "repo": "o/r", "number": 1, "head_sha": "abc", "actions": [valid_action, malformed_action]}

                with self.assertRaisesRegex(ValueError, "Each action must be an object"):
                    process_threads.validate_plan(plan, data, "me")

                with patch.object(process_threads, "github", return_value=data), \
                     patch.object(process_threads, "run", return_value={"login": "me"}), \
                     patch.object(process_threads, "perform") as perform, \
                     patch.object(sys, "stdin", io.StringIO(json.dumps(plan))), \
                     patch.object(sys, "argv", ["process_threads.py", "--execute"]), \
                     contextlib.redirect_stderr(io.StringIO()):
                    result = process_threads.main()

                self.assertEqual(result, 1)
                perform.assert_not_called()

    def test_write_failures_stop_without_automatic_retry(self):
        responses = (
            subprocess.CompletedProcess(["gh"], 1, "", "permission denied"),
            subprocess.CompletedProcess(["gh"], 0, "invalid JSON", ""),
            subprocess.CompletedProcess(["gh"], 0, json.dumps({"errors": [{"message": "rejected"}]}), ""),
        )

        for response in responses:
            with self.subTest(response=response):
                with patch.object(process_threads.subprocess, "run", return_value=response) as run:
                    with self.assertRaises(RuntimeError):
                        process_threads.cli(["gh", "api", "graphql"])

                run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
