"""Journal module view: read-only session log table, newest first (spec B.5)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wishlistor.models.view_state_model import JournalRowState
from wishlistor.shared import i18n_fra
from wishlistor.shared.constants_util import C_COLOR_LINK, C_COLOR_SELECTION
from wishlistor.shared.validation_result import ValidationResult

_LEVELS: tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
_COL_DATE: int = 0
_COL_LEVEL: int = 1
_COL_SOURCE: int = 2
_COL_MESSAGE: int = 3
_COL_COPY: int = 4
_COLUMN_COUNT: int = 5
_MAX_DISPLAYED_ROWS: int = 2000


def _make_separator(parent: QWidget) -> QFrame:
    """Build a horizontal separator line."""
    separator = QFrame(parent)
    separator.setFrameShape(QFrame.Shape.HLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    return separator


class JournalView(QWidget):
    """Journal module panel implementing IJournalView."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the module panel.

        Args:
            parent: The owning widget.
        """
        super().__init__(parent)
        self.setObjectName("journal_view")
        self.is_dirty: bool = False
        self.is_busy: bool = False
        self.is_loading: bool = False
        self._on_levels_changed: Callable[[frozenset[str]], None] | None = None
        self._on_clear: Callable[[], None] | None = None
        self._on_open_folder: Callable[[], None] | None = None
        self._level_boxes: dict[str, QCheckBox] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        """Assemble the journal panel."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        title = QLabel(i18n_fra.JOURNAL_TITLE, self)
        title.setObjectName("journal_title")
        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(_make_separator(self))
        layout.addLayout(self._build_controls_row())
        layout.addWidget(_make_separator(self))
        self._table_var = self._build_table()
        layout.addWidget(self._table_var, 1)

    def _build_controls_row(self) -> QHBoxLayout:
        """Level checkboxes with counts, log folder link, clear button."""
        row = QHBoxLayout()
        for level in _LEVELS:
            box = QCheckBox(i18n_fra.JOURNAL_LEVEL_COUNT.format(level=level, count=0), self)
            box.setObjectName(f"journal_level_{level.lower()}")
            box.setChecked(True)
            box.toggled.connect(lambda _checked: self._emit_levels())
            self._level_boxes[level] = box
            row.addWidget(box, 0)
        row.addStretch(1)
        link = QLabel(f'<a href="#" style="color: {C_COLOR_LINK};">{i18n_fra.JOURNAL_OPEN_LOG_FOLDER}</a>', self)
        link.setObjectName("journal_open_folder_link")
        link.linkActivated.connect(lambda _href: self._emit_open_folder())
        row.addWidget(link, 0)
        clear_button = QPushButton(i18n_fra.JOURNAL_CLEAR_BUTTON, self)
        clear_button.setObjectName("journal_clear_button")
        clear_button.clicked.connect(self._emit_clear)
        row.addWidget(clear_button, 0)
        return row

    def _build_table(self) -> QTableWidget:
        """Build the read-only log table."""
        table = QTableWidget(0, _COLUMN_COUNT, self)
        table.setObjectName("journal_table")
        table.setHorizontalHeaderLabels(
            [
                i18n_fra.JOURNAL_COL_DATE,
                i18n_fra.JOURNAL_COL_LEVEL,
                i18n_fra.JOURNAL_COL_SOURCE,
                i18n_fra.JOURNAL_COL_MESSAGE,
                "",
            ]
        )
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(f"QTableWidget::item:hover {{ background-color: {C_COLOR_SELECTION}; }}")
        table.horizontalHeader().setSectionResizeMode(_COL_MESSAGE, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().hide()
        return table

    # -- IJournalView ------------------------------------------------------------------

    def snapshot(self) -> frozenset[str]:
        """Return the level names currently checked."""
        return frozenset(level for level, box in self._level_boxes.items() if box.isChecked())

    def append_entry(self, entry: JournalRowState) -> None:
        """Prepend a log entry to the table (newest on top).

        Args:
            entry: The record to display.
        """
        table = self._table_var
        table.insertRow(0)
        table.setItem(0, _COL_DATE, QTableWidgetItem(entry.date_label))
        table.setItem(0, _COL_LEVEL, QTableWidgetItem(entry.level))
        table.setItem(0, _COL_SOURCE, QTableWidgetItem(entry.source))
        table.setItem(0, _COL_MESSAGE, QTableWidgetItem(entry.message))
        copy_button = QPushButton(i18n_fra.COMMON_COPY, table)
        line = f"{entry.date_label}\t{entry.level}\t{entry.source}\t{entry.message}"
        copy_button.clicked.connect(lambda _checked=False, text=line: self._copy_line(text))
        table.setCellWidget(0, _COL_COPY, copy_button)
        table.setRowHidden(0, entry.level not in self.snapshot())
        if table.rowCount() > _MAX_DISPLAYED_ROWS:
            table.removeRow(table.rowCount() - 1)

    def set_level_counts(self, counts: dict[str, int]) -> None:
        """Refresh the per-level counters next to the checkboxes.

        Args:
            counts: Level name to record count mapping.
        """
        for level, box in self._level_boxes.items():
            box.setText(i18n_fra.JOURNAL_LEVEL_COUNT.format(level=level, count=counts.get(level, 0)))

    def apply_level_filter(self, levels: frozenset[str]) -> None:
        """Show only the rows whose level is in *levels*.

        Args:
            levels: Level names to keep visible.
        """
        table = self._table_var
        for row in range(table.rowCount()):
            item = table.item(row, _COL_LEVEL)
            table.setRowHidden(row, item is None or item.text() not in levels)

    def clear_entries(self) -> None:
        """Empty the displayed table (files are not touched)."""
        self._table_var.setRowCount(0)

    def bind_levels_changed(self, callback: Callable[[frozenset[str]], None]) -> None:
        """Register the level checkbox callback."""
        self._on_levels_changed = callback

    def bind_clear_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Vider l'affichage' button callback."""
        self._on_clear = callback

    def bind_open_folder_clicked(self, callback: Callable[[], None]) -> None:
        """Register the log-folder hyperlink callback."""
        self._on_open_folder = callback

    # -- base view contract ----------------------------------------------------------------

    def set_enabled(self, enabled: bool) -> None:
        """Grey out or re-enable the module.

        Args:
            enabled: The new enabled state.
        """
        self.setEnabled(enabled)

    def notify_error(self, rs: ValidationResult) -> None:
        """No dedicated error area: errors land in the journal itself.

        Args:
            rs: The issues (ignored, already logged).
        """
        _ = rs

    def clear(self) -> None:
        """Empty the displayed table."""
        self.clear_entries()

    def notify_refresh(self, context: object) -> None:
        """Refresh the module according to *context* (unused).

        Args:
            context: Presenter-defined refresh payload.
        """
        _ = context

    # -- internals ------------------------------------------------------------------------------

    def _copy_line(self, text: str) -> None:
        """Copy one journal line to the clipboard."""
        QGuiApplication.clipboard().setText(text)

    def _emit_levels(self) -> None:
        """Forward a level filter change."""
        if self._on_levels_changed is not None:
            self._on_levels_changed(self.snapshot())

    def _emit_clear(self) -> None:
        """Forward the clear-display click."""
        if self._on_clear is not None:
            self._on_clear()

    def _emit_open_folder(self) -> None:
        """Forward the open-log-folder click."""
        if self._on_open_folder is not None:
            self._on_open_folder()


# EOF
