"""Negative checks for source metadata required by the validation audit."""

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch_issue.py"
SPEC = importlib.util.spec_from_file_location("audit_source_fetch_issue", SCRIPT)
fetch_issue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch_issue)


class AuditSourceFreshnessTests(unittest.TestCase):
    def test_missing_issue_modification_time_aborts_snapshot(self):
        issue = {
            "id": 10,
            "number": 1,
            "html_url": "https://example.invalid/o/r/issues/1",
            "title": "Acceptance criteria",
            "body": "Required behavior",
        }

        with self.assertRaisesRegex(RuntimeError, "updated|modification|timestamp"):
            fetch_issue.normalize_issue("github", issue, [])

    def test_malformed_issue_modification_time_aborts_snapshot(self):
        issue = {
            "id": 10,
            "iid": 1,
            "web_url": "https://example.invalid/g/p/-/issues/1",
            "title": "Acceptance criteria",
            "description": "Required behavior",
            "updated_at": {"unexpected": "shape"},
        }

        with self.assertRaisesRegex(RuntimeError, "updated|modification|timestamp"):
            fetch_issue.normalize_issue("gitlab", issue, [])

    def test_issue_modification_time_must_be_parseable_and_timezone_aware(self):
        for provider, url_key in (("github", "html_url"), ("gitlab", "web_url")):
            issue = {
                "id": 10,
                "number" if provider == "github" else "iid": 1,
                url_key: "https://example.invalid/o/r/issues/1",
                "title": "Acceptance criteria",
                "updated_at": "2026-09-24T10:00:00Z",
            }

            for updated_at in ("", "not-a-date", "2026-09-24T10:00:00", "2026-13-24T10:00:00Z", 123):
                with self.subTest(provider=provider, updated_at=updated_at):
                    with self.assertRaisesRegex(RuntimeError, "updated_at.*timestamp|updated_at.*timezone"):
                        fetch_issue.normalize_issue(provider, {**issue, "updated_at": updated_at}, [])

    def test_comment_creation_time_must_be_parseable_and_timezone_aware(self):
        for provider, url_key, author_key in (
            ("github", "html_url", "user"),
            ("gitlab", "web_url", "author"),
        ):
            issue = {
                "id": 10,
                "number" if provider == "github" else "iid": 1,
                url_key: "https://example.invalid/o/r/issues/1",
                "title": "Acceptance criteria",
                "updated_at": "2026-09-24T10:00:00Z",
            }
            comment = {
                "id": 1,
                "body": "",
                "created_at": "2026-09-24T10:00:00Z",
                author_key: {"login" if provider == "github" else "username": "reviewer"},
            }

            if provider == "github":
                comment["html_url"] = "https://example.invalid/o/r/issues/1#issuecomment-1"

            for created_at in ("not-a-date", "2026-09-24T10:00:00", "2026-13-24T10:00:00Z"):
                with self.subTest(provider=provider, created_at=created_at):
                    with self.assertRaisesRegex(RuntimeError, "created_at.*timestamp|created_at.*timezone"):
                        fetch_issue.normalize_issue(provider, issue, [{**comment, "created_at": created_at}])

            result = fetch_issue.normalize_issue(provider, issue, [comment])
            self.assertEqual(result["comments"][0]["body"], "")

    def test_mixed_offsets_sort_comments_by_instant(self):
        for provider, url_key, author_key in (
            ("github", "html_url", "user"),
            ("gitlab", "web_url", "author"),
        ):
            issue = {
                "id": 10,
                "number" if provider == "github" else "iid": 1,
                url_key: "https://example.invalid/o/r/issues/1",
                "title": "Acceptance criteria",
                "updated_at": "2026-09-24T10:00:00Z",
            }
            comments = []

            for comment_id, created_at in (
                (10, "2026-09-24T10:00:00Z"),
                (1, "2026-09-24T10:30:00+01:00"),
            ):
                comment = {
                    "id": comment_id,
                    "body": "",
                    "created_at": created_at,
                    author_key: {"login" if provider == "github" else "username": "reviewer"},
                }

                if provider == "github":
                    comment["html_url"] = f"https://example.invalid/o/r/issues/1#issuecomment-{comment_id}"

                comments.append(comment)

            with self.subTest(provider=provider):
                result = fetch_issue.normalize_issue(provider, issue, comments)
                self.assertEqual([comment["id"] for comment in result["comments"]], ["1", "10"])

    def test_equivalent_utc_formats_use_numeric_id_tie_break(self):
        for provider, url_key, author_key in (
            ("github", "html_url", "user"),
            ("gitlab", "web_url", "author"),
        ):
            issue = {
                "id": 10,
                "number" if provider == "github" else "iid": 1,
                url_key: "https://example.invalid/o/r/issues/1",
                "title": "Acceptance criteria",
                "updated_at": "2026-09-24T10:00:00Z",
            }
            comments = []

            for comment_id, created_at in (
                (10, "2026-09-24T10:00:00+00:00"),
                (2, "2026-09-24T10:00:00Z"),
            ):
                comment = {
                    "id": comment_id,
                    "body": "",
                    "created_at": created_at,
                    author_key: {"login" if provider == "github" else "username": "reviewer"},
                }

                if provider == "github":
                    comment["html_url"] = f"https://example.invalid/o/r/issues/1#issuecomment-{comment_id}"

                comments.append(comment)

            with self.subTest(provider=provider):
                result = fetch_issue.normalize_issue(provider, issue, comments)
                self.assertEqual([comment["id"] for comment in result["comments"]], ["2", "10"])


if __name__ == "__main__":
    unittest.main()
