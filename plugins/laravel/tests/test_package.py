"""Distribution checks; these do not evaluate model or Laravel runtime behavior."""

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


PLUGIN = Path(__file__).resolve().parents[1]
REPOSITORY = PLUGIN.parents[1]


def local_reference_errors(root):
    errors = []

    for document in root.rglob("*.md"):
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", document.read_text()):
            parsed = urlsplit(target)

            if parsed.scheme or not parsed.path:
                continue

            resolved = (document.parent / unquote(parsed.path)).resolve()

            if not resolved.is_relative_to(root.resolve()):
                errors.append(f"{document.relative_to(root)}: outside package: {target}")
            elif not resolved.exists():
                errors.append(f"{document.relative_to(root)}: missing: {target}")

    return errors


class PackageTests(unittest.TestCase):
    def test_references_survive_standalone_installation(self):
        with tempfile.TemporaryDirectory() as temporary:
            installed = Path(temporary) / "installed-laravel"
            shutil.copytree(PLUGIN, installed, ignore=shutil.ignore_patterns("__pycache__"))
            self.assertEqual([], local_reference_errors(installed))

    def test_reference_check_detects_missing_and_external_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "plugin"
            root.mkdir()
            (Path(temporary) / "outside.md").write_text("outside")
            (root / "SKILL.md").write_text(
                "[missing](missing.md)\n[outside](../outside.md)\n"
            )
            errors = local_reference_errors(root)
            self.assertEqual(2, len(errors))
            self.assertTrue(any("missing:" in error for error in errors))
            self.assertTrue(any("outside package:" in error for error in errors))

    def test_client_manifests_describe_the_same_plugin(self):
        codex = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())

        for field in ("name", "version", "description", "author"):
            self.assertEqual(codex[field], claude[field])

        self.assertEqual(PLUGIN.name, codex["name"])
        self.assertTrue((PLUGIN / codex["skills"]).is_dir())

    def test_catalogs_resolve_to_this_plugin_once(self):
        for catalog in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
            data = json.loads((REPOSITORY / catalog).read_text())
            entries = [entry for entry in data["plugins"] if entry["name"] == PLUGIN.name]
            self.assertEqual(1, len(entries), catalog)
            source = entries[0]["source"]
            relative = source["path"] if isinstance(source, dict) else source
            self.assertEqual(PLUGIN, (REPOSITORY / relative).resolve())

    def test_six_distinct_discoverable_skills(self):
        skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual(6, len(skills))
        names = []

        for skill in skills:
            text = skill.read_text()
            frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
            self.assertIsNotNone(frontmatter, str(skill))
            fields = dict(line.split(": ", 1) for line in frontmatter[1].splitlines())
            self.assertEqual(skill.parent.name, fields["name"])
            self.assertTrue(fields["description"].strip())
            names.append(fields["name"])

        self.assertEqual(len(names), len(set(names)))

    def test_skills_only_distribution(self):
        forbidden_directories = {"agents", "droids", "hooks"}

        for item in PLUGIN.rglob("*"):
            if item.is_dir():
                self.assertNotIn(item.name, forbidden_directories)

        for descriptor in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
            manifest = json.loads((PLUGIN / descriptor).read_text())
            self.assertFalse({"agents", "hooks", "mcpServers", "apps"} & manifest.keys())


if __name__ == "__main__":
    unittest.main()
