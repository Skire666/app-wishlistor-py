"""Persistence wiring of the CSV table header: debounced widths, sort order (spec B.4.1)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import QTableView

from wishlistor.views import csv_column_sizer_view, csv_sort_view
from wishlistor.views.csv_table_model_view import CsvTableModelView

_WIDTHS_DEBOUNCE_MS: int = 600


class CsvHeaderStateView:
    """Debounces column-resize events and reports sort-order changes for persistence."""

    def __init__(self, parent: QObject, table: QTableView, model: CsvTableModelView) -> None:
        """Initialize the controller.

        Args:
            parent: Owner of the internal debounce timer (the CSV view).
            table: The CSV table view.
            model: Its adapter model.
        """
        self._table = table
        self._model = model
        self._is_loading: Callable[[], bool] = lambda: False
        self._has_document: Callable[[], bool] = lambda: False
        self._on_widths_changed: Callable[[dict[str, int]], None] | None = None
        self._on_sort_changed: Callable[[str, bool], None] | None = None
        self._widths_timer = QTimer(parent)
        self._widths_timer.setSingleShot(True)
        self._widths_timer.setInterval(_WIDTHS_DEBOUNCE_MS)
        self._widths_timer.timeout.connect(self._emit_widths)
        header = table.horizontalHeader()
        header.sectionResized.connect(self._handle_section_resized)
        header.sortIndicatorChanged.connect(self._handle_sort_indicator_changed)

    def bind_guards(self, is_loading: Callable[[], bool], has_document: Callable[[], bool]) -> None:
        """Register the predicates suppressing persistence during programmatic updates.

        Args:
            is_loading: True while the view rebuilds (restore in progress).
            has_document: True once a document is displayed.
        """
        self._is_loading = is_loading
        self._has_document = has_document

    def bind_column_widths_changed(self, callback: Callable[[dict[str, int]], None]) -> None:
        """Register the user column-resize callback (debounced)."""
        self._on_widths_changed = callback

    def bind_sort_order_changed(self, callback: Callable[[str, bool], None]) -> None:
        """Register the user sort-order callback (column name, descending)."""
        self._on_sort_changed = callback

    def _handle_section_resized(self, _logical: int, _old_size: int, _new_size: int) -> None:
        """Schedule the persistence of a user column resize."""
        if not self._is_loading() and self._has_document():
            self._widths_timer.start()

    def _emit_widths(self) -> None:
        """Collect and forward the current column widths (debounced)."""
        widths = csv_column_sizer_view.collect_column_widths(self._table, self._model)
        if widths and self._on_widths_changed is not None:
            self._on_widths_changed(widths)

    def _handle_sort_indicator_changed(self, _logical: int, _order: Qt.SortOrder) -> None:
        """Collect and forward the new sort order."""
        if self._is_loading() or not self._has_document() or self._on_sort_changed is None:
            return
        column, descending = csv_sort_view.collect_sort_order(self._table, self._model)
        self._on_sort_changed(column, descending)


# EOF
