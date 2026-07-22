"""QAbstractTableModel adapter over CsvDocumentModel (display only).

Filtering, sorting and searching are done here on `_view_rows` (a list of
document row indexes) — no QSortFilterProxyModel, too slow at 100k rows.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QBrush, QColor

from wishlistor.models.csv_document_model import CsvDocumentModel
from wishlistor.shared.constants_util import (
    C_COL_CUSTOM_TAGS,
    C_COLOR_BACKGROUND_MAIN,
    C_COLOR_SURFACE,
    C_RANK_COLUMNS,
)
from wishlistor.shared.enums.tag_enum import TagEnum
from wishlistor.shared.i18n_fra import CSV_FILTER_EMPTY_TAGS

_CHECK_COLUMN: int = 0
_FIRST_DATA_COLUMN: int = 1

_ModelIndex = QModelIndex | QPersistentModelIndex


class CsvTableModelView(QAbstractTableModel):
    """Read-mostly table adapter with in-adapter filter, sort and selection."""

    _STRIPE_EVEN: ClassVar[QBrush] = QBrush(QColor(C_COLOR_BACKGROUND_MAIN))
    _STRIPE_ODD: ClassVar[QBrush] = QBrush(QColor(C_COLOR_SURFACE))

    def __init__(self) -> None:
        """Initialize an empty adapter."""
        super().__init__()
        self._document: CsvDocumentModel | None = None
        self._columns: list[str] = []  # visible column names, display order
        self._column_indexes: list[int] = []  # matching document column indexes
        self._view_rows: list[int] = []
        self._checked: set[int] = set()
        self._column_nicknames: dict[str, str] = {}
        self._active_tags: frozenset[str] = frozenset()
        self._filter_text: str = ""
        self._sort_column: int = -1
        self._sort_descending: bool = False
        self._on_cell_edited: Callable[[int, str, str], None] | None = None
        self._on_check_changed: Callable[[int], None] | None = None

    # -- configuration -------------------------------------------------------------

    def bind_cell_edited(self, callback: Callable[[int, str, str], None]) -> None:
        """Register the edit callback (doc row, column name, new value)."""
        self._on_cell_edited = callback

    def bind_check_changed(self, callback: Callable[[int], None]) -> None:
        """Register the checked-count callback."""
        self._on_check_changed = callback

    def set_document(self, document: CsvDocumentModel | None, visible_columns: list[str]) -> None:
        """Install a document and its visible columns, resetting every state.

        Args:
            document: The loaded document (None clears the table).
            visible_columns: Column names to show, in display order.
        """
        self.beginResetModel()
        self._document = document
        self._checked = set()
        self._sort_column = -1
        self._column_nicknames = {}
        self._apply_columns(visible_columns)
        self._rebuild_view_rows()
        self.endResetModel()
        self._emit_check_changed()

    def set_visible_columns(self, visible_columns: list[str]) -> None:
        """Change the visible columns, keeping filters and selection.

        Args:
            visible_columns: Column names to show, in display order.
        """
        self.beginResetModel()
        self._apply_columns(visible_columns)
        self.endResetModel()

    def set_column_nicknames(self, nicknames: dict[str, str]) -> None:
        """Update the header nickname mapping and repaint the header.

        Args:
            nicknames: Column name to display nickname mapping.
        """
        self._column_nicknames = dict(nicknames)
        if self.columnCount() > 0:
            self.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, self.columnCount() - 1)

    def _apply_columns(self, visible_columns: list[str]) -> None:
        """Resolve visible column names to document indexes."""
        document = self._document
        self._columns = []
        self._column_indexes = []
        if document is None:
            return
        for name in visible_columns:
            index = document.column_index(name)
            if index >= 0:
                self._columns.append(name)
                self._column_indexes.append(index)

    # -- filters, sort, search -------------------------------------------------------

    def apply_filters(self, active_tags: frozenset[str], filter_text: str) -> None:
        """Filter the rows by tags (OR) combined with the text filter (AND).

        Args:
            active_tags: Active tag labels; may contain the empty-tags filter.
            filter_text: Substring searched in the indexed columns.
        """
        self.beginResetModel()
        self._active_tags = active_tags
        self._filter_text = filter_text
        self._rebuild_view_rows()
        self.endResetModel()

    def _rebuild_view_rows(self) -> None:
        """Recompute `_view_rows` from the document and the current filters."""
        document = self._document
        if document is None:
            self._view_rows = []
            return
        needle = self._filter_text.lower()
        rows: list[int] = []
        for row_index, tags in enumerate(document.tag_sets):
            if needle and needle not in document.index_strings[row_index]:
                continue
            if self._matches_tag_filter(tags):
                rows.append(row_index)
        self._view_rows = rows
        if self._sort_column >= _FIRST_DATA_COLUMN:
            self._sort_view_rows()

    def _matches_tag_filter(self, tags: frozenset[TagEnum]) -> bool:
        """Return True when a row passes the OR-combined tag filters."""
        if not self._active_tags:
            return True
        if tags:
            return any(tag.value in self._active_tags for tag in tags)
        return CSV_FILTER_EMPTY_TAGS in self._active_tags

    def refresh(self) -> None:
        """Re-read the document (after edits), keeping filters and sort."""
        self.beginResetModel()
        self._drop_stale_checks()
        self._rebuild_view_rows()
        self.endResetModel()
        self._emit_check_changed()

    def _drop_stale_checks(self) -> None:
        """Remove checked rows that no longer exist in the document."""
        if self._document is not None:
            count = len(self._document)
            self._checked = {row for row in self._checked if row < count}

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Sort the displayed rows (display state only, spec B.4.1).

        Args:
            column: View column index (0 is the check column, unsortable).
            order: Ascending or descending.
        """
        if column < _FIRST_DATA_COLUMN or self._document is None or self.is_delete_column(column):
            return
        self.beginResetModel()
        self._sort_column = column
        self._sort_descending = order is Qt.SortOrder.DescendingOrder
        self._sort_view_rows()
        self.endResetModel()

    def _sort_view_rows(self) -> None:
        """Sort `_view_rows` intelligently: numeric when possible, empties last."""
        document = self._document
        if document is None:
            return
        column_index = self._column_indexes[self._sort_column - _FIRST_DATA_COLUMN]
        rows = document.rows
        filled = [row for row in self._view_rows if rows[row][column_index].strip()]
        empty = [row for row in self._view_rows if not rows[row][column_index].strip()]
        if _is_numeric_column(rows, filled, column_index):
            filled.sort(key=lambda row: float(rows[row][column_index].replace(",", ".", 1)))
        else:
            filled.sort(key=lambda row: rows[row][column_index].lower())
        if self._sort_descending:
            filled.reverse()
        self._view_rows = filled + empty

    def search_positions(self, text: str) -> list[int]:
        """Return the view positions matching *text* (indexed columns).

        Args:
            text: Case-insensitive substring.

        Returns:
            Matching view row positions, top to bottom.
        """
        document = self._document
        if document is None or not text:
            return []
        needle = text.lower()
        strings = document.index_strings
        return [pos for pos, row in enumerate(self._view_rows) if needle in strings[row]]

    def tag_counts(self) -> dict[str, int]:
        """Count rows per tag label over the whole document (plus empty)."""
        counts: dict[str, int] = {CSV_FILTER_EMPTY_TAGS: 0}
        if self._document is None:
            return counts
        for tags in self._document.tag_sets:
            if not tags:
                counts[CSV_FILTER_EMPTY_TAGS] += 1
            for tag in tags:
                counts[tag.value] = counts.get(tag.value, 0) + 1
        return counts

    # -- selection ----------------------------------------------------------------------

    def checked_rows(self) -> list[int]:
        """Return the checked document rows, ascending."""
        return sorted(self._checked)

    def clear_all_checks(self) -> None:
        """Uncheck every row (button 'Dé-sélectionner')."""
        self._checked.clear()
        self._notify_check_column()

    def check_all_visible(self) -> None:
        """Check every currently displayed row."""
        self._checked.update(self._view_rows)
        self._notify_check_column()

    def invert_visible_checks(self) -> None:
        """Invert the check state of every currently displayed row."""
        for row in self._view_rows:
            if row in self._checked:
                self._checked.discard(row)
            else:
                self._checked.add(row)
        self._notify_check_column()

    def _notify_check_column(self) -> None:
        """Repaint the check column and notify the presenter."""
        if self._view_rows:
            top = self.index(0, _CHECK_COLUMN)
            bottom = self.index(len(self._view_rows) - 1, _CHECK_COLUMN)
            self.dataChanged.emit(top, bottom, [Qt.ItemDataRole.CheckStateRole])
        self._emit_check_changed()

    def _emit_check_changed(self) -> None:
        """Notify the presenter of the checked-row count."""
        if self._on_check_changed is not None:
            self._on_check_changed(len(self._checked))

    # -- row/column resolution -------------------------------------------------------------

    def doc_row_at(self, view_row: int) -> int:
        """Return the document row shown at *view_row* (-1 when out of range)."""
        if 0 <= view_row < len(self._view_rows):
            return self._view_rows[view_row]
        return -1

    def view_row_of(self, doc_row: int) -> int:
        """Return the view position of a document row (-1 when filtered out)."""
        try:
            return self._view_rows.index(doc_row)
        except ValueError:
            return -1

    def column_name_at(self, view_column: int) -> str:
        """Return the document column name at *view_column* ('' for the check column)."""
        offset = view_column - _FIRST_DATA_COLUMN
        if 0 <= offset < len(self._columns):
            return self._columns[offset]
        return ""

    def visible_row_count(self) -> int:
        """Return the number of rows currently displayed."""
        return len(self._view_rows)

    def is_delete_column(self, column: int) -> bool:
        """Return True when *column* is the trailing per-row delete column."""
        return bool(self._columns) and column == _FIRST_DATA_COLUMN + len(self._columns)

    # -- QAbstractTableModel ------------------------------------------------------------------

    def rowCount(self, parent: _ModelIndex | None = None) -> int:  # noqa: N802 - Qt override
        """Return the number of displayed rows."""
        _ = parent
        return len(self._view_rows)

    def columnCount(self, parent: _ModelIndex | None = None) -> int:  # noqa: N802 - Qt override
        """Return the displayed columns (check and per-row delete included)."""
        _ = parent
        if not self._columns:
            return _FIRST_DATA_COLUMN
        return _FIRST_DATA_COLUMN + len(self._columns) + 1  # trailing delete column

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = 0) -> object:  # noqa: N802 - Qt override
        """Return the header labels."""
        if role != Qt.ItemDataRole.DisplayRole or orientation is not Qt.Orientation.Horizontal:
            return None
        if section == _CHECK_COLUMN:
            return ""
        name = self.column_name_at(section)
        if not name:
            return ""
        return self._column_nicknames.get(name) or name

    def data(self, index: _ModelIndex, role: int = 0) -> object:
        """Return cell payloads: text, check state and stripe background."""
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == _CHECK_COLUMN:
            doc_row = self._view_rows[index.row()]
            return Qt.CheckState.Checked if doc_row in self._checked else Qt.CheckState.Unchecked
        if role == Qt.ItemDataRole.BackgroundRole:
            return self._STRIPE_ODD if index.row() % 2 else self._STRIPE_EVEN
        if role in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole}:
            return self._cell_text(index)
        return None

    def _cell_text(self, index: _ModelIndex) -> str:
        """Return the raw cell text of a data column."""
        if index.column() == _CHECK_COLUMN or self._document is None:
            return ""
        offset = index.column() - _FIRST_DATA_COLUMN
        if offset >= len(self._column_indexes):
            return ""  # trailing delete column
        doc_row = self._view_rows[index.row()]
        return self._document.rows[doc_row][self._column_indexes[offset]]

    def setData(self, index: _ModelIndex, value: object, role: int = 0) -> bool:  # noqa: N802 - Qt override
        """Handle check toggles and forward cell edits to the presenter."""
        if not index.isValid():
            return False
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == _CHECK_COLUMN:
            doc_row = self._view_rows[index.row()]
            self._checked.symmetric_difference_update({doc_row})
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
            self._emit_check_changed()
            return True
        if role == Qt.ItemDataRole.EditRole and self._on_cell_edited is not None:
            doc_row = self._view_rows[index.row()]
            column_name = self.column_name_at(index.column())
            if column_name:
                self._on_cell_edited(doc_row, column_name, str(value))
                return True
        return False

    def flags(self, index: _ModelIndex) -> Qt.ItemFlag:
        """Return per-column interaction flags (ranks are never editable)."""
        base = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == _CHECK_COLUMN:
            return base | Qt.ItemFlag.ItemIsUserCheckable
        if self.is_delete_column(index.column()):
            return base
        name = self.column_name_at(index.column())
        if name in C_RANK_COLUMNS or name == C_COL_CUSTOM_TAGS:
            return base
        return base | Qt.ItemFlag.ItemIsEditable


def _is_numeric_column(rows: list[list[str]], filled: list[int], column_index: int) -> bool:
    """Return True when every non-empty value of the column is numeric."""
    for row in filled:
        try:
            float(rows[row][column_index].replace(",", ".", 1))
        except ValueError:
            return False
    return True


# EOF
