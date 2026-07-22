"""Filesystem path helpers (validation and metadata, no business logic)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def make_all_folders_if_not_exists(path: Path | str) -> None:
    """Create the directory *path* (and its parents) when missing.

    Args:
        path: Directory path to create.
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def get_mtime_of_file(file_path: Path | str) -> datetime | None:
    """Return the last modified time of a file, or None when it is missing.

    Args:
        file_path: The path to the file.

    Returns:
        The last modified time, or None.
    """
    path = Path(file_path)
    if not path.is_file():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime)


# EOF
