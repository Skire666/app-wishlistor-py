"""Table of (selected, raw CSV name, nickname) rows, reorderable by drag and drop."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wishlistor.shared.i18n_fra import (
    COMMON_COLUMN_NAME_HEADER,
    COMMON_COLUMN_NICKNAME_HEADER,
    COMMON_COLUMN_SELECT_HEADER,
)

_COL_SELECT: int = 0
_COL_NAME: int = 1
_COL_NICKNAME: int = 2
_COLUMN_COUNT: int = 3


class _ReorderableTable(QTableWidget):
    """QTableWidget where a press-drag-release gesture reorders whole rows.

    Ordinary clicks (press then release without much movement) are left to
    the base class exactly as before, so checkbox toggling and inline
    nickname editing are untouched. Only once the mouse moves past the
    platform's drag threshold does this widget switch into manually
    relocating the pressed row's items — deliberately bypassing Qt's
    built-in `QAbstractItemModel`-based drag-and-drop, which (a) only
    reorders whole rows reliably for QListWidget/QTreeWidget, not
    QTableWidget, and (b) starts a drag from the *selection* model, which
    is unusable here since selection is disabled (see `ColumnNicknameTableView`).
    """

    row_reordered = Signal()

    def __init__(self, rows: int, columns: int, parent: QWidget) -> None:
        """Initialize the table.

        Args:
            rows: Initial row count.
            columns: Column count.
            parent: The owning widget.
        """
        super().__init__(rows, columns, parent)
        self._press_row: int = -1
        self._press_pos = QPoint()
        self._dragging_row = False
        self._drop_row: int = -1  # "insert before this index" (0..rowCount(): append at the end)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt override
        """Record the pressed row, then let the base class handle the press normally."""
        self._press_row = self.rowAt(event.position().toPoint().y())
        self._press_pos = event.position().toPoint()
        self._dragging_row = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt override
        """Arm row-dragging once the press has moved past the drag threshold."""
        if (
            not self._dragging_row
            and self._press_row >= 0
            and bool(event.buttons() & Qt.MouseButton.LeftButton)
            and (event.position().toPoint() - self._press_pos).manhattanLength()
            >= QApplication.startDragDistance()
        ):
            self._dragging_row = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        if self._dragging_row:
            self._drop_row = self._drop_index_at(event.position().toPoint())
            self.viewport().update()
            return  # suppress hover/selection handling while a row is being dragged
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt override
        """Drop the dragged row at the release position, or forward a plain click."""
        if self._dragging_row:
            self._move_row(self._press_row, self._drop_row)
            self.unsetCursor()
        else:
            super().mouseReleaseEvent(event)
        self._press_row = -1
        self._dragging_row = False
        self._drop_row = -1
        self.viewport().update()

    def _drop_index_at(self, pos: QPoint) -> int:
        """Return the insertion index (0..rowCount()) the given position snaps to."""
        row = self.rowAt(pos.y())
        if row < 0:
            return self.rowCount()
        row_mid = self.rowViewportPosition(row) + self.rowHeight(row) // 2
        return row + 1 if pos.y() >= row_mid else row

    def _move_row(self, source_row: int, target_row: int) -> None:
        """Relocate a row so it lands just before `target_row` (native item data only)."""
        if source_row < 0:
            return
        target_row = max(0, min(target_row, self.rowCount()))
        if target_row in {source_row, source_row + 1}:
            return  # dropped back where it already was
        # The PySide6 stub declares takeItem() as always returning QTableWidgetItem, but at
        # runtime it returns None for an empty cell (defensive check kept via cast below).
        items = [
            cast("QTableWidgetItem | None", self.takeItem(source_row, column))
            for column in range(self.columnCount())
        ]
        self.removeRow(source_row)
        insert_at = target_row - 1 if target_row > source_row else target_row
        self.insertRow(insert_at)
        for column, item in enumerate(items):
            if item is not None:
                self.setItem(insert_at, column, item)
        self.row_reordered.emit()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        """Paint the table normally, then a drop indicator line while dragging a row."""
        super().paintEvent(event)
        if not self._dragging_row:
            return
        painter = QPainter(self.viewport())
        self._paint_source_highlight(painter)
        self._paint_drop_indicator(painter)
        painter.end()

    def _paint_source_highlight(self, painter: QPainter) -> None:
        """Tint the row currently being dragged."""
        if not 0 <= self._press_row < self.rowCount():
            return
        highlight = QColor(self.palette().color(QPalette.ColorRole.Highlight))
        highlight.setAlpha(60)
        top = self.rowViewportPosition(self._press_row)
        painter.fillRect(0, top, self.viewport().width(), self.rowHeight(self._press_row), highlight)

    def _paint_drop_indicator(self, painter: QPainter) -> None:
        """Draw the insertion line at the current drop target."""
        if self.rowCount() == 0:
            return
        if self._drop_row >= self.rowCount():
            last = self.rowCount() - 1
            y = self.rowViewportPosition(last) + self.rowHeight(last)
        else:
            y = self.rowViewportPosition(self._drop_row)
        pen = QPen(self.palette().color(QPalette.ColorRole.Highlight))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(0, y, self.viewport().width(), y)


class ColumnNicknameTableView(QWidget):
    """Reorderable table of CSV columns: a select checkbox, the raw name, and a nickname.

    Every cell is plain item data (no cell widgets), so row reordering moves
    a row's state as a unit with no extra bookkeeping. Clicking the checkbox
    or the raw name toggles selection; clicking the nickname cell edits it
    in place; pressing and dragging a row moves it (see `_ReorderableTable`).
    """

    def __init__(self, parent: QWidget) -> None:
        """Initialize the empty table.

        Args:
            parent: The owning widget.
        """
        super().__init__(parent)
        self.setObjectName("column_nickname_table_view")
        self._on_changed: Callable[[], None] | None = None
        self._suppress_click_toggle = False
        self._table_var = _ReorderableTable(0, _COLUMN_COUNT, self)
        self._table_var.setObjectName("column_nickname_table")
        self._table_var.setHorizontalHeaderLabels(
            [COMMON_COLUMN_SELECT_HEADER, COMMON_COLUMN_NAME_HEADER, COMMON_COLUMN_NICKNAME_HEADER]
        )
        self._table_var.verticalHeader().hide()
        self._configure_header()
        # NoSelection: row selection is not used here (the Sél. checkbox is the only
        # "selected" concept), and it was swallowing the first click on a row — Qt
        # spent it turning the row into the current/selected one instead of toggling.
        self._table_var.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._table_var.setEditTriggers(
            QAbstractItemView.EditTrigger.CurrentChanged
            | QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        self._table_var.itemChanged.connect(self._handle_item_changed)
        self._table_var.cellClicked.connect(self._handle_cell_clicked)
        self._table_var.row_reordered.connect(self._handle_row_moved)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table_var)

    def _configure_header(self) -> None:
        """Set the resize behavior of each column of the header."""
        header = self._table_var.horizontalHeader()
        header.setSectionResizeMode(_COL_SELECT, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(_COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(_COL_NICKNAME, QHeaderView.ResizeMode.Stretch)

    # -- data -----------------------------------------------------------------------

    def set_items(self, items: list[tuple[str, bool]], nicknames: dict[str, str] | None = None) -> None:
        """Replace the whole table content.

        Args:
            items: (raw CSV column name, checked) pairs, in display order.
            nicknames: Column name to nickname mapping.
        """
        nickname_by_name = nicknames or {}
        table = self._table_var
        table.blockSignals(True)
        table.setRowCount(0)
        for name, checked in items:
            self._append_row(name, checked, nickname_by_name.get(name, ""))
        table.blockSignals(False)

    def _append_row(self, name: str, checked: bool, nickname: str) -> None:
        """Insert one (checkbox, name, nickname) row at the bottom of the table."""
        table = self._table_var
        row = table.rowCount()
        table.insertRow(row)
        select_item = QTableWidgetItem()
        select_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
        select_item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        table.setItem(row, _COL_SELECT, select_item)
        name_item = QTableWidgetItem(name)
        name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        table.setItem(row, _COL_NAME, name_item)
        nickname_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        nickname_item = QTableWidgetItem(nickname)
        nickname_item.setFlags(nickname_flags)
        table.setItem(row, _COL_NICKNAME, nickname_item)

    def _rows(self) -> list[tuple[str, bool, str]]:
        """Return every (raw name, checked, nickname) row, in current order."""
        table = self._table_var
        rows: list[tuple[str, bool, str]] = []
        for row in range(table.rowCount()):
            select_item = table.item(row, _COL_SELECT)
            name_item = table.item(row, _COL_NAME)
            nickname_item = table.item(row, _COL_NICKNAME)
            checked = select_item is not None and select_item.checkState() is Qt.CheckState.Checked
            name = name_item.text() if name_item is not None else ""
            nickname = nickname_item.text().strip() if nickname_item is not None else ""
            rows.append((name, checked, nickname))
        return rows

    def checked_labels(self) -> list[str]:
        """Return the checked raw column names, in current order."""
        return [name for name, checked, _nickname in self._rows() if checked]

    def nicknames(self) -> dict[str, str]:
        """Return the non-empty nicknames, keyed by raw column name."""
        return {name: nickname for name, _checked, nickname in self._rows() if nickname}

    def bind_changed(self, callback: Callable[[], None]) -> None:
        """Register the change callback (check toggles, reorders and nickname edits).

        Args:
            callback: Called after any user change.
        """
        self._on_changed = callback

    # -- interaction ----------------------------------------------------------------

    def _handle_item_changed(self, item: QTableWidgetItem) -> None:
        """React to a checkbox toggle or a nickname text edit."""
        if item.column() == _COL_SELECT:
            self._suppress_click_toggle = True
        self._emit_changed()

    def _handle_cell_clicked(self, row: int, column: int) -> None:
        """Toggle selection when the checkbox or the raw name cell is clicked."""
        if column == _COL_NICKNAME:
            return
        if self._suppress_click_toggle:
            self._suppress_click_toggle = False
            return
        item = self._table_var.item(row, _COL_SELECT)
        if item is None:
            return
        state = Qt.CheckState.Unchecked if item.checkState() is Qt.CheckState.Checked else Qt.CheckState.Checked
        item.setCheckState(state)
        # setCheckState() synchronously fires itemChanged, which re-arms the suppress
        # flag above; clear it again so the *next* click isn't swallowed by mistake.
        self._suppress_click_toggle = False

    def _handle_row_moved(self) -> None:
        """React to a drag-and-drop row reorder."""
        self._suppress_click_toggle = False
        self._emit_changed()

    def _emit_changed(self) -> None:
        """Forward a change to the bound callback."""
        if self._on_changed is not None:
            self._on_changed()


# EOF
