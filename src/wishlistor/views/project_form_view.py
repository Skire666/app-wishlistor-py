"""Inline project creation/edition form (spec B.3.1): 3 columns of frames."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from wishlistor.models.view_state_model import ProjectFormState
from wishlistor.shared import i18n_fra
from wishlistor.shared.constants_util import (
    C_COL_CUSTOM_COMMENTS,
    C_COL_CUSTOM_TAGS,
    C_CSV_PRIMARY_KEY,
    C_RANK_COLUMNS,
    C_ROW_HEIGHT_MAX,
    C_ROW_HEIGHT_MIN,
    C_TEXT_FIELD_MAX_LEN,
)
from wishlistor.shared.tag_util import C_ALL_TAGS
from wishlistor.views.column_default_values_view import ColumnDefaultValuesView
from wishlistor.views.column_nickname_table_view import ColumnNicknameTableView
from wishlistor.views.field_marker_view import FieldMarkerView
from wishlistor.views.ordered_checklist_view import OrderedChecklistView

_DEBOUNCE_MS: int = 250
_WEIGHT_MIN_PERCENT: int = -100
_WEIGHT_MAX_PERCENT: int = 100


class ProjectFormView(QWidget):
    """The 6-frame project form: Informations, Tags, Colonnes, Affichage, indexation, valeurs par défaut."""

    def __init__(self, parent: QWidget) -> None:
        """Initialize the form.

        Args:
            parent: The owning widget.
        """
        super().__init__(parent)
        self.setObjectName("project_form")
        self.is_loading: bool = False
        self._is_edit: bool = False
        self._headers: list[str] = []
        self._on_edited: Callable[[], None] | None = None
        self._on_csv_path_edited: Callable[[str], None] | None = None
        self._on_submitted: Callable[[], None] | None = None
        self._on_cancelled: Callable[[], None] | None = None
        self._on_row_height_changed: Callable[[int], None] | None = None
        self._debounce_var = QTimer(self)
        self._debounce_var.setSingleShot(True)
        self._debounce_var.setInterval(_DEBOUNCE_MS)
        self._debounce_var.timeout.connect(self._emit_edited)
        self._markers: dict[str, FieldMarkerView] = {}
        self._build_ui()

    # -- construction -------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the three columns and the action row."""
        columns = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(self._build_info_group())
        left.addWidget(self._build_tags_group())
        left.addStretch(1)
        columns.addLayout(left, 1)
        middle = QVBoxLayout()
        middle.addWidget(self._build_columns_group(), 0)
        middle.addWidget(self._build_search_index_group(), 1)
        columns.addLayout(middle, 1)
        right = QVBoxLayout()
        right.addWidget(self._build_display_group(), 1)
        right.addWidget(self._build_default_values_group(), 1)
        columns.addLayout(right, 1)
        layout = QVBoxLayout(self)
        layout.addLayout(columns, 1)
        layout.addLayout(self._build_actions_row(), 0)

    def _build_info_group(self) -> QGroupBox:
        """Build the 'Informations' frame."""
        group = QGroupBox(i18n_fra.FORM_GROUP_INFO, self)
        group.setObjectName("form_group_info")
        form = QFormLayout(group)
        self._build_csv_path_row(group, form)
        self._name_var = self._add_text_row(group, form, "name", i18n_fra.FORM_FIELD_NAME)
        self._website_var = self._add_text_row(group, form, "website", i18n_fra.FORM_FIELD_WEBSITE)
        self._category_var = self._add_text_row(group, form, "category", i18n_fra.FORM_FIELD_CATEGORY)
        self._build_row_height_field(group, form)
        self._created_at_var = QLabel("", group)
        form.addRow(i18n_fra.FORM_FIELD_CREATED_AT, self._created_at_var)
        return group

    def _build_csv_path_row(self, group: QGroupBox, form: QFormLayout) -> None:
        """Add the CSV path field with its Parcourir button."""
        self._csv_path_var = QLineEdit(group)
        browse = QPushButton(i18n_fra.COMMON_BROWSE, group)
        browse.setObjectName("form_browse_button")
        # NoFocus: clicking Parcourir must not blur the path field (validation on exit only).
        browse.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        browse.clicked.connect(self._browse_csv)
        self._browse_var = browse
        path_row = QWidget(group)
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.addWidget(self._wrap("csv_path", self._csv_path_var), 1)
        path_layout.addWidget(browse, 0)
        form.addRow(i18n_fra.FORM_FIELD_CSV_PATH, path_row)
        self._csv_path_var.editingFinished.connect(self._handle_csv_path)

    def _build_row_height_field(self, group: QGroupBox, form: QFormLayout) -> None:
        """Add the row-height spin box field."""
        self._row_height_var = QSpinBox(group)
        self._row_height_var.setRange(C_ROW_HEIGHT_MIN, C_ROW_HEIGHT_MAX)
        self._row_height_var.valueChanged.connect(self._handle_row_height)
        form.addRow(i18n_fra.FORM_FIELD_ROW_HEIGHT, self._wrap("row_height", self._row_height_var))

    def _add_text_row(self, group: QGroupBox, form: QFormLayout, field: str, label: str) -> QLineEdit:
        """Add one validated text row to the Informations form."""
        edit = QLineEdit(group)
        edit.setMaxLength(C_TEXT_FIELD_MAX_LEN)
        edit.textEdited.connect(lambda _text: self._schedule_edited())
        form.addRow(label, self._wrap(field, edit))
        return edit

    def _build_tags_group(self) -> QGroupBox:
        """Build the 'Tags' frame (weights only, the tag list is frozen)."""
        group = QGroupBox("", self)
        group.setObjectName("form_group_tags")
        layout = QVBoxLayout(group)
        layout.addLayout(self._build_tags_header(group))
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

    def _build_tags_header(self, group: QGroupBox) -> QHBoxLayout:
        """Title row for 'Tags' with the tag-weights error icon on the right."""
        title = QLabel(i18n_fra.FORM_GROUP_TAGS, group)
        title.setObjectName("form_group_tags_title")
        self._tag_weights_icon_var = FieldMarkerView.icon_only(group)
        row = QHBoxLayout()
        row.addWidget(title, 0)
        row.addStretch(1)
        row.addWidget(self._tag_weights_icon_var, 0)
        return row

    def _build_columns_group(self) -> QGroupBox:
        """Build the 'Colonnes' frame (column mapping)."""
        group = QGroupBox(i18n_fra.FORM_GROUP_COLUMNS, self)
        group.setObjectName("form_group_columns")
        form = QFormLayout(group)
        self._primary_var = self._add_combo_row(group, form, "primary_column", i18n_fra.FORM_FIELD_PRIMARY)
        self._released_var = self._add_combo_row(group, form, "released_column", i18n_fra.FORM_FIELD_RELEASED)
        self._popularity_var = self._add_combo_row(
            group, form, "popularity_column", i18n_fra.FORM_FIELD_POPULARITY
        )
        self._scoring_var = self._add_combo_row(group, form, "scoring_column", i18n_fra.FORM_FIELD_SCORING)
        hint = QLabel(i18n_fra.FORM_COLUMNS_ALL_DEFAULT, group)
        hint.setObjectName("form_columns_all_default_hint")
        hint.setWordWrap(True)
        form.addRow(hint)
        return group

    def _build_search_index_group(self) -> QGroupBox:
        """Build the dedicated 'Colonnes à indexer pour la recherche' frame, full height."""
        group = QGroupBox(i18n_fra.FORM_FIELD_SEARCH_INDEX, self)
        group.setObjectName("form_group_search_index")
        layout = QVBoxLayout(group)
        self._search_index_var = OrderedChecklistView(group)
        self._search_index_var.bind_changed(self._schedule_edited)
        layout.addWidget(self._wrap("search_index_columns", self._search_index_var))
        return group

    def _add_combo_row(self, group: QGroupBox, form: QFormLayout, field: str, label: str) -> QComboBox:
        """Add one column-mapping combo row."""
        combo = QComboBox(group)
        combo.currentIndexChanged.connect(lambda _index: self._schedule_edited())
        form.addRow(label, self._wrap(field, combo))
        return combo

    def _build_display_group(self) -> QGroupBox:
        """Build the 'Affichage' frame (visible columns and their order)."""
        group = QGroupBox(i18n_fra.FORM_GROUP_DISPLAY, self)
        group.setObjectName("form_group_display")
        layout = QVBoxLayout(group)
        self._visible_var = ColumnNicknameTableView(group)
        self._visible_var.bind_changed(self._schedule_edited)
        layout.addWidget(self._wrap("visible_columns", self._visible_var))
        return group

    def _build_default_values_group(self) -> QGroupBox:
        """Build the 'Valeurs par défaut des colonnes' frame, error icon beside the title (spec §2)."""
        group = QGroupBox("", self)
        group.setObjectName("form_group_default_values")
        layout = QVBoxLayout(group)
        layout.addLayout(self._build_default_values_header(group))
        self._column_defaults_var = ColumnDefaultValuesView(group)
        self._column_defaults_var.bind_changed(self._handle_column_defaults_changed)
        marker = self._wrap("column_default_values", self._column_defaults_var, show_icon=False)
        layout.addWidget(marker)
        return group

    def _build_default_values_header(self, group: QGroupBox) -> QHBoxLayout:
        """Title row for 'Valeurs par défaut des colonnes' with the error icon on the right."""
        title = QLabel(i18n_fra.FORM_GROUP_DEFAULT_VALUES, group)
        title.setObjectName("form_group_default_values_title")
        self._column_defaults_icon_var = FieldMarkerView.icon_only(group)
        row = QHBoxLayout()
        row.addWidget(title, 0)
        row.addStretch(1)
        row.addWidget(self._column_defaults_icon_var, 0)
        return row

    def _build_actions_row(self) -> QHBoxLayout:
        """Build the cancel/create/validate action row."""
        cancel = QPushButton(i18n_fra.COMMON_CANCEL, self)
        cancel.setObjectName("form_cancel_button")
        cancel.clicked.connect(self._emit_cancelled)
        self._create_var = QPushButton(i18n_fra.FORM_SUBMIT_CREATE, self)
        self._create_var.setObjectName("form_create_button")
        self._create_var.clicked.connect(self._emit_submitted)
        self._validate_var = QPushButton(i18n_fra.FORM_SUBMIT_VALIDATE, self)
        self._validate_var.setObjectName("form_validate_button")
        self._validate_var.clicked.connect(self._emit_submitted)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(cancel)
        row.addWidget(self._create_var)
        row.addWidget(self._validate_var)
        return row

    def _wrap(self, field: str, widget: QWidget, show_icon: bool = True) -> FieldMarkerView:
        """Wrap a widget in an inline error marker registered under *field*."""
        marker = FieldMarkerView(widget, self, show_icon=show_icon)
        self._markers[field] = marker
        return marker

    # -- population ------------------------------------------------------------------

    def populate(self, state: ProjectFormState, headers: list[str], is_edit: bool) -> None:
        """Fill the form.

        Args:
            state: Initial form values.
            headers: CSV columns for the pickers.
            is_edit: True when editing an existing project.
        """
        self.is_loading = True
        self._csv_path_var.setText(state.csv_path)
        self._name_var.setText(state.name)
        self._website_var.setText(state.website)
        self._category_var.setText(state.category)
        self._created_at_var.setText(state.created_at)
        self._row_height_var.setValue(state.row_height)
        for tag, spin in self._weight_vars.items():
            spin.setValue(round(state.tag_weights.get(tag, 0.0) * 100))
        self._is_edit = is_edit
        self._apply_headers(headers, state)
        self._column_defaults_var.set_rows(list(state.column_default_values))
        self.show_field_errors({})
        self._update_submit_enabled()
        self.is_loading = False

    def set_form_columns(self, headers: list[str]) -> None:
        """Refresh the pickers after the CSV path changed, keeping selections.

        Args:
            headers: CSV columns (special columns are appended by the view).
        """
        self.is_loading = True
        self._apply_headers(headers, self.snapshot())
        self._update_submit_enabled()
        self.is_loading = False

    def _apply_headers(self, headers: list[str], state: ProjectFormState) -> None:
        """Rebuild the four combos and the two checklists."""
        self._headers = list(headers)
        default_primary = state.primary_column or (C_CSV_PRIMARY_KEY if C_CSV_PRIMARY_KEY in headers else "")
        self._fill_combo(self._primary_var, headers, default_primary)
        self._fill_combo(self._released_var, headers, state.released_column)
        self._fill_combo(self._popularity_var, headers, state.popularity_column)
        self._fill_combo(self._scoring_var, headers, state.scoring_column)
        search_available = [*headers, C_COL_CUSTOM_TAGS, C_COL_CUSTOM_COMMENTS]
        self._search_index_var.set_items(_ordered_items(search_available, list(state.search_index_columns)))
        display_available = [*headers, C_COL_CUSTOM_TAGS, C_COL_CUSTOM_COMMENTS, *C_RANK_COLUMNS]
        self._visible_var.set_items(
            _ordered_items(display_available, list(state.visible_columns)), dict(state.column_nicknames)
        )
        self._column_defaults_var.set_available_columns(display_available)

    @staticmethod
    def _fill_combo(combo: QComboBox, headers: list[str], current: str) -> None:
        """Fill a mapping combo with an empty choice plus every CSV column."""
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(i18n_fra.FORM_NO_SELECTION, "")
        for name in headers:
            combo.addItem(name, name)
        index = combo.findData(current) if current else 0
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    # -- snapshot / errors --------------------------------------------------------------

    def snapshot(self) -> ProjectFormState:
        """Return the current content of the form."""
        return ProjectFormState(
            csv_path=self._csv_path_var.text(),
            name=self._name_var.text(),
            website=self._website_var.text(),
            category=self._category_var.text(),
            created_at=self._created_at_var.text(),
            row_height=self._row_height_var.value(),
            tag_weights={tag: spin.value() / 100.0 for tag, spin in self._weight_vars.items()},
            primary_column=str(self._primary_var.currentData() or ""),
            released_column=str(self._released_var.currentData() or ""),
            popularity_column=str(self._popularity_var.currentData() or ""),
            scoring_column=str(self._scoring_var.currentData() or ""),
            search_index_columns=tuple(self._search_index_var.checked_labels()),
            visible_columns=tuple(self._visible_var.checked_labels()),
            column_nicknames=dict(self._visible_var.nicknames()),
            column_default_values=tuple(self._column_defaults_var.rows()),
        )

    def show_field_errors(self, errors: dict[str, str]) -> None:
        """Show inline, per-field validation feedback.

        Args:
            errors: Field name to French message mapping (empty clears all).
        """
        for field, marker in self._markers.items():
            marker.set_error(errors.get(field, ""))
        self._column_defaults_icon_var.set_error(errors.get("column_default_values", ""))
        self._tag_weights_icon_var.set_error(errors.get("tag_weights", ""))

    # -- callbacks -----------------------------------------------------------------------

    def bind_edited(self, callback: Callable[[], None]) -> None:
        """Register the debounced form change callback."""
        self._on_edited = callback

    def bind_csv_path_edited(self, callback: Callable[[str], None]) -> None:
        """Register the CSV path edition callback."""
        self._on_csv_path_edited = callback

    def bind_submitted(self, callback: Callable[[], None]) -> None:
        """Register the submit callback."""
        self._on_submitted = callback

    def bind_cancelled(self, callback: Callable[[], None]) -> None:
        """Register the cancel callback."""
        self._on_cancelled = callback

    def bind_row_height_changed(self, callback: Callable[[int], None]) -> None:
        """Register the live row-height change callback."""
        self._on_row_height_changed = callback

    def _schedule_edited(self) -> None:
        """Restart the debounce timer after a user edit."""
        if not self.is_loading:
            self._debounce_var.start()

    def _handle_column_defaults_changed(self) -> None:
        """React to a default-values row change: gate submit, then debounce (spec §3.4)."""
        self._update_submit_enabled()
        self._schedule_edited()

    def _update_submit_enabled(self) -> None:
        """Enable Créer xor Valider per mode, both greyed while default-values are in error."""
        valid = not self._column_defaults_var.has_errors()
        self._create_var.setEnabled(valid and not self._is_edit)
        self._validate_var.setEnabled(valid and self._is_edit)

    def _emit_edited(self) -> None:
        """Fire the debounced edit callback."""
        if self._on_edited is not None and not self.is_loading:
            self._on_edited()

    def _handle_csv_path(self) -> None:
        """Forward a CSV path edition."""
        if self._on_csv_path_edited is not None and not self.is_loading:
            self._on_csv_path_edited(self._csv_path_var.text())

    def _handle_row_height(self, value: int) -> None:
        """Forward a live row-height change."""
        self._schedule_edited()
        if self._on_row_height_changed is not None and not self.is_loading:
            self._on_row_height_changed(value)

    def _browse_csv(self) -> None:
        """Open the native file dialog for the CSV path."""
        path, _selected = QFileDialog.getOpenFileName(
            self, i18n_fra.CSV_OPEN_DIALOG_TITLE, self._csv_path_var.text(), i18n_fra.CSV_FILE_DIALOG_FILTER
        )
        if path:
            self._csv_path_var.setText(path)
            self._handle_csv_path()
            self._schedule_edited()

    def _emit_submitted(self) -> None:
        """Forward the submit click."""
        if self._on_submitted is not None:
            self._on_submitted()

    def _emit_cancelled(self) -> None:
        """Forward the cancel click."""
        if self._on_cancelled is not None:
            self._on_cancelled()


def _ordered_items(available: list[str], selected: list[str]) -> list[tuple[str, bool]]:
    """Order checklist items: selected first (kept order), then the rest."""
    unique_available = list(dict.fromkeys(available))
    items = [(name, True) for name in selected if name in unique_available]
    items.extend((name, False) for name in unique_available if name not in selected)
    return items


# EOF
