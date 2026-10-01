"""Regression checks for empty reviewer comments that still change thread state."""

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


feedback = load("fetch_feedback")
threads = load("process_threads")


class EmptyFeedbackBoundaryTests(unittest.TestCase):
    def test_github_empty_latest_comment_blocks_stale_action(self):
        responses = [
            {"html_url": "https://github.com/o/r/pull/4", "head": {"sha": "abc"}},
            [[]],
            [[
                {"id": 10, "body": "Original request", "user": {"login": "reviewer"}, "created_at": "2026-09-24T10:00:00Z"},
                {"id": 11, "body": "", "in_reply_to_id": 10, "user": {"login": "reviewer"}, "created_at": "2026-09-24T10:01:00Z"},
            ]],
            [[]],
            [{"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
                {"id": "T", "isResolved": False, "isOutdated": False, "comments": {"nodes": [{"databaseId": 10}]}}
            ]}}}}}],
        ]

        with patch.object(feedback, "run", side_effect=responses):
            data = feedback.github(SimpleNamespace(repo="o/r", number=4, host=None))

        plan = {"provider": "github", "head_sha": "abc", "actions": [
            {"thread_id": "T", "last_comment_id": "10", "action": "resolve"}
        ]}

        with self.assertRaisesRegex(ValueError, "new comment"):
            threads.validate_plan(plan, data, "me")

        self.assertEqual([record["id"] for record in data["records"] if record["source"] == "inline"], ["10", "11"])
        self.assertEqual(data["records"][1]["body"], "")

    def test_github_bodyless_conversation_event_is_retained(self):
        responses = [
            {"html_url": "https://github.com/o/r/pull/4", "head": {"sha": "abc"}},
            [[]],
            [[]],
            [[{"id": 12, "body": None, "created_at": "2026-09-24T10:02:00Z"}]],
            [{"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}}}],
        ]

        with patch.object(feedback, "run", side_effect=responses):
            data = feedback.github(SimpleNamespace(repo="o/r", number=4, host=None))

        self.assertEqual([(record["id"], record["body"]) for record in data["records"]], [("12", "")])
        self.assertEqual(data["counts"]["conversation"], 1)

    def test_github_incomplete_new_event_aborts_collection(self):
        for bad_event in (
            {"id": 11, "body": "", "in_reply_to_id": 10},
            {"id": 11, "body": False, "in_reply_to_id": 10, "created_at": "2026-09-24T10:01:00Z"},
        ):
            with self.subTest(bad_event=bad_event):
                responses = [
                    {"html_url": "https://github.com/o/r/pull/4", "head": {"sha": "abc"}},
                    [[]],
                    [[
                        {"id": 10, "body": "Original request", "created_at": "2026-09-24T10:00:00Z"},
                        bad_event,
                    ]],
                    [[]],
                    [{"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}}}],
                ]

                with patch.object(feedback, "run", side_effect=responses):
                    with self.assertRaisesRegex(RuntimeError, "timestamp|body"):
                        feedback.github(SimpleNamespace(repo="o/r", number=4, host=None))

    def test_gitlab_empty_latest_note_blocks_stale_action(self):
        responses = [
            {"web_url": "https://gitlab.example/g/p/-/merge_requests/7", "diff_refs": {"head_sha": "abc"}},
            [{"id": "D", "notes": [
                {"id": 10, "body": "Original request", "author": {"username": "reviewer"}, "created_at": "2026-09-24T10:00:00Z"},
                {"id": 11, "body": "", "author": {"username": "reviewer"}, "created_at": "2026-09-24T10:01:00Z"},
            ]}],
            [],
        ]

        with patch.object(feedback, "run", side_effect=responses):
            data = feedback.gitlab(SimpleNamespace(repo="g/p", number=7, host=None))

        plan = {"provider": "gitlab", "head_sha": "abc", "actions": [
            {"thread_id": "D", "last_comment_id": "10", "action": "reply", "body": "Addressed"}
        ]}

        with self.assertRaisesRegex(ValueError, "new comment"):
            threads.validate_plan(plan, data, "me")

        self.assertEqual([record["id"] for record in data["records"] if record["source"] == "discussion"], ["10", "11"])
        self.assertEqual(data["records"][1]["body"], "")

    def test_gitlab_bodyless_standalone_note_is_retained(self):
        responses = [
            {"web_url": "https://gitlab.example/g/p/-/merge_requests/7", "diff_refs": {"head_sha": "abc"}},
            [],
            [{"id": 12, "body": None, "created_at": "2026-09-24T10:02:00Z"}],
        ]

        with patch.object(feedback, "run", side_effect=responses):
            data = feedback.gitlab(SimpleNamespace(repo="g/p", number=7, host=None))

        self.assertEqual([(record["id"], record["body"]) for record in data["records"]], [("12", "")])
        self.assertEqual(data["counts"]["note"], 1)

    def test_gitlab_incomplete_new_note_aborts_collection(self):
        for bad_note in (
            {"id": 11, "body": ""},
            {"id": 11, "body": 0, "created_at": "2026-09-24T10:01:00Z"},
        ):
            with self.subTest(bad_note=bad_note):
                responses = [
                    {"web_url": "https://gitlab.example/g/p/-/merge_requests/7", "diff_refs": {"head_sha": "abc"}},
                    [{"id": "D", "notes": [
                        {"id": 10, "body": "Original request", "created_at": "2026-09-24T10:00:00Z"},
                        bad_note,
                    ]}],
                    [],
                ]

                with patch.object(feedback, "run", side_effect=responses):
                    with self.assertRaisesRegex(RuntimeError, "timestamp|body"):
                        feedback.gitlab(SimpleNamespace(repo="g/p", number=7, host=None))


if __name__ == "__main__":
    unittest.main()
