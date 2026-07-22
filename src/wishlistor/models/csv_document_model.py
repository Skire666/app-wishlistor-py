"""In-memory CSV document: header, rows in file order, and derived caches.

Rows are stored as plain ``list[str]`` for performance (100k rows). The model
maintains two parallel caches used by filtering and searching:
- one parsed tag set per row (from `__custom_tags__`);
- one lowercase concatenation of the indexed columns per row.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Iterator
from typing import Self

from wishlistor.shared.constants_util import C_COL_CUSTOM_TAGS
from wishlistor.shared.enums.copy_mode_enum import CopyModeEnum
from wishlistor.shared.enums.severity_enum import SeverityEnum
from wishlistor.shared.enums.tag_enum import TagEnum
from wishlistor.shared.errors.csv_error import ErrorCodeCsv
from wishlistor.shared.tag_util import clean_tags
from wishlistor.shared.typing.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from wishlistor.shared.typing.json_util import as_object_list, as_str_list
from wishlistor.shared.validation_result import ValidationResult

_INDEX_JOIN: str = ""  # unlikely separator for the per-row search string


class CsvDocumentModel:
    """One loaded CSV file, its rows and the caches derived from them."""

    def __init__(self) -> None:
        """Initialize an empty document."""
        self._id_document: str = ""
        self._csv_path: str = ""
        self._header: list[str] = []
        self._rows: list[list[str]] = []
        self._tag_sets: list[frozenset[TagEnum]] = []
        self._index_strings: list[str] = []
        self._search_column_names: list[str] = []
        self._mtime: float = 0.0
        self._size_bytes: int = 0
        self._is_dirty: bool = False
        self._created_at: str = ""
        self._modified_at: str = ""

    # -- container protocol --------------------------------------------------------

    def __iter__(self) -> Iterator[list[str]]:
        """Iterate over the rows in file order."""
        return iter(self._rows)

    def __len__(self) -> int:
        """Return the number of data rows."""
        return len(self._rows)

    def __getitem__(self, row_index: int) -> list[str]:
        """Return the row at *row_index* (file order).

        Args:
            row_index: Zero-based row index.

        Returns:
            The row values.
        """
        return self._rows[row_index]

    # -- properties -------------------------------------------------------------------

    @property
    def id_document(self) -> str:
        """Unique identifier (the CSV path)."""
        return self._id_document

    @property
    def csv_path(self) -> str:
        """Path of the loaded CSV file."""
        return self._csv_path

    @csv_path.setter
    def csv_path(self, value: str) -> None:
        """Set the CSV path (also refreshes the identity)."""
        self._csv_path = value
        self._id_document = value

    @property
    def header(self) -> list[str]:
        """Column names, in file order."""
        return self._header

    @header.setter
    def header(self, value: list[str]) -> None:
        """Set the column names."""
        self._header = list(value)

    @property
    def rows(self) -> list[list[str]]:
        """Data rows, in file order."""
        return self._rows

    @property
    def tag_sets(self) -> list[frozenset[TagEnum]]:
        """Parsed tag set cache, parallel to rows."""
        return self._tag_sets

    @property
    def index_strings(self) -> list[str]:
        """Lowercase search-index cache, parallel to rows."""
        return self._index_strings

    @property
    def mtime(self) -> float:
        """File modification time captured at load or last save."""
        return self._mtime

    @property
    def size_bytes(self) -> int:
        """File size captured at load or last save."""
        return self._size_bytes

    @property
    def is_dirty(self) -> bool:
        """True when in-memory data differs from the file."""
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, value: bool) -> None:
        """Set the dirty flag."""
        self._is_dirty = value

    def set_file_stats(self, mtime: float, size_bytes: int) -> None:
        """Record the on-disk stats used to detect external modifications.

        Args:
            mtime: File modification timestamp.
            size_bytes: File size in bytes.
        """
        self._mtime = mtime
        self._size_bytes = size_bytes

    # -- cell and row access -------------------------------------------------------------

    def column_index(self, name: str) -> int:
        """Return the index of a column, or -1 when absent.

        Args:
            name: Column name.

        Returns:
            Zero-based column index, or -1.
        """
        try:
            return self._header.index(name)
        except ValueError:
            return -1

    def cell(self, row_index: int, column_index: int) -> str:
        """Return one cell value.

        Args:
            row_index: Zero-based row index.
            column_index: Zero-based column index.

        Returns:
            The cell content.
        """
        return self._rows[row_index][column_index]

    def set_cell(self, row_index: int, column_index: int, value: str) -> None:
        """Write one cell value and refresh the row caches.

        Args:
            row_index: Zero-based row index.
            column_index: Zero-based column index.
            value: New cell content.
        """
        self._rows[row_index][column_index] = value
        self.refresh_row_caches(row_index)
        self._is_dirty = True

    def insert_row(self, row_index: int, values: list[str]) -> None:
        """Insert a row at *row_index* and refresh the caches.

        Args:
            row_index: Insertion position in file order.
            values: Row values (must match the header length).
        """
        self._rows.insert(row_index, values)
        self._tag_sets.insert(row_index, frozenset())
        self._index_strings.insert(row_index, "")
        self.refresh_row_caches(row_index)
        self._is_dirty = True

    def remove_row(self, row_index: int) -> list[str]:
        """Remove and return the row at *row_index*.

        Args:
            row_index: Zero-based row index.

        Returns:
            The removed row values.
        """
        self._tag_sets.pop(row_index)
        self._index_strings.pop(row_index)
        self._is_dirty = True
        return self._rows.pop(row_index)

    # -- caches ------------------------------------------------------------------------

    def set_search_columns(self, names: list[str]) -> None:
        """Define the indexed columns and rebuild the search cache.

        Args:
            names: Column names to concatenate into the search index.
        """
        self._search_column_names = list(names)
        self.rebuild_caches()

    def refresh_row_caches(self, row_index: int) -> None:
        """Recompute the tag set and index string of a single row.

        Args:
            row_index: Zero-based row index.
        """
        tags_col = self.column_index(C_COL_CUSTOM_TAGS)
        row = self._rows[row_index]
        if 0 <= tags_col < len(row):
            self._tag_sets[row_index] = clean_tags(row[tags_col])[0]
        columns = [self.column_index(name) for name in self._search_column_names]
        parts = [row[col] for col in columns if 0 <= col < len(row)]
        self._index_strings[row_index] = _INDEX_JOIN.join(parts).lower()

    def rebuild_caches(self) -> None:
        """Recompute the tag and search caches for every row."""
        count = len(self._rows)
        self._tag_sets = [frozenset()] * count
        self._index_strings = [""] * count
        for row_index in range(count):
            self.refresh_row_caches(row_index)

    def find_in_column(self, column_index: int, value: str) -> int:
        """Return the first row whose cell equals *value* (strict comparison).

        Args:
            column_index: Zero-based column index.
            value: Exact value to look for (case sensitive).

        Returns:
            The row index, or -1 when not found.
        """
        for row_index, row in enumerate(self._rows):
            if row[column_index] == value:
                return row_index
        return -1

    def search(self, text: str) -> list[int]:
        """Return the rows whose search index contains *text* (case-insensitive).

        Args:
            text: Substring to look for.

        Returns:
            Matching row indexes, in file order.
        """
        needle = text.lower()
        return [i for i, value in enumerate(self._index_strings) if needle in value]

    # -- contract methods ------------------------------------------------------------------

    @property
    def fieldnames(self) -> list[str]:
        """All column names (the CSV header)."""
        return list(self._header)

    def validate(self, context: object | None = None) -> ValidationResult:
        """Check that every row matches the header length.

        Args:
            context: Unused; kept for the shared model contract.

        Returns:
            The accumulated validation issues.
        """
        _ = context
        result = ValidationResult()
        expected = len(self._header)
        for line, row in enumerate(self._rows, start=2):
            if len(row) != expected:
                context_data = {"line": line, "found": len(row), "expected": expected}
                result.append(ErrorCodeCsv.CSV_1008, SeverityEnum.E_ERROR, context_data)
        return result

    def to_dict(self) -> dict[str, object]:
        """Serialize header and rows (used by tests and technical copies)."""
        return {"csv_path": self._csv_path, "header": list(self._header), "rows": [list(r) for r in self._rows]}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Rebuild a document from ``to_dict`` output.

        Args:
            data: Raw dictionary produced by :meth:`to_dict`.

        Returns:
            The rebuilt document (caches rebuilt, clean state).
        """
        instance = cls()
        path = data.get("csv_path")
        instance.csv_path = path if isinstance(path, str) else ""
        instance.header = as_str_list(data.get("header"))
        rows = as_object_list(data.get("rows"))
        if rows is not None:
            for row in rows:
                items = as_object_list(row)
                if items is not None:
                    instance.rows.append([str(value) for value in items])
        instance.rebuild_caches()
        return instance

    def serialize(self) -> dict[str, object]:
        """Serialize the whole collection (alias of :meth:`to_dict`)."""
        return self.to_dict()

    @classmethod
    def deserialize(cls, data: dict[str, object]) -> Self:
        """Rebuild a document (alias of :meth:`from_dict`).

        Args:
            data: Raw dictionary produced by :meth:`serialize`.

        Returns:
            The rebuilt document.
        """
        return cls.from_dict(data)

    @classmethod
    def get_default(cls) -> Self:
        """Return a fully initialized empty document."""
        instance = cls()
        instance.mark_as_created()
        return instance

    def mark_as_created(self) -> None:
        """Stamp the creation and modification timestamps."""
        self._created_at = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        self._modified_at = self._created_at

    def mark_as_modified(self) -> None:
        """Stamp the modification timestamp."""
        self._modified_at = get_datetime_now_yyyy_mm_dd_hh_mm_ss()

    def copy(self, mode: CopyModeEnum) -> Self:
        """Duplicate the document.

        Args:
            mode: E_BUSINESS drops the path identity; E_TECHNICAL keeps it.

        Returns:
            The duplicated document.
        """
        clone = type(self).from_dict(self.to_dict())
        clone.set_search_columns(self._search_column_names)
        if mode is CopyModeEnum.E_BUSINESS:
            clone.csv_path = ""
        else:
            clone.set_file_stats(self._mtime, self._size_bytes)
            clone.is_dirty = self._is_dirty
        return clone

    def clear(self) -> None:
        """Reset the document to its empty default state."""
        self._csv_path = ""
        self._id_document = ""
        self._header = []
        self._rows = []
        self._tag_sets = []
        self._index_strings = []
        self._search_column_names = []
        self._mtime = 0.0
        self._size_bytes = 0
        self._is_dirty = False


# EOF
