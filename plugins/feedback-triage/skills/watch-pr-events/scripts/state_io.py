"""Private atomic JSON writes with a unique temporary file for each writer."""

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
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


@contextmanager
def delivery_guard(path, blocking=True):
    """Serialize migration against the entire transition into and out of delivery."""
    with Path(path).with_suffix(".handoff.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError as error:
            raise RuntimeError(
                "Delivery is in progress; inspect it before migration"
            ) from error
        yield
