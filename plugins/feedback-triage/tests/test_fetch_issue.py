import contextlib
import importlib.util
import io
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_issue.py"
spec = importlib.util.spec_from_file_location("fetch_issue", MODULE_PATH)
fetch_issue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_issue)


class FetchIssueTests(unittest.TestCase):
    def test_timeout_aborts_issue_collection(self):
        command = ["gh", "api", "repos/o/r/issues/4"]

        with patch.object(fetch_issue.subprocess, "run", side_effect=subprocess.TimeoutExpired(command, 300)) as cli:
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                fetch_issue.run_json(command)

        self.assertEqual(cli.call_args.kwargs["timeout"], 300)

    def test_comment_body_is_required_but_explicit_empty_string_is_valid(self):
        cases = (
            ("github", {"id": 40, "number": 4, "html_url": "https://github.com/o/r/issues/4", "title": "Fix", "body": None, "updated_at": "2026-09-24T10:00:00Z"},
             {"id": 1, "created_at": "2026-09-24T10:00:00Z", "user": {"login": "a"}, "html_url": "https://github.com/o/r/issues/4#issuecomment-1"}),
            ("gitlab", {"id": 70, "iid": 7, "web_url": "https://gitlab.example/g/p/-/issues/7", "title": "Fix", "description": None, "updated_at": "2026-09-24T10:00:00Z"},
             {"id": 1, "created_at": "2026-09-24T10:00:00Z", "author": {"username": "a"}}),
        )

        for provider, issue, comment in cases:
            for body in (None, 123, ["unexpected"]):
                with self.subTest(provider=provider, body=body):
                    malformed = {**comment, "body": body}

                    with self.assertRaisesRegex(RuntimeError, "Issue comment has an unexpected shape"):
                        fetch_issue.normalize_issue(provider, issue, [malformed])

            with self.subTest(provider=provider, body="missing"):
                with self.assertRaisesRegex(RuntimeError, "Issue comment has an unexpected shape"):
                    fetch_issue.normalize_issue(provider, issue, [comment])

            result = fetch_issue.normalize_issue(provider, issue, [{**comment, "body": ""}])
            self.assertEqual(result["body"], "")
            self.assertEqual(result["comments"][0]["body"], "")

    def test_equal_timestamp_comment_ids_sort_numerically(self):
        issue = {"id": 40, "number": 4, "html_url": "https://github.com/o/r/issues/4", "title": "Fix", "updated_at": "2026-09-24T10:00:00Z"}
        comments = [
            {"id": number, "body": "", "created_at": "2026-09-24T10:00:00Z", "user": {"login": "a"},
             "html_url": f"https://github.com/o/r/issues/4#issuecomment-{number}"}
            for number in (10, 2, 1)
        ]

        result = fetch_issue.normalize_issue("github", issue, comments)

        self.assertEqual([comment["id"] for comment in result["comments"]], ["1", "2", "10"])

    def test_github_collects_all_comment_pages_and_sorts_them(self):
        responses = [
            {"id": 40, "number": 4, "html_url": "https://github.com/o/r/issues/4", "title": "Fix flow", "body": "Acceptance", "updated_at": "2026-09-24T10:00:00Z"},
            [[{"id": 2, "body": "last", "created_at": "2026-09-24T10:02:00Z", "user": {"login": "b"}, "html_url": "https://github.com/o/r/issues/4#issuecomment-2"}],
             [{"id": 1, "body": "first", "created_at": "2026-09-24T10:01:00Z", "user": {"login": "a"}, "html_url": "https://github.com/o/r/issues/4#issuecomment-1"}]],
        ]

        def fake_run(command, **_):
            return subprocess.CompletedProcess(command, 0, json.dumps(responses.pop(0)), "")

        with patch.object(fetch_issue.subprocess, "run", side_effect=fake_run) as run:
            result = fetch_issue.github_issue("o/r", 4, None)

        self.assertEqual(result["provider"], "github")
        self.assertEqual(result["target"], "https://github.com/o/r/issues/4")
        self.assertEqual(result["title"], "Fix flow")
        self.assertEqual(result["body"], "Acceptance")
        self.assertEqual(result["updated_at"], "2026-09-24T10:00:00Z")
        self.assertEqual([item["id"] for item in result["comments"]], ["1", "2"])
        self.assertEqual(result["comments"][0]["author"], "a")
        self.assertEqual(result["comments"][0]["url"], "https://github.com/o/r/issues/4#issuecomment-1")
        self.assertEqual(result["comments"][0]["created_at"], "2026-09-24T10:01:00Z")
        self.assertEqual(result["counts"], {"comments": 2})
        self.assertIn("--paginate", run.call_args_list[1].args[0])
        self.assertIn("--slurp", run.call_args_list[1].args[0])
        self.assertFalse(responses)

    def test_gitlab_collects_notes_and_encodes_namespaced_project(self):
        responses = [
            {"id": 70, "iid": 7, "web_url": "https://gitlab.example/g/sub/p/-/issues/7", "title": "Fix flow", "description": "", "updated_at": "2026-09-24T10:00:00Z"},
            [{"id": 8, "body": "second", "created_at": "2026-09-24T10:02:00Z", "author": {"username": "b"}, "web_url": "https://gitlab.example/g/sub/p/-/issues/7#note_8"},
             {"id": 7, "body": "first", "created_at": "2026-09-24T10:01:00Z", "author": {"username": "a"}}],
        ]

        def fake_run(command, **_):
            return subprocess.CompletedProcess(command, 0, json.dumps(responses.pop(0)), "")

        with patch.object(fetch_issue.subprocess, "run", side_effect=fake_run) as run:
            result = fetch_issue.gitlab_issue("g/sub/p", 7, "gitlab.example")

        self.assertEqual(result["provider"], "gitlab")
        self.assertEqual(result["body"], "")
        self.assertEqual([item["id"] for item in result["comments"]], ["7", "8"])
        self.assertEqual(result["comments"][0]["url"], "https://gitlab.example/g/sub/p/-/issues/7#note_7")
        self.assertEqual(result["counts"], {"comments": 2})
        self.assertIn("projects/g%2Fsub%2Fp/issues/7", run.call_args_list[0].args[0])
        self.assertIn("--paginate", run.call_args_list[1].args[0])
        self.assertNotIn("--slurp", run.call_args_list[1].args[0])
        self.assertTrue(all("--hostname" in call.args[0] for call in run.call_args_list))
        self.assertFalse(responses)

    def test_empty_github_comment_pages_preserve_empty_body(self):
        responses = [
            {"id": 40, "number": 4, "html_url": "https://github.com/o/r/issues/4", "title": "Fix flow", "body": "", "updated_at": "2026-09-24T10:00:00Z"},
            [[]],
        ]

        with patch.object(fetch_issue.subprocess, "run", side_effect=[
            subprocess.CompletedProcess(["gh"], 0, json.dumps(item), "") for item in responses
        ]):
            result = fetch_issue.github_issue("o/r", 4, None)

        self.assertEqual(result["body"], "")
        self.assertEqual(result["comments"], [])
        self.assertEqual(result["counts"], {"comments": 0})

    def test_provider_response_for_different_issue_aborts(self):
        cases = (
            ("github", {"id": 40, "number": 5, "html_url": "https://github.com/o/r/issues/5", "title": "Other", "updated_at": "2026-09-24T10:00:00Z"}, [[]], fetch_issue.github_issue, ("o/r", 4, None)),
            ("gitlab", {"id": 70, "iid": 8, "web_url": "https://gitlab.example/g/p/-/issues/8", "title": "Other", "updated_at": "2026-09-24T10:00:00Z"}, [], fetch_issue.gitlab_issue, ("g/p", 7, None)),
        )

        for provider, issue, comments, fetch, args in cases:
            with self.subTest(provider=provider):
                with patch.object(fetch_issue, "run_json", side_effect=[issue, comments]):
                    with self.assertRaisesRegex(RuntimeError, "unexpected number|unexpected IID"):
                        fetch(*args)

    def test_failed_page_aborts_without_stdout_snapshot(self):
        responses = [
            subprocess.CompletedProcess(["gh"], 0, json.dumps({"id": 40, "number": 4, "html_url": "https://github.com/o/r/issues/4", "title": "Fix", "body": "", "updated_at": "2026-09-24T10:00:00Z"}), ""),
            subprocess.CompletedProcess(["gh"], 1, "", "page failed"),
        ]
        stdout = io.StringIO()

        with patch.object(fetch_issue.subprocess, "run", side_effect=responses):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                status = fetch_issue.main(["github", "--repo", "o/r", "--number", "4"])

        self.assertEqual(status, 1)
        self.assertEqual(stdout.getvalue(), "")

    def test_malformed_github_page_or_comment_raises(self):
        issue = {"id": 40, "number": 4, "html_url": "https://github.com/o/r/issues/4", "title": "Fix", "updated_at": "2026-09-24T10:00:00Z"}

        for pages in ([{"id": 1}], [[{"body": "missing ID"}]], [[{"id": 1, "body": "valid", "created_at": {}}]], {"items": []}):
            with self.subTest(pages=pages):
                responses = [issue, pages]

                with patch.object(fetch_issue.subprocess, "run", side_effect=[
                    subprocess.CompletedProcess(["gh"], 0, json.dumps(item), "") for item in responses
                ]):
                    with self.assertRaises(RuntimeError):
                        fetch_issue.github_issue("o/r", 4, None)

    def test_malformed_gitlab_response_and_invalid_json_raise(self):
        issue = {"id": 70, "iid": 7, "web_url": "https://gitlab.example/g/p/-/issues/7", "title": "Fix", "updated_at": "2026-09-24T10:00:00Z"}

        with patch.object(fetch_issue.subprocess, "run", side_effect=[
            subprocess.CompletedProcess(["glab"], 0, json.dumps(issue), ""),
            subprocess.CompletedProcess(["glab"], 0, json.dumps({"notes": []}), ""),
        ]):
            with self.assertRaises(RuntimeError):
                fetch_issue.gitlab_issue("g/p", 7, None)

        with patch.object(fetch_issue.subprocess, "run", return_value=subprocess.CompletedProcess(["gh"], 0, "broken", "")):
            with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
                fetch_issue.github_issue("o/r", 4, None)

    def test_github_rejects_comments_without_url_or_timestamp_or_string_author(self):
        issue = {"id": 40, "number": 4, "html_url": "https://github.com/o/r/issues/4", "title": "Fix", "updated_at": "2026-09-24T10:00:00Z"}
        complete = {"id": 1, "body": "note", "html_url": "https://github.com/o/r/issues/4#issuecomment-1", "created_at": "2026-09-24T10:00:00Z", "user": {"login": "a"}}

        for missing in ("html_url", "created_at", "user"):
            with self.subTest(missing=missing):
                comment = {key: value for key, value in complete.items() if key != missing}

                with patch.object(fetch_issue.subprocess, "run", side_effect=[
                    subprocess.CompletedProcess(["gh"], 0, json.dumps(issue), ""),
                    subprocess.CompletedProcess(["gh"], 0, json.dumps([[comment]]), ""),
                ]):
                    with self.assertRaises(RuntimeError):
                        fetch_issue.github_issue("o/r", 4, None)

        comment = {**complete, "user": {"login": 123}}

        with patch.object(fetch_issue.subprocess, "run", side_effect=[
            subprocess.CompletedProcess(["gh"], 0, json.dumps(issue), ""),
            subprocess.CompletedProcess(["gh"], 0, json.dumps([[comment]]), ""),
        ]):
            with self.assertRaises(RuntimeError):
                fetch_issue.github_issue("o/r", 4, None)

    def test_gitlab_rejects_non_string_note_author(self):
        issue = {"id": 70, "iid": 7, "web_url": "https://gitlab.example/g/p/-/issues/7", "title": "Fix", "updated_at": "2026-09-24T10:00:00Z"}
        note = {"id": 1, "body": "note", "created_at": "2026-09-24T10:00:00Z", "author": {"username": 123}}

        with patch.object(fetch_issue.subprocess, "run", side_effect=[
            subprocess.CompletedProcess(["glab"], 0, json.dumps(issue), ""),
            subprocess.CompletedProcess(["glab"], 0, json.dumps([note]), ""),
        ]):
            with self.assertRaises(RuntimeError):
                fetch_issue.gitlab_issue("g/p", 7, None)

    def test_main_rejects_invalid_repo_or_number_before_cli(self):
        for repo, number in (("o/r", "0"), ("o/r", "-1"), ("one", "4"), ("/r", "4"), ("o/", "4"), ("o//r", "4")):
            with self.subTest(repo=repo, number=number):
                with patch.object(fetch_issue.subprocess, "run") as run:
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit):
                            fetch_issue.main(["github", "--repo", repo, "--number", number])

                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
