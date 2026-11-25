"""Check Git Workflow distribution; these do not prove agent or browser behavior."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


PLUGIN = Path(__file__).resolve().parents[1]
REPOSITORY = PLUGIN.parents[1]
SKILLS = {"pre-push-sync", "merge-origin-main", "process-pr-feedback", "watch-pr-events"}


class PackageTests(unittest.TestCase):
    def test_skills_are_discoverable_with_ui_metadata(self):
        skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual(
            SKILLS,
            {skill.parent.name for skill in skills},
        )

        for skill in skills:
            match = re.match(r"\A---\n(.*?)\n---\n", skill.read_text(), re.DOTALL)
            self.assertIsNotNone(match, str(skill))
            fields = dict(line.split(": ", 1) for line in match[1].splitlines())
            self.assertEqual(skill.parent.name, fields["name"])
            self.assertTrue(fields["description"].strip())
            self.assertTrue((skill.parent / "agents/openai.yaml").is_file())

    def test_client_manifests_and_catalogs_agree(self):
        codex = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())

        for field in ("name", "version", "description", "author"):
            self.assertEqual(codex[field], claude[field])

        self.assertEqual(PLUGIN.name, codex["name"])
        self.assertTrue((PLUGIN / codex["skills"]).is_dir())

        for manifest in (
            ".cursor-plugin/plugin.json",
            ".factory-plugin/plugin.json",
            "gemini-extension.json",
            "kimi.plugin.json",
        ):
            with self.subTest(manifest=manifest):
                path = PLUGIN / manifest
                self.assertTrue(path.is_file(), manifest)
                fields = json.loads(path.read_text())
                for field in ("name", "version", "description"):
                    self.assertEqual(codex[field], fields[field])
                if "skills" in fields:
                    self.assertTrue((PLUGIN / fields["skills"]).is_dir())

        for catalog in (
            ".agents/plugins/marketplace.json",
            ".claude-plugin/marketplace.json",
            ".cursor-plugin/marketplace.json",
            ".factory-plugin/marketplace.json",
            ".github/plugin/marketplace.json",
            "kimi-marketplace.json",
        ):
            entries = json.loads((REPOSITORY / catalog).read_text())["plugins"]
            names = [entry.get("name", entry.get("id")) for entry in entries]
            self.assertIn("development", names, catalog)
            self.assertNotIn("feedback-triage", names, catalog)
            matches = [entry for entry, name in zip(entries, names) if name == PLUGIN.name]
            self.assertEqual(1, len(matches), catalog)
            source = matches[0]["source"]
            path = source["path"] if isinstance(source, dict) else source
            self.assertEqual(PLUGIN, (REPOSITORY / path).resolve())

            if "description" in matches[0]:
                self.assertEqual(codex["description"], matches[0]["description"])

    def test_resources_survive_standalone_installation(self):
        with tempfile.TemporaryDirectory() as temporary:
            installed = Path(temporary) / "git-workflow"
            shutil.copytree(PLUGIN, installed, ignore=shutil.ignore_patterns("__pycache__"))

            for document in installed.rglob("*.md"):
                for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", document.read_text()):
                    parsed = urlsplit(target)

                    if parsed.scheme or not parsed.path:
                        continue

                    resolved = (document.parent / unquote(parsed.path)).resolve()
                    self.assertTrue(resolved.is_relative_to(installed), str(document))
                    self.assertTrue(resolved.exists(), target)

            self.assertEqual(
                SKILLS,
                {skill.parent.name for skill in (installed / "skills").glob("*/SKILL.md")},
            )
            for script in ("fetch_feedback.py", "process_threads.py"):
                self.assertTrue((installed / "scripts" / script).is_file(), script)

            watcher = installed / "skills/watch-pr-events"
            instructions = (watcher / "SKILL.md").read_text()
            self.assertIn("git-workflow:process-pr-feedback", instructions)
            if os.name != "posix":
                return
            result = subprocess.run(
                [sys.executable, "-B", str(watcher / "scripts/watch.py"), "--help"],
                cwd=temporary,
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            for option in ("{github,gitlab}", "--workflow", "--job", "--one-shot"):
                self.assertIn(option, result.stdout)


if __name__ == "__main__":
    unittest.main()
