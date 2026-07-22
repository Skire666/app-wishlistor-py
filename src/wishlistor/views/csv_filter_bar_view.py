"""Filter and search bar of the CSV module (spec B.4.2), on two rows.

Row 1 holds one checkbox per tag filter (never zero active), a separator,
then row 2 holds the free text filter and the search field with its counter
and navigation buttons.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from wishlistor.shared import i18n_fra
from wishlistor.shared.constants_util import C_COLOR_SELECTION, C_TAG_PILL_SPACING_PX
from wishlistor.shared.tag_util import C_ALL_TAGS, C_TAG_COLORS
from wishlistor.views.tag_pill_view import TagPillView


class CsvFilterBarView(QWidget):
    """Two-row bar: tag filter checkboxes, then free filter and search."""

    def __init__(self, parent: QWidget) -> None:
        """Initialize the bar.

        Args:
            parent: The owning widget.
        """
        super().__init__(parent)
        self.setObjectName("csv_filter_bar")
        self._on_filters_changed: Callable[[], None] | None = None
        self._on_search_text_changed: Callable[[str], None] | None = None
        self._on_search_navigate: Callable[[int], None] | None = None
        self._tag_boxes_var: dict[str, QCheckBox] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._build_tag_row())
        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        layout.addLayout(self._build_filter_and_search_row())

    def _build_tag_row(self) -> QHBoxLayout:
        """One colored pill checkbox per tag, plus the special empty-tags filter."""
        row = QHBoxLayout()
        row.setSpacing(C_TAG_PILL_SPACING_PX)
        for tag in C_ALL_TAGS:
            row.addWidget(self._build_tag_checkbox(tag.value, C_TAG_COLORS[tag]), 0)
        row.addWidget(self._build_tag_checkbox(i18n_fra.CSV_FILTER_EMPTY_TAGS, C_COLOR_SELECTION), 0)
        row.addStretch(1)
        return row

    def _build_tag_checkbox(self, label: str, color: str) -> QCheckBox:
        """Build one pill-styled checkbox filter colored like its tag pill."""
        box = TagPillView(label, color, self)
        box.setObjectName(f"csv_tag_filter_{label}")
        box.setChecked(True)
        box.clicked.connect(self._handle_tag_clicked)
        self._tag_boxes_var[label] = box
        return box

    def _build_filter_and_search_row(self) -> QHBoxLayout:
        """Free text filter and the search field with its navigation."""
        row = QHBoxLayout()
        self._filter_edit_var = QLineEdit(self)
        self._filter_edit_var.setObjectName("csv_filter_edit")
        self._filter_edit_var.returnPressed.connect(self._emit_filters_changed)
        self._filter_counter_var = QLabel("", self)
        self._filter_counter_var.setObjectName("csv_filter_counter")
        self._filter_counter_var.setVisible(False)
        filter_button = QPushButton(i18n_fra.CSV_FILTER_BUTTON, self)
        filter_button.setObjectName("csv_filter_button")
        filter_button.clicked.connect(self._emit_filters_changed)
        clear_button = QPushButton(i18n_fra.CSV_FILTER_CLEAR, self)
        clear_button.setObjectName("csv_filter_clear_button")
        clear_button.clicked.connect(self._clear_filter)
        row.addWidget(self._filter_edit_var, 1)
        row.addWidget(self._filter_counter_var, 0)
        row.addWidget(filter_button, 0)
        row.addWidget(clear_button, 0)
        self._add_search_controls(row)
        return row

    def _add_search_controls(self, row: QHBoxLayout) -> None:
        """Search field, counter label, previous/next buttons."""
        self._search_edit_var = QLineEdit(self)
        self._search_edit_var.setObjectName("csv_search_edit")
        self._search_edit_var.setPlaceholderText(i18n_fra.CSV_SEARCH_PLACEHOLDER)
        self._search_edit_var.textChanged.connect(self._emit_search_text)
        self._search_edit_var.returnPressed.connect(lambda: self._emit_navigate(1))
        self._search_counter_var = QLabel("", self)
        self._search_counter_var.setObjectName("csv_search_counter")
        previous_button = QPushButton(i18n_fra.CSV_SEARCH_PREVIOUS, self)
        previous_button.setObjectName("csv_search_previous_button")
        previous_button.clicked.connect(lambda: self._emit_navigate(-1))
        next_button = QPushButton(i18n_fra.CSV_SEARCH_NEXT, self)
        next_button.setObjectName("csv_search_next_button")
        next_button.clicked.connect(lambda: self._emit_navigate(1))
        row.addSpacing(24)
        row.addWidget(self._search_edit_var, 1)
        row.addWidget(self._search_counter_var, 0)
        row.addWidget(previous_button, 0)
        row.addWidget(next_button, 0)

    # -- state -----------------------------------------------------------------------

    def active_tags(self) -> frozenset[str]:
        """Return the labels of the checked tag filters."""
        return frozenset(label for label, box in self._tag_boxes_var.items() if box.isChecked())

    def filter_text(self) -> str:
        """Return the free filter text."""
        return self._filter_edit_var.text()

    def search_text(self) -> str:
        """Return the search text."""
        return self._search_edit_var.text()

    def set_tag_counts(self, counts: dict[str, int]) -> None:
        """Refresh the per-tag element counts on the checkboxes.

        Args:
            counts: Tag label to row count mapping.
        """
        for label, box in self._tag_boxes_var.items():
            box.setText(f"{label} ({counts.get(label, 0)})")

    def set_filter_counter(self, count: int | None) -> None:
        """Show the row count matched by the free text filter, or hide it if unused.

        Args:
            count: Number of matching rows, or None to hide the counter (no active filter).
        """
        if count is None:
            self._filter_counter_var.setVisible(False)
            return
        self._filter_counter_var.setText(i18n_fra.CSV_FILTER_COUNT.format(count=count))
        self._filter_counter_var.setVisible(True)

    def set_search_counter(self, text: str) -> None:
        """Refresh the search counter label (e.g. '1/37' or '0 trouvé').

        Args:
            text: The counter text.
        """
        if not text:
            text = " - / - "
        self._search_counter_var.setText(text)

    def focus_search(self) -> None:
        """Give the focus to the search field (Ctrl+F)."""
        self._search_edit_var.setFocus()
        self._search_edit_var.selectAll()

    def reset_for_new_document(self) -> None:
        """Re-check every tag filter and clear both text fields (silently)."""
        for box in self._tag_boxes_var.values():
            box.setChecked(True)
        self._filter_edit_var.blockSignals(True)
        self._filter_edit_var.clear()
        self._filter_edit_var.blockSignals(False)
        self._search_edit_var.blockSignals(True)
        self._search_edit_var.clear()
        self._search_edit_var.blockSignals(False)
        self._search_counter_var.clear()

    # -- callbacks --------------------------------------------------------------------

    def bind_filters_changed(self, callback: Callable[[], None]) -> None:
        """Register the tag/text filter change callback."""
        self._on_filters_changed = callback

    def bind_search_text_changed(self, callback: Callable[[str], None]) -> None:
        """Register the search text change callback."""
        self._on_search_text_changed = callback

    def bind_search_navigate(self, callback: Callable[[int], None]) -> None:
        """Register the search navigation callback (+1 next, -1 previous)."""
        self._on_search_navigate = callback

    # -- internals ----------------------------------------------------------------------

    def _handle_tag_clicked(self) -> None:
        """Enforce 'never zero active filter' then notify (spec B.4.2)."""
        if not self.active_tags():
            self._tag_boxes_var[i18n_fra.CSV_FILTER_EMPTY_TAGS].setChecked(True)
        self._emit_filters_changed()

    def _clear_filter(self) -> None:
        """Clear the free text filter and notify."""
        self._filter_edit_var.blockSignals(True)
        self._filter_edit_var.clear()
        self._filter_edit_var.blockSignals(False)
        self._emit_filters_changed()

    def _emit_filters_changed(self) -> None:
        """Forward a filter change."""
        if self._on_filters_changed is not None:
            self._on_filters_changed()

    def _emit_search_text(self, text: str) -> None:
        """Forward a search text change."""
        if self._on_search_text_changed is not None:
            self._on_search_text_changed(text)

    def _emit_navigate(self, delta: int) -> None:
        """Forward a search navigation request."""
        if self._on_search_navigate is not None:
            self._on_search_navigate(delta)


# EOF
