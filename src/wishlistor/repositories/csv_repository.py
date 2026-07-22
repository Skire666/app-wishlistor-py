"""Raw CSV file access: full read, atomic write, file metadata (spec D.1/D.5)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import csv
import logging
from pathlib import Path

from wishlistor.shared.constants_util import C_CSV_DELIMITER, C_CSV_ENCODING_READ, C_CSV_ENCODING_WRITE
from wishlistor.shared.exceptions.csv_structure_error import CsvStructureError
from wishlistor.shared.exceptions.file_access_error import FileAccessError


class CsvRepository:
    """Reads and writes CSV files (`;` delimiter, UTF-8, minimal quoting)."""

    def __init__(self) -> None:
        """Initialize the repository."""
        self._logger = logging.getLogger(self.__class__.__name__)

    def file_exists(self, path: str) -> bool:
        """Return True when *path* points to an existing file.

        Args:
            path: File path to test.
        """
        return Path(path).is_file()

    def file_stats(self, path: str) -> tuple[float, int] | None:
        """Return (mtime, size) of a file, or None when it is missing.

        Args:
            path: File path to inspect.
        """
        try:
            stats = Path(path).stat()
        except OSError:
            return None
        return stats.st_mtime, stats.st_size

    def read_header(self, path: str) -> list[str]:
        """Read only the header line of a CSV file.

        Args:
            path: CSV file path.

        Returns:
            The column names (empty for an empty file).

        Raises:
            FileAccessError: When the file cannot be read.
        """
        self._logger.debug("Lecture de l'en-tête CSV : %s", path)
        try:
            with Path(path).open(encoding=C_CSV_ENCODING_READ, newline="") as handle:
                reader = csv.reader(handle, delimiter=C_CSV_DELIMITER)
                return next(reader, [])
        except (OSError, UnicodeDecodeError, csv.Error) as excp:
            raise FileAccessError(path, str(excp)) from excp

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
        self._logger.debug("Lecture complète du CSV : %s", path)
        try:
            with Path(path).open(encoding=C_CSV_ENCODING_READ, newline="") as handle:
                reader = csv.reader(handle, delimiter=C_CSV_DELIMITER)
                header = next(reader, None)
                if header is None or not any(name.strip() for name in header):
                    raise CsvStructureError(path, "en-tête absent ou vide")
                rows = list(reader)
        except (OSError, UnicodeDecodeError, csv.Error) as excp:
            raise FileAccessError(path, str(excp)) from excp
        self._logger.debug("CSV lu : %s colonnes, %s lignes", len(header), len(rows))
        return header, rows

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
        target = Path(path)
        temp_path = target.with_name(target.name + ".tmp")
        self._logger.debug("Écriture atomique du CSV : %s (%s lignes)", path, len(rows))
        try:
            with temp_path.open("w", encoding=C_CSV_ENCODING_WRITE, newline="") as handle:
                writer = csv.writer(handle, delimiter=C_CSV_DELIMITER, quoting=csv.QUOTE_MINIMAL)
                writer.writerow(header)
                writer.writerows(rows)
            Path(temp_path).replace(target)
        except (OSError, csv.Error) as excp:
            raise FileAccessError(path, str(excp)) from excp
        stats = target.stat()
        return stats.st_mtime, stats.st_size


# EOF
