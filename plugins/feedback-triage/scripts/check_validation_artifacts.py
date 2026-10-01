#!/usr/bin/env python3
"""Reject generated validation reports still present in Git's index."""

import argparse
import subprocess
import sys
from pathlib import Path


def check(repo: Path) -> list[str]:
    command = ["git", "-C", str(repo), "ls-files", "-z", "--", ".ai/triage"]
    output = subprocess.run(command, check=True, capture_output=True).stdout
    paths = (raw_path.decode("utf-8", errors="surrogateescape") for raw_path in output.split(b"\0") if raw_path)

    return sorted({path for path in paths if path.startswith(".ai/triage/")})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="repository root (defaults to current directory)")
    args = parser.parse_args(argv)

    try:
        offending = check(args.repo)
    except subprocess.CalledProcessError as error:
        print(f"git check failed with exit status {error.returncode}", file=sys.stderr)
        return 1

    if offending:
        print("Generated validation artifacts must not be committed:", file=sys.stderr)

        for path in offending:
            print(path, file=sys.stderr)

        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
