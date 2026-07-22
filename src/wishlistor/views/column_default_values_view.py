"""Editable table of column -> default-value assignments (project form)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from PySide6.QtWidgets import QComboBox, QHeaderView, QPushButton, QTableWidget, QVBoxLayout, QWidget

from wishlistor.shared import i18n_fra
from wishlistor.shared.constants_util import C_COLOR_ERROR
from wishlistor.shared.default_value_util import C_ALL_DEFAULT_VALUES
from wishlistor.shared.errors.project_error import ErrorCodeProject
from wishlistor.views.field_marker_view import FieldMarkerView

_COL_COLUMN: int = 0
_COL_VALUE: int = 1
_COL_REMOVE: int = 2
_COLUMN_COUNT: int = 3
_REMOVE_COLUMN_WIDTH_PX: int = 25


class ColumnDefaultValuesView(QWidget):
    """Rows of (column, default value), with add/remove and inline validation (spec §3-4)."""

    def __init__(self, parent: QWidget) -> None:
        """Initialize the empty table.

        Args:
            parent: The owning widget.
        """
        super().__init__(parent)
        self.setObjectName("column_default_values")
        self._on_changed: Callable[[], None] | None = None
        self._available_columns: list[str] = []
        self._row_markers: list[tuple[FieldMarkerView, FieldMarkerView]] = []
        self._has_errors: bool = False
        self._table_var = QTableWidget(0, _COLUMN_COUNT, self)
        self._table_var.setObjectName("column_default_values_table")
        self._table_var.setHorizontalHeaderLabels(
            [i18n_fra.FORM_DEFAULT_VALUES_COL_COLUMN, i18n_fra.FORM_DEFAULT_VALUES_COL_VALUE, ""]
        )
        self._table_var.verticalHeader().hide()
        header = self._table_var.horizontalHeader()
        header.setSectionResizeMode(_COL_COLUMN, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(_COL_VALUE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(_COL_REMOVE, QHeaderView.ResizeMode.Fixed)
        self._table_var.setColumnWidth(_COL_REMOVE, _REMOVE_COLUMN_WIDTH_PX)
        add_button = QPushButton(i18n_fra.FORM_DEFAULT_VALUES_ADD, self)
        add_button.setObjectName("column_default_values_add_button")
        add_button.clicked.connect(lambda: self._add_row("", "", emit=True))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table_var, 1)
        layout.addWidget(add_button, 0)

    # -- data -----------------------------------------------------------------------

    def set_available_columns(self, columns: list[str]) -> None:
        """Refresh the column choices, keeping valid selections (spec §5).

        Args:
            columns: Same source as the 'Affichage' checklist.
        """
        self._available_columns = list(columns)
        for row in range(self._table_var.rowCount()):
            self._refresh_column_combo(row)
        self._revalidate()

    def set_rows(self, rows: list[tuple[str, str]]) -> None:
        """Replace the whole table content.

        Args:
            rows: (column, default_value) pairs, in row order.
        """
        self._table_var.setRowCount(0)
        self._row_markers.clear()
        for column, default_value in rows:
            self._add_row(column, default_value, emit=False)
        self._revalidate()

    def rows(self) -> list[tuple[str, str]]:
        """Return the (column, default_value) pairs, in row order."""
        result: list[tuple[str, str]] = []
        for row in range(self._table_var.rowCount()):
            column = str(self._column_combo(row).currentData() or "")
            value = str(self._value_combo(row).currentData() or "")
            result.append((column, value))
        return result

    def has_errors(self) -> bool:
        """True when a duplicate column or an incomplete row is present."""
        return self._has_errors

    def bind_changed(self, callback: Callable[[], None]) -> None:
        """Register the change callback (add, remove, or edit a row).

        Args:
            callback: Called after any user change.
        """
        self._on_changed = callback

    # -- rows -----------------------------------------------------------------------

    def _add_row(self, column: str, default_value: str, emit: bool) -> None:
        """Insert one row at the bottom of the table."""
        row = self._table_var.rowCount()
        self._table_var.insertRow(row)
        column_combo = QComboBox(self._table_var)
        self._fill_column_combo(column_combo, column)
        value_combo = QComboBox(self._table_var)
        self._fill_value_combo(value_combo, default_value)
        column_marker = FieldMarkerView(column_combo, self._table_var)
        value_marker = FieldMarkerView(value_combo, self._table_var)
        self._table_var.setCellWidget(row, _COL_COLUMN, column_marker)
        self._table_var.setCellWidget(row, _COL_VALUE, value_marker)
        remove_button = QPushButton(i18n_fra.FORM_DEFAULT_VALUES_REMOVE_ICON, self._table_var)
        remove_button.setObjectName(f"column_default_values_remove_button_{row}")
        remove_button.setToolTip(i18n_fra.FORM_DEFAULT_VALUES_REMOVE)
        remove_button.setStyleSheet(f"color: {C_COLOR_ERROR}; font-weight: bold;")
        remove_button.clicked.connect(lambda _checked=False, button=remove_button: self._remove_row(button))
        self._table_var.setCellWidget(row, _COL_REMOVE, remove_button)
        self._row_markers.append((column_marker, value_marker))
        column_combo.currentIndexChanged.connect(lambda _index: self._handle_row_changed())
        value_combo.currentIndexChanged.connect(lambda _index: self._handle_row_changed())
        if emit:
            self._handle_row_changed()

    def _remove_row(self, button: QPushButton) -> None:
        """Remove the row owning *button* (spec §3.2, no confirmation)."""
        for row in range(self._table_var.rowCount()):
            if self._table_var.cellWidget(row, _COL_REMOVE) is button:
                self._table_var.removeRow(row)
                del self._row_markers[row]
                break
        self._handle_row_changed()

    def _handle_row_changed(self) -> None:
        """Recompute validation and forward the change (spec §3.3)."""
        self._revalidate()
        self._emit_changed()

    def _emit_changed(self) -> None:
        """Forward a change to the bound callback."""
        if self._on_changed is not None:
            self._on_changed()

    # -- combos ---------------------------------------------------------------------

    def _column_combo(self, row: int) -> QComboBox:
        """Return the 'Colonne' combo of *row*."""
        return cast("QComboBox", self._row_markers[row][0].inner)

    def _value_combo(self, row: int) -> QComboBox:
        """Return the 'Valeur par défaut' combo of *row*."""
        return cast("QComboBox", self._row_markers[row][1].inner)

    def _refresh_column_combo(self, row: int) -> None:
        """Keep the current selection if still available, else clear it."""
        combo = self._column_combo(row)
        current = str(combo.currentData() or "")
        self._fill_column_combo(combo, current if current in self._available_columns else "")

    def _fill_column_combo(self, combo: QComboBox, current: str) -> None:
        """(Re)fill the 'Colonne' combo, all available columns, every row (spec §1)."""
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(i18n_fra.FORM_NO_SELECTION, "")
        for name in self._available_columns:
            combo.addItem(name, name)
        index = combo.findData(current) if current else 0
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def _fill_value_combo(self, combo: QComboBox, current: str) -> None:
        """(Re)fill the 'Valeur par défaut' combo with the fixed choice list (spec §2)."""
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(i18n_fra.FORM_NO_SELECTION, "")
        for choice in C_ALL_DEFAULT_VALUES:
            combo.addItem(i18n_fra.FORM_DEFAULT_VALUE_LABELS.get(choice, choice.value), choice.value)
        index = combo.findData(current) if current else 0
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    # -- validation -------------------------------------------------------------------

    def _revalidate(self) -> None:
        """Mark duplicate columns and incomplete rows inline (spec §4)."""
        row_values, incomplete_rows, duplicate_rows = self._collect_row_states()
        self._apply_row_markers(row_values, duplicate_rows)
        self._has_errors = bool(incomplete_rows or duplicate_rows)
        # A fixed default row height can clip the marker's warning icon (_ICON_SCALE) once it
        # becomes visible; Qt's layout excludes hidden widgets from sizeHint, so re-fit on every pass.
        self._table_var.resizeRowsToContents()

    def _collect_row_states(self) -> tuple[list[tuple[str, str]], set[int], set[int]]:
        """Read each row's (column, value) pair and compute incomplete/duplicate rows."""
        columns_seen: dict[str, list[int]] = {}
        incomplete_rows: set[int] = set()
        row_values: list[tuple[str, str]] = []
        for row in range(self._table_var.rowCount()):
            column = str(self._column_combo(row).currentData() or "")
            value = str(self._value_combo(row).currentData() or "")
            row_values.append((column, value))
            if not column or not value:
                incomplete_rows.add(row)
            if column:
                columns_seen.setdefault(column, []).append(row)
        duplicate_rows = {row for rows in columns_seen.values() if len(rows) > 1 for row in rows}
        return row_values, incomplete_rows, duplicate_rows

    def _apply_row_markers(self, row_values: list[tuple[str, str]], duplicate_rows: set[int]) -> None:
        """Paint the error markers for each row from its (column, value) pair."""
        for row, (column, value) in enumerate(row_values):
            column_marker, value_marker = self._row_markers[row]
            if row in duplicate_rows:
                column_marker.set_error(ErrorCodeProject.PRJ_1014.value.format(column=column))
            elif not column:
                column_marker.set_error(ErrorCodeProject.PRJ_1015.value)
            else:
                column_marker.set_error("")
            value_marker.set_error(ErrorCodeProject.PRJ_1015.value if not value else "")


# EOF
