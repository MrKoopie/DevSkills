"""Check installable resource integrity, not agent or application behavior."""

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


PLUGIN = Path(__file__).resolve().parents[1]
REPOSITORY = PLUGIN.parents[1]


def broken_references(root):
    errors = []

    for document in root.rglob("*.md"):
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", document.read_text()):
            parsed = urlsplit(target)

            if parsed.scheme or not parsed.path:
                continue

            resolved = (document.parent / unquote(parsed.path)).resolve()

            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                errors.append(f"{document.relative_to(root)}: {target}")

    return errors


class PackageTests(unittest.TestCase):
    def test_resources_survive_standalone_installation(self):
        with tempfile.TemporaryDirectory() as temporary:
            installed = Path(temporary) / "installed-plugin"
            shutil.copytree(PLUGIN, installed, ignore=shutil.ignore_patterns("__pycache__"))
            self.assertEqual([], broken_references(installed))

    def test_reference_check_rejects_missing_and_escaping_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "plugin"
            root.mkdir()
            (Path(temporary) / "outside.md").write_text("outside")
            (root / "SKILL.md").write_text("[missing](missing.md)\n[outside](../outside.md)\n")
            self.assertEqual(2, len(broken_references(root)))

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

    def test_skills_and_agent_are_discoverable(self):
        skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual(
            {"modernize-app", "app-behavior-baseline"},
            {skill.parent.name for skill in skills},
        )

        for document in [*skills, PLUGIN / "agents/baseline-discovery.md"]:
            match = re.match(r"\A---\n(.*?)\n---\n", document.read_text(), re.DOTALL)
            self.assertIsNotNone(match, str(document))
            fields = dict(line.split(": ", 1) for line in match[1].splitlines())
            expected = document.parent.name if document.name == "SKILL.md" else document.stem
            self.assertEqual(expected, fields["name"])
            self.assertTrue(fields["description"].strip())

        for skill in skills:
            self.assertTrue((skill.parent / "agents/openai.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
