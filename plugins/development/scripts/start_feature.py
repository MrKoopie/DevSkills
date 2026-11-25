"""Prepare a local feature workspace inside a Git checkout."""
import argparse
from pathlib import Path
import re
import subprocess


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def prepare(repo, feature):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", feature):
        raise ValueError("Use a lowercase feature name with digits and hyphens.")
    root = Path(git(repo, "rev-parse", "--show-toplevel"))
    home = root / ".ai/work" / feature
    for directory in (".ai/work", ".ai/triage"):
        if git(root, "ls-files", "--", directory):
            raise ValueError(f"Tracked files in {directory}; inspect the index before continuing.")
    exclude = Path(git(root, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude"))
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a+b") as stream:
        stream.seek(0)
        existing = stream.read()
        rules = [rule for rule in (b"/.ai/work/", b"/.ai/triage/") if rule not in existing.splitlines()]
        if rules:
            if existing and not existing.endswith(b"\n"):
                stream.write(b"\n")
            stream.write(b"\n".join(rules) + b"\n")
    for directory in (".ai/work", ".ai/triage"):
        git(root, "check-ignore", "-q", "--no-index", "--", directory + "/probe")
    directories = [home / name for name in ("requirements", "prototype", "plans", "validations")]
    outputs = [home / "README.md", home / "changes.md"]
    paths = {str(path.relative_to(root)) for path in [*outputs, *home.rglob("*")]}
    paths.update(str(path.relative_to(root)) + "/" for path in [home, *directories])
    for path in sorted(paths):
        git(root, "check-ignore", "-q", "--no-index", "--", path)
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    for name, content in {
        "README.md": "# " + feature + "\n\nCurrent combination: pending.\nCandidate: pending.\n",
        "changes.md": "# User changes to the agreed plan\n\n",
    }.items():
        try:
            with (home / name).open("x", encoding="utf-8") as stream:
                stream.write(content)
        except FileExistsError:
            pass
    return home


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feature")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(prepare(args.repo, args.feature))
