import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_validation_artifacts.py"
spec = importlib.util.spec_from_file_location("check_validation_artifacts", MODULE_PATH)
check_validation_artifacts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_validation_artifacts)


class ValidationArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.com"], check=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ignored_report_is_not_offending_until_force_added(self):
        report = self.repo / ".ai/triage/2026-09-24/10-00-report.md"
        report.parent.mkdir(parents=True)
        report.write_text("audit", encoding="utf-8")
        (self.repo / ".gitignore").write_text("*.log\n/.ai/triage/\n", encoding="utf-8")

        ignored = subprocess.run(
            ["git", "-C", str(self.repo), "check-ignore", "-q", "--no-index", "--", ".ai/triage/ignore-probe.md"],
            check=False,
        )

        self.assertEqual(ignored.returncode, 0)
        self.assertEqual((self.repo / ".gitignore").read_text(encoding="utf-8"), "*.log\n/.ai/triage/\n")
        self.assertEqual(check_validation_artifacts.check(self.repo), [])

        subprocess.run(["git", "-C", str(self.repo), "add", "-f", str(report)], check=True)

        self.assertEqual(check_validation_artifacts.check(self.repo), [".ai/triage/2026-09-24/10-00-report.md"])

    def test_tracked_report_is_offending_even_when_ignored(self):
        report = self.repo / ".ai/triage/old/report.md"
        report.parent.mkdir(parents=True)
        report.write_text("audit", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "-f", str(report)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-m", "add report"], check=True)
        (self.repo / ".gitignore").write_text("/.ai/triage/\n", encoding="utf-8")

        self.assertEqual(check_validation_artifacts.check(self.repo), [".ai/triage/old/report.md"])

    def test_nested_and_similarly_named_paths_do_not_trigger(self):
        nested = self.repo / "src/.ai/triage/report.md"
        similarly_named = self.repo / ".ai/triage-old/report.md"

        for path in (nested, similarly_named):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("audit", encoding="utf-8")
            subprocess.run(["git", "-C", str(self.repo), "add", str(path)], check=True)

        self.assertEqual(check_validation_artifacts.check(self.repo), [])

    def test_untracking_report_allows_cleanup_commit_and_preserves_local_artifact(self):
        report = self.repo / ".ai/triage/old/report.md"
        report.parent.mkdir(parents=True)
        report.write_text("audit", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "-f", str(report)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-m", "fixture tracked report"], check=True)
        (self.repo / ".gitignore").write_text("/.ai/triage/\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "rm", "--cached", str(report)], check=True)

        self.assertTrue(report.exists())
        self.assertEqual(check_validation_artifacts.check(self.repo), [])


if __name__ == "__main__":
    unittest.main()
