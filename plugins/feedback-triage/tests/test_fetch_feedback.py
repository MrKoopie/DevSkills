import importlib.util
import json
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_feedback.py"
spec = importlib.util.spec_from_file_location("fetch_feedback", MODULE_PATH)
fetch_feedback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_feedback)


class FetchFeedbackTests(unittest.TestCase):
    def test_pending_github_review_is_not_published_feedback(self):
        responses = [
            {"html_url": "https://github.com/o/r/pull/4", "head": {"sha": "abc"}},
            [[
                {"id": 1, "state": "PENDING", "body": None, "user": {"login": "drafter"}},
                {"id": 2, "state": "COMMENTED", "body": "published", "submitted_at": "2026-09-24T10:00:00Z", "user": {"login": "reviewer"}},
            ]],
            [[]],
            [[]],
            [{"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}}}],
        ]

        with patch.object(fetch_feedback.subprocess, "run", side_effect=[
            subprocess.CompletedProcess(["gh"], 0, json.dumps(item), "") for item in responses
        ]):
            result = fetch_feedback.github(SimpleNamespace(repo="o/r", number=4, host=None))

        self.assertEqual([record["id"] for record in result["records"]], ["2"])
        self.assertEqual(result["counts"]["review"], 1)

    def test_timeout_aborts_feedback_collection(self):
        command = ["gh", "api", "repos/o/r/pulls/4"]

        with patch.object(fetch_feedback.subprocess, "run", side_effect=subprocess.TimeoutExpired(command, 300)) as cli:
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                fetch_feedback.run(command)

        self.assertEqual(cli.call_args.kwargs["timeout"], 300)

    def test_github_keeps_bodyless_review_state_and_submission_commit(self):
        responses = [
            {"html_url": "https://github.com/o/r/pull/4", "head": {"sha": "current"}},
            [[
                {"id": 1, "body": "", "state": "APPROVED", "commit_id": "older", "submitted_at": "2026-09-24T10:00:00Z", "user": {"login": "reviewer"}},
                {"id": 2, "body": None, "state": "CHANGES_REQUESTED", "commit_id": "current", "submitted_at": "2026-09-24T11:00:00Z", "user": {"login": "reviewer"}},
            ]],
            [[]],
            [[]],
            [{"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}}}],
        ]

        with patch.object(fetch_feedback.subprocess, "run", side_effect=[
            subprocess.CompletedProcess(["gh"], 0, json.dumps(item), "") for item in responses
        ]):
            result = fetch_feedback.github(SimpleNamespace(repo="o/r", number=4, host=None))

        reviews = result["records"]
        self.assertEqual([record["state"] for record in reviews], ["APPROVED", "CHANGES_REQUESTED"])
        self.assertEqual([record["commit_id"] for record in reviews], ["older", "current"])
        self.assertEqual([record["submitted_at"] for record in reviews], ["2026-09-24T10:00:00Z", "2026-09-24T11:00:00Z"])
        self.assertEqual([record["body"] for record in reviews], ["", ""])
        self.assertEqual(result["counts"]["review"], 2)

    def test_github_keeps_feedback_from_every_paginated_source(self):
        responses = [
            {"html_url": "https://github.com/o/r/pull/4", "head": {"sha": "abc"}},
            [[{"id": 1, "body": "review", "user": {"login": "a"}, "submitted_at": "2026-09-24T10:00:00Z"}], [{"id": 2, "body": "later review", "submitted_at": "2026-09-24T10:01:00Z"}]],
            [[{"id": 3, "body": "inline", "pull_request_review_id": 1, "created_at": "2026-09-24T10:02:00Z"}, {"id": 5, "body": "reply", "in_reply_to_id": 3, "created_at": "2026-09-24T10:03:00Z"}]],
            [[{"id": 4, "body": "conversation", "created_at": "2026-09-24T10:04:00Z"}]],
            [{"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
                {"id": "T1", "isResolved": True, "isOutdated": False,
                 "comments": {"nodes": [{"databaseId": 3}]}}
            ]}}}}}],
        ]
        commands = []

        def fake_run(command, **_):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, json.dumps(responses.pop(0)), "")

        with patch.object(fetch_feedback.subprocess, "run", side_effect=fake_run):
            result = fetch_feedback.github(SimpleNamespace(repo="o/r", number=4, host=None))

        self.assertEqual([item["id"] for item in result["records"]], ["1", "2", "3", "5", "4"])
        self.assertEqual(result["head_sha"], "abc")
        self.assertTrue(all("--paginate" in command and "--slurp" in command for command in commands[1:]))
        self.assertEqual([item.get("resolved") for item in result["records"] if item["source"] == "inline"], [True, True])
        self.assertFalse(responses)

    def test_gitlab_deduplicates_notes_across_discussions_and_notes(self):
        responses = [
            {"web_url": "https://gitlab.example/g/p/-/merge_requests/7", "diff_refs": {"head_sha": "def"}},
            [{"id": "thread", "notes": [{"id": 10, "body": "first", "resolved": False, "created_at": "2026-09-24T10:00:00Z"}, {"id": 11, "body": "reply", "created_at": "2026-09-24T10:01:00Z"}]}],
            [{"id": 10, "body": "first", "created_at": "2026-09-24T10:00:00Z"}, {"id": 12, "body": "standalone", "system": True, "created_at": "2026-09-24T10:02:00Z"}],
        ]
        commands = []

        def fake_run(command, **_):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, json.dumps(responses.pop(0)), "")

        with patch.object(fetch_feedback.subprocess, "run", side_effect=fake_run):
            result = fetch_feedback.gitlab(SimpleNamespace(repo="g/p", number=7, host="gitlab.example"))

        self.assertEqual([item["id"] for item in result["records"]], ["10", "11", "12"])
        self.assertEqual(result["counts"], {"discussion": 2, "note": 1})
        self.assertTrue(all("--paginate" in command for command in commands[1:]))
        self.assertTrue(all("--hostname" in command for command in commands))
        self.assertIn("projects/g%2Fp/merge_requests/7", commands[0])

    def test_cli_failure_aborts_collection(self):
        failed = subprocess.CompletedProcess(["gh"], 1, "", "authentication failed")

        with patch.object(fetch_feedback.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, "authentication failed"):
                fetch_feedback.github(SimpleNamespace(repo="o/r", number=4, host=None))

    def test_missing_head_sha_aborts_feedback_snapshot(self):
        cases = (
            (
                fetch_feedback.github,
                SimpleNamespace(repo="o/r", number=4, host=None),
                [
                    {"html_url": "https://github.com/o/r/pull/4", "head": {}},
                    [[]],
                    [[]],
                    [[]],
                    [{"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}}}],
                ],
            ),
            (
                fetch_feedback.gitlab,
                SimpleNamespace(repo="g/p", number=7, host=None),
                [
                    {"web_url": "https://gitlab.example/g/p/-/merge_requests/7", "diff_refs": {}},
                    [],
                    [],
                ],
            ),
        )

        for collector, args, responses in cases:
            with self.subTest(provider=collector.__name__):
                with patch.object(fetch_feedback.subprocess, "run", side_effect=[
                    subprocess.CompletedProcess(["api"], 0, json.dumps(item), "") for item in responses
                ]):
                    with self.assertRaisesRegex(RuntimeError, "head SHA"):
                        collector(args)

    def test_invalid_head_sha_aborts_before_paginating(self):
        cases = (
            (fetch_feedback.github, SimpleNamespace(repo="o/r", number=4, host=None), {"head": {"sha": "   "}}),
            (fetch_feedback.github, SimpleNamespace(repo="o/r", number=4, host=None), {"head": {"sha": 123}}),
            (fetch_feedback.gitlab, SimpleNamespace(repo="g/p", number=7, host=None), {"diff_refs": {"head_sha": "   "}}),
            (fetch_feedback.gitlab, SimpleNamespace(repo="g/p", number=7, host=None), {"diff_refs": {"head_sha": 123}}),
        )

        for collector, args, metadata in cases:
            with self.subTest(provider=collector.__name__, metadata=metadata):
                with patch.object(fetch_feedback.subprocess, "run", return_value=subprocess.CompletedProcess(
                    ["api"], 0, json.dumps(metadata), ""
                )) as cli:
                    with self.assertRaisesRegex(RuntimeError, "head SHA"):
                        collector(args)

                self.assertEqual(cli.call_count, 1)

    def test_gitlab_falls_back_to_top_level_sha(self):
        responses = [
            {"web_url": "https://gitlab.example/g/p/-/merge_requests/7", "diff_refs": {}, "sha": "fallback"},
            [],
            [],
        ]

        with patch.object(fetch_feedback.subprocess, "run", side_effect=[
            subprocess.CompletedProcess(["glab"], 0, json.dumps(item), "") for item in responses
        ]):
            result = fetch_feedback.gitlab(SimpleNamespace(repo="g/p", number=7, host=None))

        self.assertEqual(result["head_sha"], "fallback")

    def test_gitlab_prefers_current_sha_when_diff_refs_lag(self):
        responses = [
            {"web_url": "https://gitlab.example/g/p/-/merge_requests/7", "sha": "current", "diff_refs": {"head_sha": "older"}},
            [],
            [],
        ]

        with patch.object(fetch_feedback.subprocess, "run", side_effect=[
            subprocess.CompletedProcess(["glab"], 0, json.dumps(item), "") for item in responses
        ]):
            result = fetch_feedback.gitlab(SimpleNamespace(repo="g/p", number=7, host=None))

        self.assertEqual(result["head_sha"], "current")


if __name__ == "__main__":
    unittest.main()
