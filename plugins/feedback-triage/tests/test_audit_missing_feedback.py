"""Negative coverage for feedback pages that omit required thread data."""

import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch_feedback.py"
spec = importlib.util.spec_from_file_location("fetch_feedback_audit", SCRIPT)
feedback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feedback)


class MissingFeedbackTests(unittest.TestCase):
    def test_github_inline_comment_without_thread_metadata_aborts_collection(self):
        responses = [
            {"html_url": "https://github.com/o/r/pull/4", "head": {"sha": "abc"}},
            [[]],
            [[{"id": 10, "body": "Fix this", "created_at": "2026-09-24T10:00:00Z"}]],
            [[]],
            [{"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}}}],
        ]

        with patch.object(feedback, "run", side_effect=responses):
            with self.assertRaises(RuntimeError):
                feedback.github(SimpleNamespace(repo="o/r", number=4, host=None))

    def test_gitlab_discussion_without_notes_aborts_collection(self):
        for notes in (None, [], "invalid"):
            with self.subTest(notes=notes):
                discussion = {"id": "D"}

                if notes is not None:
                    discussion["notes"] = notes

                responses = [
                    {"web_url": "https://gitlab.example/g/p/-/merge_requests/7", "diff_refs": {"head_sha": "abc"}},
                    [discussion],
                    [],
                ]

                with patch.object(feedback, "run", side_effect=responses):
                    with self.assertRaisesRegex(RuntimeError, "missing notes"):
                        feedback.gitlab(SimpleNamespace(repo="g/p", number=7, host=None))

    def test_empty_feedback_collections_are_valid(self):
        github_responses = [
            {"html_url": "https://github.com/o/r/pull/4", "head": {"sha": "abc"}},
            [[]],
            [[]],
            [[]],
            [{"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": []}}}}}],
        ]

        with patch.object(feedback, "run", side_effect=github_responses):
            self.assertEqual(feedback.github(SimpleNamespace(repo="o/r", number=4, host=None))["records"], [])

        gitlab_responses = [
            {"web_url": "https://gitlab.example/g/p/-/merge_requests/7", "diff_refs": {"head_sha": "abc"}},
            [],
            [],
        ]

        with patch.object(feedback, "run", side_effect=gitlab_responses):
            self.assertEqual(feedback.gitlab(SimpleNamespace(repo="g/p", number=7, host=None))["records"], [])
