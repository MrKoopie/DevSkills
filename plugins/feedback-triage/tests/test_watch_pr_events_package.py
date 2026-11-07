"""Exercise the packaged monitor from a standalone plugin installation."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILL = PLUGIN / "skills" / "watch-pr-events"


class WatchPackageTests(unittest.TestCase):
    def test_skill_and_plugin_versions_are_discoverable(self):
        text = (SKILL / "SKILL.md").read_text()
        self.assertIn("name: watch-pr-events", text)
        self.assertIn("Codex-specific", text)
        self.assertTrue((SKILL / "agents/openai.yaml").is_file())
        manifests = [
            json.loads(path.read_text())
            for path in PLUGIN.rglob("*.json")
            if path.name in ("plugin.json", "gemini-extension.json", "kimi.plugin.json")
        ]
        self.assertEqual({manifest["version"] for manifest in manifests}, {"0.2.0"})

    @unittest.skipUnless(
        os.name == "posix", "The watcher uses Unix file locks and daemon sockets"
    )
    def test_standalone_install_runs_both_behavioral_suites_without_live_services(self):
        with tempfile.TemporaryDirectory() as temporary:
            installed = Path(temporary) / "feedback-triage"
            shutil.copytree(
                PLUGIN, installed, ignore=shutil.ignore_patterns("__pycache__")
            )
            scripts = installed / "skills/watch-pr-events/scripts"
            for name in ("test_watch.py", "test_daemon_delivery.py"):
                result = subprocess.run(
                    [sys.executable, "-B", str(scripts / name)],
                    cwd=temporary,
                    capture_output=True,
                    text=True,
                    timeout=45,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(
        os.name == "posix", "The watcher uses Unix file locks and daemon sockets"
    )
    def test_help_is_available_outside_the_repository_without_github_or_codex(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, "-B", str(SKILL / "scripts/watch.py"), "--help"],
                cwd=temporary,
                env=dict(os.environ, PATH=""),
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("--until-merged", result.stdout)
            self.assertIn("--one-shot", result.stdout)


if __name__ == "__main__":
    unittest.main()
