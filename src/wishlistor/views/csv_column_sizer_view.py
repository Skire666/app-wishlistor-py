"""Column sizing helpers of the CSV table (persisted widths, first-open fit)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableView

from wishlistor.views.csv_table_model_view import CsvTableModelView

C_COLUMN_WIDTH_MAX_PX: int = 200
C_COLUMN_WIDTH_MIN_PX: int = 40
_CHECK_COLUMN_WIDTH_PX: int = 32
_DELETE_COLUMN_WIDTH_PX: int = 36
_AUTO_SIZE_SAMPLE_ROWS: int = 50
_MEASURED_TEXT_MAX_CHARS: int = 64


def apply_column_widths(table: QTableView, model: CsvTableModelView, widths: dict[str, int]) -> None:
    """Restore the persisted user column widths.

    Args:
        table: The CSV table view.
        model: Its adapter model.
        widths: Column name to width (pixels) mapping.
    """
    for column in range(1, model.columnCount()):
        name = model.column_name_at(column)
        if name and name in widths:
            table.setColumnWidth(column, max(C_COLUMN_WIDTH_MIN_PX, widths[name]))
    fit_check_column(table, model)
    fit_delete_column(table, model)


def auto_size_columns(table: QTableView, model: CsvTableModelView) -> None:
    """First-open sizing: fit each column to its content, capped at 200 px.

    Columns are processed from the rightmost one, sampling the first rows only
    so a 100k-row document stays instantaneous.

    Args:
        table: The CSV table view.
        model: Its adapter model.
    """
    metrics = table.fontMetrics()
    sample = min(_AUTO_SIZE_SAMPLE_ROWS, model.rowCount())
    for column in reversed(range(1, model.columnCount())):
        name = model.column_name_at(column)
        if not name:
            continue  # trailing delete column
        width = metrics.horizontalAdvance(name) + 24
        for view_row in range(sample):
            text = str(model.index(view_row, column).data(Qt.ItemDataRole.DisplayRole) or "")
            width = max(width, metrics.horizontalAdvance(text[:_MEASURED_TEXT_MAX_CHARS]) + 16)
        table.setColumnWidth(column, max(C_COLUMN_WIDTH_MIN_PX, min(C_COLUMN_WIDTH_MAX_PX, width)))
    fit_check_column(table, model)
    fit_delete_column(table, model)


def fit_check_column(table: QTableView, model: CsvTableModelView) -> None:
    """Give the leading selection (checkbox) column its fixed small width.

    Args:
        table: The CSV table view.
        model: Its adapter model.
    """
    if model.columnCount() > 0:
        table.setColumnWidth(0, _CHECK_COLUMN_WIDTH_PX)


def fit_delete_column(table: QTableView, model: CsvTableModelView) -> None:
    """Give the trailing per-row delete column its fixed small width.

    Args:
        table: The CSV table view.
        model: Its adapter model.
    """
    last = model.columnCount() - 1
    if model.is_delete_column(last):
        table.setColumnWidth(last, _DELETE_COLUMN_WIDTH_PX)


def collect_column_widths(table: QTableView, model: CsvTableModelView) -> dict[str, int]:
    """Return the current data-column widths, keyed by column name.

    Args:
        table: The CSV table view.
        model: Its adapter model.

    Returns:
        Column name to width (pixels) mapping.
    """
    widths: dict[str, int] = {}
    for column in range(1, model.columnCount()):
        name = model.column_name_at(column)
        if name:
            widths[name] = table.columnWidth(column)
    return widths


# EOF
