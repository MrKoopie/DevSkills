"""Negative source-identity checks for original-request validation."""

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch_issue.py"
SPEC = importlib.util.spec_from_file_location("audit_fetch_issue", SCRIPT)
fetch_issue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch_issue)


class AuditIssueIdentityTests(unittest.TestCase):
    def test_missing_issue_id_aborts_snapshot_for_both_providers(self):
        cases = (
            ("github", {"number": 4, "html_url": "https://github.com/o/r/issues/4", "title": "Fix", "body": "Acceptance", "updated_at": "2026-09-24T10:00:00Z"}),
            ("gitlab", {"iid": 4, "web_url": "https://gitlab.example/o/r/-/issues/4", "title": "Fix", "description": "Acceptance", "updated_at": "2026-09-24T10:00:00Z"}),
        )

        for provider, issue in cases:
            with self.subTest(provider=provider):
                with self.assertRaisesRegex(RuntimeError, "valid id"):
                    fetch_issue.normalize_issue(provider, issue, [])

    def test_malformed_issue_identity_aborts_snapshot_for_both_providers(self):
        cases = (
            ("github", "number", {"id": 40, "number": 4, "html_url": "https://github.com/o/r/issues/4", "title": "Fix", "body": None, "updated_at": "2026-09-24T10:00:00Z"}),
            ("gitlab", "iid", {"id": 40, "iid": 4, "web_url": "https://gitlab.example/o/r/-/issues/4", "title": "Fix", "description": None, "updated_at": "2026-09-24T10:00:00Z"}),
        )

        for provider, number_key, issue in cases:
            with self.subTest(provider=provider, identity="valid"):
                result = fetch_issue.normalize_issue(provider, issue, [])
                self.assertEqual(result["body"], "")

            for key in ("id", number_key):
                for value in (None, 0, -1, True, False, "", "4", 4.0, {}, []):
                    with self.subTest(provider=provider, key=key, value=value):
                        with self.assertRaisesRegex(RuntimeError, f"valid {key}"):
                            fetch_issue.normalize_issue(provider, {**issue, key: value}, [])


if __name__ == "__main__":
    unittest.main()
