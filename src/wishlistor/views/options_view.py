"""Options module view: application settings with inline validation (B.6)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from wishlistor.models.view_state_model import OptionsViewState
from wishlistor.shared import i18n_fra
from wishlistor.shared.constants_util import C_FONT_SIZE_MAX, C_FONT_SIZE_MIN, C_UNDO_MAX, C_UNDO_MIN
from wishlistor.shared.enums.tag_enum import TagEnum
from wishlistor.shared.tag_util import C_ALL_TAGS, tag_from_label
from wishlistor.shared.validation_result import ValidationResult
from wishlistor.views.field_marker_view import FieldMarkerView
from wishlistor.views.tag_selector_view import TagChecklistView

_DEBOUNCE_MS: int = 400
_WEIGHT_MIN_PERCENT: int = -100
_WEIGHT_MAX_PERCENT: int = 100


def _ordered_labels(labels: frozenset[str]) -> tuple[str, ...]:
    """Return tag labels in their canonical display order."""
    return tuple(tag.value for tag in C_ALL_TAGS if tag.value in labels)


def _labels_to_tags(labels: tuple[str, ...]) -> frozenset[TagEnum]:
    """Convert stored labels into the tag set of a checklist."""
    return frozenset(tag_from_label(label) for label in labels) - {TagEnum.E_UNKNOWN}


def _make_separator(parent: QWidget) -> QFrame:
    """Build a horizontal separator line."""
    separator = QFrame(parent)
    separator.setFrameShape(QFrame.Shape.HLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    return separator


class OptionsView(QWidget):
    """Options module panel implementing IOptionsView."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the module panel.

        Args:
            parent: The owning widget.
        """
        super().__init__(parent)
        self.setObjectName("options_view")
        self.is_dirty: bool = False
        self.is_busy: bool = False
        self.is_loading: bool = False
        self._on_edited: Callable[[], None] | None = None
        self._on_factory_reset: Callable[[], None] | None = None
        self._markers: dict[str, FieldMarkerView] = {}
        self._debounce_var = QTimer(self)
        self._debounce_var.setSingleShot(True)
        self._debounce_var.setInterval(_DEBOUNCE_MS)
        self._debounce_var.timeout.connect(self._emit_edited)
        self._build_ui()

    # -- construction -----------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the options panel."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        title = QLabel(i18n_fra.OPTIONS_TITLE, self)
        title.setObjectName("options_title")
        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(_make_separator(self))
        layout.addLayout(self._build_header_row())
        layout.addWidget(self._build_general_group())
        layout.addWidget(self._build_shortcuts_group())
        layout.addLayout(self._build_weights_and_special_columns_row(), 1)

    def _build_weights_and_special_columns_row(self) -> QHBoxLayout:
        """Row with the tag weights group at 50% width on the left.

        The special columns group takes the other 50% on the right, spanning
        the full available height.
        """
        row = QHBoxLayout()
        row.addWidget(self._build_weights_group(), 1)
        row.addWidget(self._build_special_columns_group(), 1)
        return row

    def _build_shortcuts_group(self) -> QGroupBox:
        """Configurable tags for the fixed Ctrl+O / Ctrl+N combinations."""
        group = QGroupBox(i18n_fra.OPTIONS_SHORTCUTS, self)
        group.setObjectName("options_shortcuts_group")
        form = QFormLayout(group)
        self._shortcut_o_var = TagChecklistView(group, horizontal=True)
        self._shortcut_o_var.bind_changed(self._schedule_edited)
        form.addRow(i18n_fra.OPTIONS_SHORTCUT_CTRL_O, self._wrap("shortcut_ctrl_o_tags", self._shortcut_o_var))
        self._shortcut_t_var = TagChecklistView(group, horizontal=True)
        self._shortcut_t_var.bind_changed(self._schedule_edited)
        form.addRow(i18n_fra.OPTIONS_SHORTCUT_CTRL_T, self._wrap("shortcut_ctrl_t_tags", self._shortcut_t_var))
        self._shortcut_n_var = TagChecklistView(group, horizontal=True)
        self._shortcut_n_var.bind_changed(self._schedule_edited)
        form.addRow(i18n_fra.OPTIONS_SHORTCUT_CTRL_N, self._wrap("shortcut_ctrl_n_tags", self._shortcut_n_var))
        return group

    def _build_header_row(self) -> QHBoxLayout:
        """Last save date label and factory reset button."""
        self._last_save_var = QLabel(i18n_fra.OPTIONS_LAST_SAVE.format(date=i18n_fra.COMMON_EMPTY_VALUE), self)
        self._last_save_var.setObjectName("options_last_save_label")
        reset_button = QPushButton(i18n_fra.OPTIONS_FACTORY_RESET, self)
        reset_button.setObjectName("options_factory_reset_button")
        reset_button.clicked.connect(self._emit_factory_reset)
        row = QHBoxLayout()
        row.addWidget(self._last_save_var, 0)
        row.addStretch(1)
        row.addWidget(reset_button, 0, Qt.AlignmentFlag.AlignRight)
        return row

    def _build_general_group(self) -> QGroupBox:
        """Undo depth and font size."""
        group = QGroupBox("", self)
        group.setObjectName("options_general_group")
        form = QFormLayout(group)
        self._undo_var = QSpinBox(group)
        self._undo_var.setRange(C_UNDO_MIN, C_UNDO_MAX)
        self._undo_var.valueChanged.connect(lambda _value: self._schedule_edited())
        form.addRow(i18n_fra.OPTIONS_UNDO_MAX, self._wrap("undo_max", self._undo_var))
        self._font_size_var = QSpinBox(group)
        self._font_size_var.setRange(C_FONT_SIZE_MIN, C_FONT_SIZE_MAX)
        self._font_size_var.valueChanged.connect(lambda _value: self._schedule_edited())
        form.addRow(i18n_fra.OPTIONS_FONT_SIZE, self._wrap("font_size", self._font_size_var))
        return group

    def _build_weights_group(self) -> QGroupBox:
        """Default tag weights."""
        group = QGroupBox("", self)
        group.setObjectName("options_weights_group")
        layout = QVBoxLayout(group)
        layout.addLayout(self._build_weights_header(group))
        form = QFormLayout()
        layout.addLayout(form)
        self._weight_vars: dict[str, QSpinBox] = {}
        for tag in C_ALL_TAGS:
            spin = QSpinBox(group)
            spin.setRange(_WEIGHT_MIN_PERCENT, _WEIGHT_MAX_PERCENT)
            spin.setSuffix(" %")
            spin.valueChanged.connect(lambda _value: self._schedule_edited())
            self._weight_vars[tag.value] = spin
            form.addRow(tag.value, spin)
        return group

    def _build_weights_header(self, group: QGroupBox) -> QHBoxLayout:
        """Title row for the tag-weights group with the error icon on the right."""
        title = QLabel(i18n_fra.OPTIONS_DEFAULT_TAG_WEIGHTS, group)
        title.setObjectName("options_weights_group_title")
        self._weights_icon_var = FieldMarkerView.icon_only(group)
        row = QHBoxLayout()
        row.addWidget(title, 0)
        row.addStretch(1)
        row.addWidget(self._weights_icon_var, 0)
        return row

    def _build_special_columns_group(self) -> QGroupBox:
        """Special display columns list with add/remove controls."""
        group = QGroupBox(i18n_fra.OPTIONS_SPECIAL_COLUMNS, self)
        group.setObjectName("options_special_columns_group")
        layout = QVBoxLayout(group)
        self._special_list_var = QListWidget(group)
        layout.addWidget(self._wrap("special_display_columns", self._special_list_var), 1)
        self._special_edit_var = QLineEdit(group)
        add_button = QPushButton(i18n_fra.OPTIONS_SPECIAL_COLUMNS_ADD, group)
        add_button.setObjectName("options_special_add_button")
        add_button.clicked.connect(self._add_special_column)
        remove_button = QPushButton(i18n_fra.OPTIONS_SPECIAL_COLUMNS_REMOVE, group)
        remove_button.setObjectName("options_special_remove_button")
        remove_button.clicked.connect(self._remove_special_column)
        row = QHBoxLayout()
        row.addWidget(self._special_edit_var, 1)
        row.addWidget(add_button, 0)
        row.addWidget(remove_button, 0)
        layout.addLayout(row)
        return group

    def _wrap(self, field: str, widget: QWidget) -> FieldMarkerView:
        """Wrap a widget in an inline error marker registered under *field*."""
        marker = FieldMarkerView(widget, self)
        self._markers[field] = marker
        return marker

    # -- IOptionsView ---------------------------------------------------------------------

    def snapshot(self) -> OptionsViewState:
        """Return the current content of the options form."""
        columns = tuple(
            self._special_list_var.item(index).text() for index in range(self._special_list_var.count())
        )
        return OptionsViewState(
            undo_max=self._undo_var.value(),
            default_tag_weights={tag: spin.value() / 100.0 for tag, spin in self._weight_vars.items()},
            special_display_columns=columns,
            font_size=self._font_size_var.value(),
            shortcut_ctrl_o_tags=_ordered_labels(self._shortcut_o_var.tag_labels()),
            shortcut_ctrl_n_tags=_ordered_labels(self._shortcut_n_var.tag_labels()),
            shortcut_ctrl_t_tags=_ordered_labels(self._shortcut_t_var.tag_labels()),
        )

    def show_state(self, state: OptionsViewState, last_save_label: str) -> None:
        """Populate the options form.

        Args:
            state: Values to display.
            last_save_label: Display label of the last options save.
        """
        self.is_loading = True
        self._undo_var.setValue(state.undo_max)
        self._font_size_var.setValue(state.font_size)
        for tag, spin in self._weight_vars.items():
            spin.setValue(round(state.default_tag_weights.get(tag, 0.0) * 100))
        self._special_list_var.clear()
        for column in state.special_display_columns:
            self._special_list_var.addItem(column)
        self._shortcut_o_var.set_tags(_labels_to_tags(state.shortcut_ctrl_o_tags))
        self._shortcut_n_var.set_tags(_labels_to_tags(state.shortcut_ctrl_n_tags))
        self._shortcut_t_var.set_tags(_labels_to_tags(state.shortcut_ctrl_t_tags))
        self.set_last_save_label(last_save_label)
        self.show_field_errors({})
        self.is_loading = False

    def set_last_save_label(self, label: str) -> None:
        """Refresh the last-save date label.

        Args:
            label: The new label.
        """
        self._last_save_var.setText(i18n_fra.OPTIONS_LAST_SAVE.format(date=label))

    def show_field_errors(self, errors: dict[str, str]) -> None:
        """Show inline, per-field validation feedback.

        Args:
            errors: Field name to French message mapping (empty clears all).
        """
        for field, marker in self._markers.items():
            marker.set_error(errors.get(field, ""))
        self._weights_icon_var.set_error(errors.get("default_tag_weights", ""))

    def confirm(self, title: str, message: str) -> bool:
        """Ask a destructive-action confirmation (modal).

        Args:
            title: Dialog title.
            message: Dialog body.

        Returns:
            True when the user confirmed.
        """
        answer = QMessageBox.question(self, title, message)
        return answer == QMessageBox.StandardButton.Yes

    def bind_options_edited(self, callback: Callable[[], None]) -> None:
        """Register the auto-save callback fired on every edit."""
        self._on_edited = callback

    def bind_factory_reset_clicked(self, callback: Callable[[], None]) -> None:
        """Register the factory reset button callback."""
        self._on_factory_reset = callback

    # -- base view contract ------------------------------------------------------------------

    def set_enabled(self, enabled: bool) -> None:
        """Grey out or re-enable the module.

        Args:
            enabled: The new enabled state.
        """
        self.setEnabled(enabled)

    def notify_error(self, rs: ValidationResult) -> None:
        """Surface non-field issues as a tooltip-free message box.

        Args:
            rs: The issues to display.
        """
        if rs.has_errors_or_fatals():
            QMessageBox.warning(self, i18n_fra.OPTIONS_TITLE, rs.concat_issues_by_severity())

    def clear(self) -> None:
        """Reset the displayed values (the presenter repopulates)."""
        self.is_dirty = False

    def notify_refresh(self, context: object) -> None:
        """Refresh the module according to *context* (unused).

        Args:
            context: Presenter-defined refresh payload.
        """
        _ = context

    # -- internals ---------------------------------------------------------------------------

    def _schedule_edited(self) -> None:
        """Restart the auto-save debounce timer."""
        if not self.is_loading:
            self._debounce_var.start()

    def _emit_edited(self) -> None:
        """Fire the debounced auto-save callback."""
        if self._on_edited is not None and not self.is_loading:
            self._on_edited()

    def _emit_factory_reset(self) -> None:
        """Forward the factory reset click."""
        if self._on_factory_reset is not None:
            self._on_factory_reset()

    def _add_special_column(self) -> None:
        """Add the typed special column to the list."""
        text = self._special_edit_var.text().strip()
        if text:
            self._special_list_var.addItem(text)
            self._special_edit_var.clear()
            self._schedule_edited()

    def _remove_special_column(self) -> None:
        """Remove the selected special column from the list."""
        row = self._special_list_var.currentRow()
        if row >= 0:
            self._special_list_var.takeItem(row)
            self._schedule_edited()


# EOF
