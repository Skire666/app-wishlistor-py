# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations


class CsvStructureError(Exception):
    """Raised by the CSV repository when a file has no exploitable structure."""

    def __init__(self, path: str, detail: str) -> None:
        """Initialize the error with the offending path and a short detail.

        Args:
            path: The CSV file path.
            detail: Short technical detail (French, may reach the logs).
        """
        super().__init__(f"Structure CSV invalide : {path} ({detail})")
        self.path = path
        self.detail = detail


# EOF
