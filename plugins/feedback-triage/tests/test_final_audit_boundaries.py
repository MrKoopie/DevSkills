"""Additional independent validation of collection and resolution boundaries."""

import contextlib
import importlib.util
import io
import subprocess
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


class FinalAuditBoundaryTests(unittest.TestCase):
    def test_feedback_bad_page_and_graphql_error_abort(self):
        metadata = {"html_url": "https://example/pull/1", "head": {"sha": "abc"}}
        cases = (
            [metadata, {"message": "bad page"}],
            [metadata, [[]], [[]], [[]], [{"errors": [{"message": "denied"}]}]],
        )

        for responses in cases:
            with self.subTest(responses=responses):
                with patch.object(feedback, "run", side_effect=responses):
                    with self.assertRaises(RuntimeError):
                        feedback.github(SimpleNamespace(repo="o/r", number=1, host=None))

    def test_feedback_missing_cli_and_invalid_json_abort(self):
        with patch.object(feedback.subprocess, "run", side_effect=FileNotFoundError("missing")):
            with self.assertRaises(RuntimeError):
                feedback.run(["gh", "api", "user"])

        response = subprocess.CompletedProcess(["glab"], 0, "not json", "")

        with patch.object(feedback.subprocess, "run", return_value=response):
            with self.assertRaises(RuntimeError):
                feedback.run(["glab", "api", "user"])

    def test_resolution_success_for_both_providers(self):
        for provider in ("github", "gitlab"):
            with self.subTest(provider=provider):
                thread_id = "T/1" if provider == "gitlab" else "T"
                plan = {"provider": provider, "repo": "o/r", "number": 1, "head_sha": "abc"}
                action = {"thread_id": thread_id, "action": "resolve", "last_comment_id": "1"}
                plan["actions"] = [action]
                record = {"source": "inline" if provider == "github" else "discussion",
                          "id": "1", "thread_id": thread_id, "discussion_id": thread_id, "resolvable": True}
                prepared = threads.validate_plan(plan, {"head_sha": "abc", "records": [record]}, "me")
                response = ({"data": {"resolveReviewThread": {"thread": {"isResolved": True}}}}
                            if provider == "github" else {"id": thread_id})

                with patch.object(threads, "cli", return_value=response) as cli:
                    with patch.object(threads, "run", return_value={"notes": [{"resolved": True}]}) as read:
                        with contextlib.redirect_stderr(io.StringIO()):
                            result = threads.perform(plan, prepared)

                self.assertEqual(result[0]["action"], "resolve")
                self.assertEqual(cli.call_count, 1)
                self.assertEqual(cli.call_args.args[0][0], "gh" if provider == "github" else "glab")
                self.assertEqual(read.call_count, 0 if provider == "github" else 1)

                if provider == "gitlab":
                    self.assertEqual(cli.call_args.args[0], [
                        "glab", "api", "-X", "PUT", "-F", "resolved=true",
                        "projects/o%2Fr/merge_requests/1/discussions/T%2F1",
                    ])
                    self.assertEqual(read.call_args.args[0], [
                        "glab", "api", "projects/o%2Fr/merge_requests/1/discussions/T%2F1",
                    ])

    def test_uncertain_first_resolution_stops_remaining_writes(self):
        plan = {"provider": "github", "repo": "o/r", "number": 1}
        prepared = [({"thread_id": thread, "action": "resolve"}, {}) for thread in ("T1", "T2")]

        with patch.object(threads, "cli", return_value={"data": {}}) as cli:
            with self.assertRaisesRegex(RuntimeError, "uncertain"):
                threads.perform(plan, prepared)

        self.assertEqual(cli.call_count, 1)


if __name__ == "__main__":
    unittest.main()
