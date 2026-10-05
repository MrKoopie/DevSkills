"""Check Git Workflow distribution; these do not prove agent or browser behavior."""

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


PLUGIN = Path(__file__).resolve().parents[1]
REPOSITORY = PLUGIN.parents[1]


class PackageTests(unittest.TestCase):
    def test_both_skills_are_discoverable_with_ui_metadata(self):
        skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual(
            {"pre-push-sync", "merge-origin-main"},
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

        for catalog in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
            entries = json.loads((REPOSITORY / catalog).read_text())["plugins"]
            matches = [entry for entry in entries if entry["name"] == PLUGIN.name]
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
                {"pre-push-sync", "merge-origin-main"},
                {skill.parent.name for skill in (installed / "skills").glob("*/SKILL.md")},
            )


if __name__ == "__main__":
    unittest.main()
