# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations


class FileAccessError(Exception):
    """Raised by repositories when a file cannot be read or written."""

    def __init__(self, path: str, detail: str) -> None:
        """Initialize the error with the offending path and a short detail.

        Args:
            path: The file path involved in the failure.
            detail: Short technical detail (French, may reach the logs).
        """
        super().__init__(f"Accès au fichier impossible : {path} ({detail})")
        self.path = path
        self.detail = detail


# EOF
