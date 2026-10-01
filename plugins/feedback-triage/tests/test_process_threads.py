import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("process_threads", SCRIPTS / "process_threads.py")
process_threads = importlib.util.module_from_spec(spec)
spec.loader.exec_module(process_threads)


class ProcessThreadsTests(unittest.TestCase):
    def test_explicitly_revalidated_reply_can_address_historical_thread(self):
        for state in ("outdated", "resolved"):
            with self.subTest(state=state):
                record = {
                    "source": "inline",
                    "id": "10",
                    "thread_id": "T",
                    "author": "reviewer",
                    "created_at": "2026-09-24T10:00:00Z",
                    "outdated": state == "outdated",
                    "resolved": state == "resolved",
                }
                data = {"head_sha": "abc", "records": [record]}
                plan = {"provider": "github", "head_sha": "abc", "actions": [
                    {"thread_id": "T", "last_comment_id": "10", "action": "reply", "body": "Fixed in abc.", "revalidated": True}
                ]}

                prepared = process_threads.validate_plan(plan, data, "me")

                self.assertEqual(prepared[0][1]["id"], "10")

                plan["actions"][0]["revalidated"] = "true"

                with self.assertRaisesRegex(ValueError, "outdated|already resolved"):
                    process_threads.validate_plan(plan, data, "me")

    def test_outdated_thread_can_be_resolved_after_explicit_revalidation(self):
        data = {"head_sha": "abc", "records": [
            {"source": "inline", "id": "10", "thread_id": "T", "author": "reviewer", "created_at": "1", "outdated": True, "resolved": False},
            {"source": "inline", "id": "11", "thread_id": "T", "author": "me", "created_at": "2", "outdated": True, "resolved": False},
        ]}
        action = {"thread_id": "T", "last_comment_id": "11", "action": "resolve", "revalidated": True}
        plan = {"provider": "github", "head_sha": "abc", "actions": [action]}

        self.assertEqual(process_threads.validate_plan(plan, data, "me")[0][0], action)

        for marker in (None, "true"):
            with self.subTest(marker=marker):
                action["revalidated"] = marker

                with self.assertRaisesRegex(ValueError, "outdated"):
                    process_threads.validate_plan(plan, data, "me")

    def test_already_resolved_thread_cannot_be_resolved_again(self):
        data = {"head_sha": "abc", "records": [
            {"source": "inline", "id": "10", "thread_id": "T", "author": "reviewer", "created_at": "1", "outdated": True, "resolved": True},
        ]}
        plan = {"provider": "github", "head_sha": "abc", "actions": [
            {"thread_id": "T", "last_comment_id": "10", "action": "resolve", "revalidated": True}
        ]}

        with self.assertRaisesRegex(ValueError, "already resolved"):
            process_threads.validate_plan(plan, data, "me")

    def test_write_timeout_requires_remote_inspection_before_retry(self):
        command = ["gh", "api", "-X", "POST", "repos/o/r/pulls/4/comments/10/replies"]

        with patch.object(process_threads.subprocess, "run", side_effect=subprocess.TimeoutExpired(command, 300)) as cli:
            with self.assertRaisesRegex(RuntimeError, "inspect the thread before retrying"):
                process_threads.cli(command)

        self.assertEqual(cli.call_args.kwargs["timeout"], 300)

    def test_github_reply_targets_root_comment_and_preserves_thread(self):
        data = {
            "head_sha": "abc",
            "records": [
                {"source": "inline", "id": "10", "thread_id": "T", "in_reply_to_id": None, "author": "reviewer", "created_at": "1", "url": "https://example/thread"},
                {"source": "inline", "id": "11", "thread_id": "T", "in_reply_to_id": 10, "author": "reviewer", "created_at": "2", "url": "https://example/thread"},
            ],
        }
        plan = {"provider": "github", "repo": "o/r", "number": 4, "head_sha": "abc", "actions": [
            {"thread_id": "T", "last_comment_id": "11", "action": "reply", "body": "Fixed in abc."}
        ]}
        prepared = process_threads.validate_plan(plan, data, "me")
        commands = []

        def fake_run(command, **_):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, json.dumps({"html_url": "https://example/reply"}), "")

        with patch.object(process_threads.subprocess, "run", side_effect=fake_run):
            result = process_threads.perform(plan, prepared)

        self.assertIn("repos/o/r/pulls/4/comments/10/replies", commands[0])
        self.assertNotIn("repos/o/r/pulls/4/comments/11/replies", commands[0])
        self.assertEqual(result[0]["url"], "https://example/reply")

    def test_gitlab_reply_uses_existing_discussion(self):
        data = {"head_sha": "def", "records": [
            {"source": "discussion", "id": "7", "discussion_id": "abc/xyz", "author": "reviewer", "created_at": "1"}
        ]}
        plan = {"provider": "gitlab", "repo": "group/project", "number": 8, "head_sha": "def", "actions": [
            {"thread_id": "abc/xyz", "last_comment_id": "7", "action": "reply", "body": "Addressed."}
        ]}
        prepared = process_threads.validate_plan(plan, data, "me")
        commands = []

        def fake_run(command, **_):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, json.dumps({"id": 8}), "")

        with patch.object(process_threads.subprocess, "run", side_effect=fake_run):
            process_threads.perform(plan, prepared)

        self.assertEqual(commands[0][0], "glab")
        self.assertIn("projects/group%2Fproject/merge_requests/8/discussions/abc%2Fxyz/notes", commands[0])

    def test_changed_head_or_last_comment_aborts_before_writing(self):
        data = {"head_sha": "new", "records": [
            {"source": "inline", "id": "11", "thread_id": "T", "author": "reviewer", "created_at": "1"}
        ]}
        plan = {"provider": "github", "head_sha": "old", "actions": [
            {"thread_id": "T", "last_comment_id": "11", "action": "resolve"}
        ]}

        with self.assertRaisesRegex(ValueError, "head changed"):
            process_threads.validate_plan(plan, data, "me")

        plan["head_sha"] = "new"
        plan["actions"][0]["last_comment_id"] = "10"

        with self.assertRaisesRegex(ValueError, "new comment"):
            process_threads.validate_plan(plan, data, "me")

    def test_own_last_comment_rejects_duplicate_reply(self):
        data = {"head_sha": "abc", "records": [
            {"source": "inline", "id": "11", "thread_id": "T", "author": "me", "created_at": "1"}
        ]}
        plan = {"provider": "github", "head_sha": "abc", "actions": [
            {"thread_id": "T", "last_comment_id": "11", "action": "reply", "body": "Again"}
        ]}

        with self.assertRaisesRegex(ValueError, "already yours"):
            process_threads.validate_plan(plan, data, "me")

    def test_gitlab_resolution_requires_resolvable_discussion(self):
        data = {"head_sha": "abc", "records": [
            {"source": "discussion", "id": "11", "discussion_id": "D", "author": "reviewer", "created_at": "1", "resolvable": False}
        ]}
        plan = {"provider": "gitlab", "head_sha": "abc", "actions": [
            {"thread_id": "D", "last_comment_id": "11", "action": "resolve"}
        ]}

        with self.assertRaisesRegex(ValueError, "not marked resolvable"):
            process_threads.validate_plan(plan, data, "me")

    def test_gitlab_resolution_is_checked_after_write(self):
        data = {"head_sha": "abc", "records": [
            {"source": "discussion", "id": "11", "discussion_id": "D", "author": "reviewer", "created_at": "1", "resolvable": True}
        ]}
        plan = {"provider": "gitlab", "repo": "group/project", "number": 8, "head_sha": "abc", "actions": [
            {"thread_id": "D", "last_comment_id": "11", "action": "resolve"}
        ]}
        prepared = process_threads.validate_plan(plan, data, "me")

        with patch.object(process_threads, "cli", return_value={"id": "D"}), patch.object(process_threads, "run", return_value={"notes": [{"resolved": False}]}):
            with self.assertRaisesRegex(RuntimeError, "uncertain"):
                process_threads.perform(plan, prepared)


if __name__ == "__main__":
    unittest.main()
