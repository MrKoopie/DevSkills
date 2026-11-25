"""Check that a standalone Development installation can find the audit assets."""

import re
import shutil
import tempfile
import unittest
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[1]
CONTRACTS = {
    "validate-original-request": "subagent-contract.md",
    "validate-business-process": "business-process-contract.md",
    "validate-technical-implementation": "technical-contract.md",
}


class ValidationPackageTests(unittest.TestCase):
    def test_audit_skill_and_review_assets_are_packaged_together(self):
        with tempfile.TemporaryDirectory() as temporary:
            installed = Path(temporary) / "development"
            shutil.copytree(PLUGIN, installed, ignore=shutil.ignore_patterns("__pycache__"))
            skill = installed / "skills/validate-original-request"

            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertTrue((skill / "references/report-template.md").is_file())
            for script in ("fetch_issue.py", "check_validation_artifacts.py"):
                self.assertTrue((installed / "scripts" / script).is_file(), script)

            for directory in ("agents", "droids"):
                for role, contract in CONTRACTS.items():
                    with self.subTest(directory=directory, role=role):
                        descriptor = installed / directory / f"{role}.md"
                        contents = descriptor.read_text()
                        self.assertRegex(contents, rf"(?m)^name: {role}$")
                        reference = re.search(r"`(\.\./skills/[^`]+)`", contents)
                        self.assertIsNotNone(reference, str(descriptor))
                        path = (descriptor.parent / reference[1]).resolve()
                        self.assertEqual(skill / "references" / contract, path)
                        self.assertTrue(path.is_file(), str(path))
