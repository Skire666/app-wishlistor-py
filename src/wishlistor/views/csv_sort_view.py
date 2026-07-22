"""Sort-order persistence helpers of the CSV table (persisted sort, live collection)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableView

from wishlistor.views.csv_table_model_view import CsvTableModelView


def apply_sort_order(table: QTableView, model: CsvTableModelView, column: str, descending: bool) -> None:
    """Restore the persisted sort order.

    Args:
        table: The CSV table view.
        model: Its adapter model.
        column: Sorted column name (empty leaves the natural row order).
        descending: True for a descending sort.
    """
    if not column:
        return
    for view_column in range(1, model.columnCount()):
        if model.column_name_at(view_column) == column:
            order = Qt.SortOrder.DescendingOrder if descending else Qt.SortOrder.AscendingOrder
            table.sortByColumn(view_column, order)
            return


def collect_sort_order(table: QTableView, model: CsvTableModelView) -> tuple[str, bool]:
    """Return the current sort column name and direction.

    Args:
        table: The CSV table view.
        model: Its adapter model.

    Returns:
        Column name (empty when unsorted) and True when the sort is descending.
    """
    header = table.horizontalHeader()
    name = model.column_name_at(header.sortIndicatorSection())
    if not name:
        return "", False
    return name, header.sortIndicatorOrder() is Qt.SortOrder.DescendingOrder


# EOF
