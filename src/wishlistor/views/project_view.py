"""Project module view: history table and inline creation form (spec B.3)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from wishlistor.models.view_state_model import ProjectFormState, ProjectRowState
from wishlistor.shared import i18n_fra
from wishlistor.shared.constants_util import C_COLOR_ERROR, C_COLOR_SELECTION, C_COLOR_SUCCESS
from wishlistor.shared.validation_result import ValidationResult
from wishlistor.views.project_form_view import ProjectFormView

_COL_NAME: int = 0
_COL_WEBSITE: int = 1
_COL_CATEGORY: int = 2
_COL_PATH: int = 3
_COL_OPENED: int = 4
_COL_SIZE: int = 5
_COL_AVAILABLE: int = 6
_COL_ACTION: int = 7
_COLUMN_COUNT: int = 8

_WIDTHS_DEBOUNCE_MS: int = 600
# _COL_PATH is excluded: it stretches to fill the table and is not user-resizable.
_COLUMN_KEYS: dict[int, str] = {
    _COL_NAME: "name",
    _COL_WEBSITE: "website",
    _COL_CATEGORY: "category",
    _COL_OPENED: "last_opened",
    _COL_SIZE: "file_size",
    _COL_AVAILABLE: "available",
    _COL_ACTION: "action",
}


def _make_separator(parent: QWidget) -> QFrame:
    """Build a horizontal separator line."""
    separator = QFrame(parent)
    separator.setFrameShape(QFrame.Shape.HLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    return separator


class _SizeItem(QTableWidgetItem):
    """Table item sorting on the raw byte count instead of the label."""

    def __lt__(self, other: QTableWidgetItem) -> bool:
        """Compare on the numeric byte count stored in UserRole."""
        return int(self.data(Qt.ItemDataRole.UserRole) or 0) < int(other.data(Qt.ItemDataRole.UserRole) or 0)


class ProjectView(QWidget):
    """Project module: list page and form page inside a stacked widget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the module panel.

        Args:
            parent: The owning widget.
        """
        super().__init__(parent)
        self.setObjectName("project_view")
        self.is_dirty: bool = False
        self.is_busy: bool = False
        self.is_loading: bool = False
        self._on_create: Callable[[], None] | None = None
        self._on_project_clicked: Callable[[str], None] | None = None
        self._on_project_deleted: Callable[[str], None] | None = None
        self._on_column_widths_changed: Callable[[dict[str, int]], None] | None = None
        self._stack_var = QStackedWidget(self)
        self._form_var = ProjectFormView(self)
        self._widths_timer_var = QTimer(self)
        self._widths_timer_var.setSingleShot(True)
        self._widths_timer_var.setInterval(_WIDTHS_DEBOUNCE_MS)
        self._widths_timer_var.timeout.connect(self._emit_column_widths)
        self._build_ui()

    # -- construction ---------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the stacked pages."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self._stack_var.addWidget(self._build_list_page())
        self._stack_var.addWidget(self._form_var)
        layout.addWidget(self._stack_var)

    def _build_list_page(self) -> QWidget:
        """Build the history page (title, button, table, count label)."""
        page = QWidget(self)
        page.setObjectName("project_list_page")
        layout = QVBoxLayout(page)
        title = QLabel(i18n_fra.PROJECT_TITLE, page)
        title.setObjectName("project_title")
        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(_make_separator(page))
        self._create_button_var = QPushButton(i18n_fra.PROJECT_CREATE_BUTTON, page)
        self._create_button_var.setObjectName("project_create_button")
        self._create_button_var.clicked.connect(self._emit_create)
        layout.addWidget(self._create_button_var, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(_make_separator(page))
        self._error_label_var = QLabel("", page)
        self._error_label_var.setStyleSheet(f"color: {C_COLOR_ERROR};")
        self._error_label_var.hide()
        layout.addWidget(self._error_label_var)
        self._table_var = self._build_table(page)
        layout.addWidget(self._table_var, 1)
        self._count_label_var = QLabel(i18n_fra.PROJECT_ROW_COUNT.format(count=0), page)
        self._count_label_var.setObjectName("project_count_label")
        layout.addWidget(self._count_label_var, 0, Qt.AlignmentFlag.AlignBottom)
        return page

    def _build_table(self, parent: QWidget) -> QTableWidget:
        """Build the sortable project history table."""
        table = QTableWidget(0, _COLUMN_COUNT, parent)
        table.setObjectName("project_table")
        table.setHorizontalHeaderLabels(
            [
                i18n_fra.PROJECT_COL_NAME,
                i18n_fra.PROJECT_COL_WEBSITE,
                i18n_fra.PROJECT_COL_CATEGORY,
                i18n_fra.PROJECT_COL_CSV_PATH,
                i18n_fra.PROJECT_COL_LAST_OPENED,
                i18n_fra.PROJECT_COL_FILE_SIZE,
                i18n_fra.PROJECT_COL_AVAILABLE,
                i18n_fra.PROJECT_COL_ACTION,
            ]
        )
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(f"QTableWidget::item:hover {{ background-color: {C_COLOR_SELECTION}; }}")
        table.horizontalHeader().setSectionResizeMode(_COL_PATH, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().hide()
        table.cellClicked.connect(self._handle_cell_clicked)
        table.horizontalHeader().sectionResized.connect(self._handle_section_resized)
        return table

    # -- IProjectView ------------------------------------------------------------------

    def show_rows(self, rows: list[ProjectRowState]) -> None:
        """Display the project history table.

        Args:
            rows: Rows to display, most recently opened first.
        """
        table = self._table_var
        self.is_loading = True
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            self._fill_row(index, row)
        table.setSortingEnabled(True)
        table.sortItems(_COL_OPENED, Qt.SortOrder.DescendingOrder)
        self.is_loading = False
        self._count_label_var.setText(i18n_fra.PROJECT_ROW_COUNT.format(count=len(rows)))

    def _fill_row(self, index: int, row: ProjectRowState) -> None:
        """Fill one table row from its state."""
        name_item = QTableWidgetItem(row.name)
        name_item.setData(Qt.ItemDataRole.UserRole, row.id_project)
        self._table_var.setItem(index, _COL_NAME, name_item)
        self._table_var.setItem(index, _COL_WEBSITE, QTableWidgetItem(row.website))
        self._table_var.setItem(index, _COL_CATEGORY, QTableWidgetItem(row.category))
        self._table_var.setItem(index, _COL_PATH, QTableWidgetItem(row.csv_path))
        self._table_var.setItem(index, _COL_OPENED, QTableWidgetItem(row.last_opened))
        size_item = _SizeItem(row.file_size_label)
        size_item.setData(Qt.ItemDataRole.UserRole, row.file_size_bytes)
        self._table_var.setItem(index, _COL_SIZE, size_item)
        label = i18n_fra.COMMON_YES if row.is_available else i18n_fra.PROJECT_FILE_MISSING
        available_item = QTableWidgetItem(label)
        color = C_COLOR_SUCCESS if row.is_available else C_COLOR_ERROR
        available_item.setForeground(QBrush(QColor(color)))
        available_item.setToolTip(label)
        self._table_var.setItem(index, _COL_AVAILABLE, available_item)
        self._add_delete_button(index, row.id_project)

    def _add_delete_button(self, index: int, id_project: str) -> None:
        """Add the 'Effacer' button (removes the project from the list)."""
        button = QPushButton(i18n_fra.PROJECT_DELETE_BUTTON, self._table_var)
        button.setObjectName(f"project_delete_button_{index}")
        button.clicked.connect(lambda _checked=False, key=id_project: self._emit_deleted(key))
        self._table_var.setCellWidget(index, _COL_ACTION, button)

    def show_list(self) -> None:
        """Switch back to the history panel."""
        self._stack_var.setCurrentIndex(0)

    def show_form(self, state: ProjectFormState, headers: list[str], is_edit: bool) -> None:
        """Replace the history panel with the inline form.

        Args:
            state: Initial form values.
            headers: CSV columns available for the mapping pickers.
            is_edit: True when editing an existing project.
        """
        self._form_var.populate(state, headers, is_edit)
        self._stack_var.setCurrentIndex(1)

    def set_form_columns(self, headers: list[str]) -> None:
        """Refresh the column pickers after the CSV path changed.

        Args:
            headers: CSV columns.
        """
        self._form_var.set_form_columns(headers)

    def show_field_errors(self, errors: dict[str, str]) -> None:
        """Show inline, per-field validation feedback.

        Args:
            errors: Field name to French message mapping (empty clears all).
        """
        self._form_var.show_field_errors(errors)

    def snapshot(self) -> ProjectFormState:
        """Return the current content of the project form."""
        return self._form_var.snapshot()

    def apply_column_widths(self, widths: dict[str, int]) -> None:
        """Restore the persisted user column widths of the history table.

        Args:
            widths: Column key to width (pixels) mapping.
        """
        self.is_loading = True
        for column, key in _COLUMN_KEYS.items():
            if key in widths:
                self._table_var.setColumnWidth(column, widths[key])
        self.is_loading = False

    # -- bindings ------------------------------------------------------------------------

    def bind_create_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Créer un projet' button callback."""
        self._on_create = callback

    def bind_project_clicked(self, callback: Callable[[str], None]) -> None:
        """Register the history row click callback (opens the project)."""
        self._on_project_clicked = callback

    def bind_project_deleted(self, callback: Callable[[str], None]) -> None:
        """Register the per-row 'Effacer' button callback."""
        self._on_project_deleted = callback

    def bind_form_submitted(self, callback: Callable[[], None]) -> None:
        """Register the form submit callback."""
        self._form_var.bind_submitted(callback)

    def bind_form_cancelled(self, callback: Callable[[], None]) -> None:
        """Register the form cancel callback."""
        self._form_var.bind_cancelled(callback)

    def bind_csv_path_edited(self, callback: Callable[[str], None]) -> None:
        """Register the CSV path edition callback."""
        self._form_var.bind_csv_path_edited(callback)

    def bind_form_edited(self, callback: Callable[[], None]) -> None:
        """Register the real-time form change callback."""
        self._form_var.bind_edited(callback)

    def bind_row_height_changed(self, callback: Callable[[int], None]) -> None:
        """Register the live row-height change callback."""
        self._form_var.bind_row_height_changed(callback)

    def bind_column_widths_changed(self, callback: Callable[[dict[str, int]], None]) -> None:
        """Register the debounced column-resize persistence callback."""
        self._on_column_widths_changed = callback

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

    # -- base view contract -----------------------------------------------------------------

    def set_enabled(self, enabled: bool) -> None:
        """Grey out or re-enable the module.

        Args:
            enabled: The new enabled state.
        """
        self.setEnabled(enabled)

    def notify_error(self, rs: ValidationResult) -> None:
        """Show the issues in the inline error label of the list page.

        Args:
            rs: The issues to display.
        """
        if rs.has_issues():
            self._error_label_var.setText(rs.concat_issues_by_severity())
            self._error_label_var.show()
        else:
            self._error_label_var.hide()

    def clear(self) -> None:
        """Empty the table and the error label."""
        self._table_var.setRowCount(0)
        self._error_label_var.hide()
        self.is_dirty = False

    def notify_refresh(self, context: object) -> None:
        """Refresh the module according to *context* (unused).

        Args:
            context: Presenter-defined refresh payload.
        """
        _ = context

    # -- internals ----------------------------------------------------------------------------

    def _handle_section_resized(self, _logical: int, _old_size: int, _new_size: int) -> None:
        """Schedule the persistence of a user column resize."""
        if not self.is_loading:
            self._widths_timer_var.start()

    def _emit_column_widths(self) -> None:
        """Collect and forward the current column widths (debounced)."""
        if self._on_column_widths_changed is None:
            return
        widths = {key: self._table_var.columnWidth(column) for column, key in _COLUMN_KEYS.items()}
        self._on_column_widths_changed(widths)

    def _handle_cell_clicked(self, row: int, column: int) -> None:
        """Open the clicked project (any cell except the action column)."""
        if column == _COL_ACTION:
            return
        item = self._table_var.item(row, _COL_NAME)
        if item is None or self._on_project_clicked is None:
            return
        id_project = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if id_project:
            self._on_project_clicked(id_project)

    def _emit_create(self) -> None:
        """Forward the create-project click."""
        if self._on_create is not None:
            self._on_create()

    def _emit_deleted(self, id_project: str) -> None:
        """Forward an 'Effacer' click."""
        if self._on_project_deleted is not None:
            self._on_project_deleted(id_project)


# EOF
