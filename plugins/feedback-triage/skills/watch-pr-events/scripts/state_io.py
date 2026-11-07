"""Private atomic JSON writes with a unique temporary file for each writer."""

import json
import os
import tempfile
from pathlib import Path


def atomic_json(path, value):
    """Replace complete state without sharing temporary paths with concurrent writers."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as file:
            temporary = Path(file.name)
            os.chmod(temporary, 0o600)
            json.dump(value, file, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
