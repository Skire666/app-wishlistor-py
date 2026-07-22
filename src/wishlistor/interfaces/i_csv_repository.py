# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol


class ICsvRepository(Protocol):
    """Raw CSV file access: reading, atomic writing, file metadata."""

    def file_exists(self, path: str) -> bool:
        """Return True when *path* points to an existing file.

        Args:
            path: File path to test.
        """
        ...

    def file_stats(self, path: str) -> tuple[float, int] | None:
        """Return (mtime, size) of a file, or None when it is missing.

        Args:
            path: File path to inspect.
        """
        ...

    def read_header(self, path: str) -> list[str]:
        """Read only the header line of a CSV file.

        Args:
            path: CSV file path.

        Returns:
            The column names (may be empty for an empty file).

        Raises:
            FileAccessError: When the file cannot be read.
        """
        ...

    def read_all(self, path: str) -> tuple[list[str], list[list[str]]]:
        """Read the whole CSV file into memory.

        Args:
            path: CSV file path.

        Returns:
            A tuple (header, rows).

        Raises:
            FileAccessError: When the file cannot be read.
            CsvStructureError: When the file has no exploitable header.
        """
        ...

    def write_atomic(self, path: str, header: list[str], rows: list[list[str]]) -> tuple[float, int]:
        """Write a CSV file atomically (temp file in the same folder, then rename).

        Args:
            path: Destination CSV file path.
            header: Column names.
            rows: Data rows, in file order.

        Returns:
            The new (mtime, size) of the written file.

        Raises:
            FileAccessError: When the file cannot be written.
        """
        ...


# EOF
