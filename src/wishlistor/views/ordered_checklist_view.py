"""Reorderable checklist widget (check, move up/down, drag and drop)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from wishlistor.shared.i18n_fra import (
    COMMON_MOVE_DOWN,
    COMMON_MOVE_DOWN_TOOLTIP,
    COMMON_MOVE_UP,
    COMMON_MOVE_UP_TOOLTIP,
)

_BUTTON_SIZE_PX: int = 28


class OrderedChecklistView(QWidget):
    """Checkable list whose order can be changed (buttons or drag and drop).

    Clicking anywhere on a row toggles its checkbox (spec A.4).
    """

    def __init__(self, parent: QWidget) -> None:
        """Initialize the checklist.

        Args:
            parent: The owning widget.
        """
        super().__init__(parent)
        self.setObjectName("ordered_checklist")
        self._on_changed: Callable[[], None] | None = None
        self._suppress_click_toggle = False
        self._list_var = QListWidget(self)
        self._list_var.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._list_var.itemChanged.connect(self._handle_item_changed)
        self._list_var.itemClicked.connect(self._handle_item_clicked)
        self._list_var.model().rowsMoved.connect(lambda *_args: self._emit_changed())
        self._build_layout()

    def _build_layout(self) -> None:
        """Assemble the list and the move buttons."""
        up_button = QPushButton(COMMON_MOVE_UP, self)
        up_button.setObjectName("checklist_up_button")
        up_button.setFixedWidth(_BUTTON_SIZE_PX)
        up_button.setToolTip(COMMON_MOVE_UP_TOOLTIP)
        up_button.clicked.connect(lambda: self._move_current(-1))
        down_button = QPushButton(COMMON_MOVE_DOWN, self)
        down_button.setObjectName("checklist_down_button")
        down_button.setFixedWidth(_BUTTON_SIZE_PX)
        down_button.setToolTip(COMMON_MOVE_DOWN_TOOLTIP)
        down_button.clicked.connect(lambda: self._move_current(1))
        buttons = QVBoxLayout()
        buttons.addWidget(up_button)
        buttons.addWidget(down_button)
        buttons.addStretch(1)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list_var, 1)
        layout.addLayout(buttons, 0)

    # -- data -----------------------------------------------------------------------

    def set_items(self, items: list[tuple[str, bool]]) -> None:
        """Replace the whole list content.

        Args:
            items: (label, checked) pairs, in display order.
        """
        self._list_var.blockSignals(True)
        self._list_var.clear()
        for label, checked in items:
            item = QListWidgetItem(label)
            flags = item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsDragEnabled
            item.setFlags(flags)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self._list_var.addItem(item)
        self._list_var.blockSignals(False)

    def items(self) -> list[tuple[str, bool]]:
        """Return every (label, checked) pair, in current order."""
        result: list[tuple[str, bool]] = []
        for index in range(self._list_var.count()):
            item = self._list_var.item(index)
            result.append((item.text(), item.checkState() is Qt.CheckState.Checked))
        return result

    def checked_labels(self) -> list[str]:
        """Return the checked labels, in current order."""
        return [label for label, checked in self.items() if checked]

    def bind_changed(self, callback: Callable[[], None]) -> None:
        """Register the change callback (check toggles and reorders).

        Args:
            callback: Called after any user change.
        """
        self._on_changed = callback

    # -- interaction ----------------------------------------------------------------

    def _move_current(self, delta: int) -> None:
        """Swap the current row with its neighbour."""
        row = self._list_var.currentRow()
        target = row + delta
        if row < 0 or target < 0 or target >= self._list_var.count():
            return
        item = self._list_var.takeItem(row)
        self._list_var.insertItem(target, item)
        self._list_var.setCurrentRow(target)
        self._emit_changed()

    def _handle_item_changed(self, item: QListWidgetItem) -> None:
        """React to a checkbox toggle."""
        _ = item
        self._suppress_click_toggle = True
        self._emit_changed()

    def _handle_item_clicked(self, item: QListWidgetItem) -> None:
        """Toggle the checkbox when the row text is clicked (spec A.4)."""
        if self._suppress_click_toggle:
            self._suppress_click_toggle = False
            return
        state = Qt.CheckState.Unchecked if item.checkState() is Qt.CheckState.Checked else Qt.CheckState.Checked
        item.setCheckState(state)
        self._suppress_click_toggle = False

    def _emit_changed(self) -> None:
        """Forward a change to the bound callback."""
        if self._on_changed is not None:
            self._on_changed()


# EOF
