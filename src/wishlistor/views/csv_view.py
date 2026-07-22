"""CSV module view: table, filters, search, URL insertion, mass actions (B.4)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from wishlistor.interfaces.i_image_repository import IImageRepository
from wishlistor.models.csv_document_model import CsvDocumentModel
from wishlistor.models.view_state_model import CsvViewState
from wishlistor.shared import i18n_fra
from wishlistor.shared.constants_util import (
    C_COL_CUSTOM_TAGS,
    C_COLOR_ERROR,
    C_COLOR_LINK,
    C_COLOR_SUCCESS,
    C_SEPARATOR_WIDTH_PX,
    C_SHORTCUT_CTRL_N,
    C_SHORTCUT_CTRL_O,
    C_SHORTCUT_CTRL_T,
)
from wishlistor.shared.enums.save_choice_enum import SaveChoiceEnum
from wishlistor.shared.enums.tag_enum import TagEnum
from wishlistor.shared.validation_result import ValidationResult
from wishlistor.views import csv_column_sizer_view, csv_dialogs_view, csv_sort_view
from wishlistor.views.busy_overlay_view import BusyOverlayView
from wishlistor.views.column_manager_view import ask_visible_columns
from wishlistor.views.csv_bindings_view import CsvBindingsMixin
from wishlistor.views.csv_cell_delegate_view import CsvCellDelegateView, is_link_value
from wishlistor.views.csv_filter_bar_view import CsvFilterBarView
from wishlistor.views.csv_footer_view import CsvFooterView
from wishlistor.views.csv_header_state_view import CsvHeaderStateView
from wishlistor.views.csv_search_nav_view import CsvSearchNavView
from wishlistor.views.csv_table_model_view import CsvTableModelView
from wishlistor.views.tag_selector_view import open_mass_tags, open_row_tags


def _make_separator(parent: QWidget) -> QFrame:
    """Build a horizontal separator line."""
    separator = QFrame(parent)
    separator.setFrameShape(QFrame.Shape.HLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    return separator


class CsvView(QWidget, CsvBindingsMixin):
    """CSV module panel implementing ICsvView."""

    def __init__(self, image_repository: IImageRepository, parent: QWidget | None = None) -> None:
        """Initialize the module panel.

        Args:
            image_repository: Reads image bytes referenced by file-based image cells.
            parent: The owning widget.
        """
        super().__init__(parent)
        self.setObjectName("csv_view")
        self.is_dirty: bool = False
        self.is_busy: bool = False
        self.is_loading: bool = False
        self._document: CsvDocumentModel | None = None
        self._column_nicknames: dict[str, str] = {}
        self._callbacks: dict[str, Callable[..., None]] = {}
        self._model_var = CsvTableModelView()
        self._delegate_var = CsvCellDelegateView(image_repository)
        self._delegate_var.bind_delete_clicked(self._handle_delete_clicked)
        self._build_ui()
        self._build_shortcuts()

    # -- construction ----------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble the stacked pages (no-project message / full panel)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        title = QLabel(i18n_fra.CSV_TITLE, self)
        title.setObjectName("csv_title")
        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(_make_separator(self))
        self._stack_var = QStackedWidget(self)
        self._no_project_var = QLabel(i18n_fra.CSV_NO_PROJECT, self)
        self._no_project_var.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stack_var.addWidget(self._no_project_var)
        self._stack_var.addWidget(self._build_main_page())
        layout.addWidget(self._stack_var, 1)
        self._overlay_var = BusyOverlayView(self)

    def _build_main_page(self) -> QWidget:
        """Assemble the full CSV panel (rows 3 to 11 of the spec)."""
        page = QWidget(self)
        page.setObjectName("csv_main_page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._build_project_row(page))
        layout.addWidget(_make_separator(page))
        self._filter_bar_var = CsvFilterBarView(page)
        self._filter_bar_var.bind_filters_changed(self._apply_filters)
        self._filter_bar_var.bind_search_text_changed(lambda _text: self._reset_search())
        self._filter_bar_var.bind_search_navigate(self._navigate_search)
        layout.addWidget(self._filter_bar_var)
        layout.addWidget(_make_separator(page))
        layout.addLayout(self._build_url_row(page))
        layout.addWidget(_make_separator(page))
        layout.addLayout(self._build_selection_row(page))
        layout.addWidget(self._build_table(page), 1)
        layout.addWidget(self._build_footer(page))
        self._search_nav_var = CsvSearchNavView(self._table_var, self._model_var, self._filter_bar_var)
        return page

    def _build_project_row(self, page: QWidget) -> QHBoxLayout:
        """Row 3: project combo, open-folder link, project options button."""
        self._project_combo_var = QComboBox(page)
        self._project_combo_var.setObjectName("csv_project_combo")
        self._project_combo_var.currentIndexChanged.connect(self._handle_project_selected)
        link = QLabel(f'<a href="#" style="color: {C_COLOR_LINK};">{i18n_fra.CSV_OPEN_FOLDER}</a>', page)
        link.setObjectName("csv_open_folder_link")
        link.linkActivated.connect(lambda _href: self._emit("open_folder"))
        self._options_button_var = QPushButton(i18n_fra.CSV_PROJECT_OPTIONS, page)
        self._options_button_var.setObjectName("csv_project_options_button")
        self._options_button_var.setEnabled(False)
        self._options_button_var.clicked.connect(lambda: self._emit("project_options"))
        row = QHBoxLayout()
        row.addWidget(self._project_combo_var, 1)
        row.addWidget(link, 0)
        row.addWidget(self._options_button_var, 0, Qt.AlignmentFlag.AlignRight)
        return row

    def _build_url_row(self, page: QWidget) -> QHBoxLayout:
        """Row 7: URL field, add button, feedback label, mass action buttons."""
        self._url_edit_var = QLineEdit(page)
        self._url_edit_var.setObjectName("csv_url_edit")
        self._url_edit_var.setPlaceholderText(i18n_fra.CSV_URL_PLACEHOLDER)
        self._url_edit_var.returnPressed.connect(self._submit_url)
        add_button = QPushButton(i18n_fra.CSV_URL_ADD_BUTTON, page)
        add_button.setObjectName("csv_url_add_button")
        add_button.clicked.connect(self._submit_url)
        self._url_feedback_var = QLabel("", page)
        self._url_feedback_var.setObjectName("csv_url_feedback")
        self._mass_tags_button_var = QPushButton(i18n_fra.CSV_EDIT_TAGS_BUTTON, page)
        self._mass_tags_button_var.clicked.connect(lambda: self._emit("mass_tags"))
        self._mass_comment_button_var = QPushButton(i18n_fra.CSV_EDIT_COMMENT_BUTTON, page)
        self._mass_comment_button_var.clicked.connect(lambda: self._emit("mass_comment"))
        self._delete_rows_button_var = QPushButton(i18n_fra.CSV_DELETE_ROW_BUTTON, page)
        self._delete_rows_button_var.clicked.connect(lambda: self._emit("delete_rows"))
        self.set_mass_actions_enabled(False)
        row = QHBoxLayout()
        row.addWidget(self._url_edit_var, 1)
        row.addWidget(add_button, 0)
        row.addWidget(self._url_feedback_var, 0)
        row.addSpacing(C_SEPARATOR_WIDTH_PX)
        row.addWidget(self._mass_tags_button_var, 0)
        row.addWidget(self._mass_comment_button_var, 0)
        row.addWidget(self._delete_rows_button_var, 0)
        return row

    def _build_selection_row(self, page: QWidget) -> QHBoxLayout:
        """Row 9: deselect, select-all, invert, selected count, column manager."""
        deselect = QPushButton(i18n_fra.CSV_DESELECT_ALL, page)
        deselect.setObjectName("csv_deselect_button")
        deselect.clicked.connect(self._model_var.clear_all_checks)
        select_all = QPushButton(i18n_fra.CSV_SELECT_ALL, page)
        select_all.setObjectName("csv_select_all_button")
        select_all.clicked.connect(self._model_var.check_all_visible)
        invert = QPushButton(i18n_fra.CSV_INVERT_SELECTION, page)
        invert.setObjectName("csv_invert_selection_button")
        invert.clicked.connect(self._model_var.invert_visible_checks)
        self._selected_label_var = QLabel(i18n_fra.CSV_SELECTED_COUNT.format(count=0), page)
        self._selected_label_var.setObjectName("csv_selected_label")
        manage = QPushButton(i18n_fra.CSV_MANAGE_COLUMNS, page)
        manage.setObjectName("csv_manage_columns_button")
        manage.clicked.connect(self._open_column_manager)
        row = QHBoxLayout()
        row.addWidget(deselect, 0)
        row.addWidget(select_all, 0)
        row.addWidget(invert, 0)
        row.addWidget(self._selected_label_var, 0)
        row.addStretch(1)
        row.addWidget(manage, 0, Qt.AlignmentFlag.AlignRight)
        return row

    def _build_table(self, page: QWidget) -> QTableView:
        """Row 10: the main table."""
        table = QTableView(page)
        table.setObjectName("csv_table")
        table.setModel(self._model_var)
        table.setItemDelegate(self._delegate_var)
        table.setSortingEnabled(True)
        header = table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header_font = header.font()
        header_font.setBold(False)  # Windows bolds the clicked/sorted section otherwise (native style quirk)
        header.setFont(header_font)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        table.setMouseTracking(True)
        table.entered.connect(self._handle_cell_entered)
        table.clicked.connect(self._handle_cell_clicked)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(lambda _pos: self._open_column_manager())
        header.sortIndicatorChanged.connect(self._handle_sort_changed)
        self._table_var = table
        self._header_state_var = CsvHeaderStateView(self, table, self._model_var)
        self._header_state_var.bind_guards(lambda: self.is_loading, lambda: self._document is not None)
        return table

    def _build_footer(self, page: QWidget) -> CsvFooterView:
        """Row 11: counters frame, inline banner, save frame."""
        self._footer_var = CsvFooterView(page)
        self._footer_var.bind_save_clicked(lambda: self._emit("save"))
        return self._footer_var

    def _build_shortcuts(self) -> None:
        """Register the CSV-module keyboard shortcuts (spec A.3)."""
        bindings: list[tuple[str, Callable[[], None]]] = [
            ("Ctrl+S", lambda: self._emit("save")),
            ("Ctrl+Z", lambda: self._emit("undo")),
            ("Ctrl+Y", lambda: self._emit("redo")),
            ("Ctrl+F", self._focus_search),
            ("Ctrl+O", lambda: self._emit("shortcut_tags", C_SHORTCUT_CTRL_O)),
            ("Ctrl+N", lambda: self._emit("shortcut_tags", C_SHORTCUT_CTRL_N)),
            ("Ctrl+T", lambda: self._emit("shortcut_tags", C_SHORTCUT_CTRL_T)),
        ]
        for sequence, handler in bindings:
            shortcut = QShortcut(QKeySequence(sequence), self)
            # WidgetWithChildrenShortcut: active in the CSV module only (spec A.3),
            # never from the Projet/Journal/Options panels.
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(handler)

    # -- ICsvView: presenter -> view --------------------------------------------------

    def snapshot(self) -> CsvViewState:
        """Return the current state of the interactive controls."""
        current = self._table_var.currentIndex()
        return CsvViewState(
            url_text=self._url_edit_var.text(),
            filter_text=self._filter_bar_var.filter_text(),
            search_text=self._filter_bar_var.search_text(),
            active_tag_filters=self._filter_bar_var.active_tags(),
            checked_rows=tuple(self._model_var.checked_rows()),
            current_doc_row=self._model_var.doc_row_at(current.row()) if current.isValid() else -1,
        )

    def set_projects(self, entries: list[tuple[str, str]], current_id: str) -> None:
        """Fill the project combo box.

        Args:
            entries: (project id, display label) pairs, recency first.
            current_id: Project id to select (empty for none).
        """
        combo = self._project_combo_var
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("", "")
        for id_project, label in entries:
            combo.addItem(label, id_project)
        index = combo.findData(current_id) if current_id else 0
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def show_no_project(self, message: str) -> None:
        """Show the inline invitation instead of the table.

        Args:
            message: French invitation text.
        """
        self._no_project_var.setText(message)
        self._stack_var.setCurrentIndex(0)
        self._options_button_var.setEnabled(False)

    def show_document(self, document: CsvDocumentModel, visible_columns: list[str], row_height: int) -> None:
        """Display a freshly loaded document.

        Args:
            document: The loaded document.
            visible_columns: Column names to show, in display order.
            row_height: Row height in pixels.
        """
        self.is_loading = True
        self._document = document
        self._delegate_var.set_csv_path(document.csv_path)
        self._model_var.set_document(document, visible_columns)
        self.set_row_height(row_height)
        # Every tag filter starts active on a fresh document (spec B.4).
        self._filter_bar_var.reset_for_new_document()
        self._url_feedback_var.clear()
        self._stack_var.setCurrentIndex(1)
        self._options_button_var.setEnabled(True)
        self.is_loading = False
        self._apply_filters()
        self._fit_delete_column()

    def refresh_table(self) -> None:
        """Re-read the document and repaint the table (keeps filters and sort)."""
        self._model_var.refresh()
        self._refresh_counts()
        self._reset_search()

    def set_row_height(self, row_height: int) -> None:
        """Apply a new row height in real time.

        Args:
            row_height: Row height in pixels.
        """
        self._table_var.verticalHeader().setDefaultSectionSize(row_height)

    def set_visible_columns(self, visible_columns: list[str]) -> None:
        """Apply a new visible-column set and order.

        Args:
            visible_columns: Column names to show, in display order.
        """
        self._model_var.set_visible_columns(visible_columns)
        self._fit_delete_column()

    def set_column_nicknames(self, nicknames: dict[str, str]) -> None:
        """Apply the column nickname mapping to the table header.

        Args:
            nicknames: Column name to display nickname mapping.
        """
        self._column_nicknames = dict(nicknames)
        self._model_var.set_column_nicknames(nicknames)

    def apply_column_widths(self, widths: dict[str, int]) -> None:
        """Restore the persisted user column widths.

        Args:
            widths: Column name to width (pixels) mapping.
        """
        self.is_loading = True
        csv_column_sizer_view.apply_column_widths(self._table_var, self._model_var, widths)
        self.is_loading = False

    def auto_size_columns(self) -> None:
        """First-open sizing: fit each column to its content, capped at 200 px."""
        self.is_loading = True
        csv_column_sizer_view.auto_size_columns(self._table_var, self._model_var)
        self.is_loading = False

    def apply_sort_order(self, column: str, descending: bool) -> None:
        """Restore the persisted sort order.

        Args:
            column: Sorted column name (empty leaves the natural row order).
            descending: True for a descending sort.
        """
        self.is_loading = True
        csv_sort_view.apply_sort_order(self._table_var, self._model_var, column, descending)
        self.is_loading = False

    def _fit_delete_column(self) -> None:
        """Give the leading selection column and the trailing delete column their fixed small widths."""
        csv_column_sizer_view.fit_check_column(self._table_var, self._model_var)
        csv_column_sizer_view.fit_delete_column(self._table_var, self._model_var)

    def set_mass_actions_enabled(self, enabled: bool) -> None:
        """Enable or grey out the mass action buttons.

        Args:
            enabled: True when at least one row is checked.
        """
        self._mass_tags_button_var.setEnabled(enabled)
        self._mass_comment_button_var.setEnabled(enabled)
        self._delete_rows_button_var.setEnabled(enabled)

    def set_save_enabled(self, enabled: bool) -> None:
        """Enable or grey out the save button.

        Args:
            enabled: True when unsaved modifications exist.
        """
        self._footer_var.set_save_enabled(enabled)
        self.is_dirty = enabled

    def set_last_save_label(self, label: str) -> None:
        """Refresh the 'Dernière sauvegarde' label.

        Args:
            label: Display text.
        """
        if label == i18n_fra.COMMON_EMPTY_VALUE:
            label = i18n_fra.COMMON_EMPTY_VALUE + "                "
        self._footer_var.set_last_save_label(label)

    def set_file_mtime_label(self, label: str) -> None:
        """Refresh the on-disk mtime label of the footer.

        Args:
            label: Display text.
        """
        self._footer_var.set_mtime_label(label)

    def set_url_feedback(self, message: str, is_error: bool) -> None:
        """Show the verification label next to the URL field.

        Args:
            message: Feedback text (empty clears it).
            is_error: True renders the error color.
        """
        color = C_COLOR_ERROR if is_error else C_COLOR_SUCCESS
        self._url_feedback_var.setStyleSheet(f"color: {color};")
        self._url_feedback_var.setText(message)

    def append_banner_issues(self, rs: ValidationResult) -> None:
        """Append warnings and errors to the inline footer banner.

        Args:
            rs: Issues to list.
        """
        self._footer_var.append_issues(rs)

    def clear_banner(self) -> None:
        """Empty the inline footer banner."""
        self._footer_var.clear_banner()

    def focus_doc_row(self, row_index: int) -> None:
        """Highlight and scroll to a document row (if currently visible).

        Args:
            row_index: Row index in file order.
        """
        view_row = self._model_var.view_row_of(row_index)
        if view_row < 0:
            return
        index = self._model_var.index(view_row, 1)
        self._table_var.setCurrentIndex(index)
        self._table_var.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)

    def peek_next_doc_row(self) -> int:
        """Return the document row right after the current one, in the display order still in effect.

        Meant to be called before an edit that may re-sort the table, so the
        Presenter can capture "the next row" before the sort moves rows around.

        Returns:
            The document row index, or -1 when there is no next visible row.
        """
        current = self._table_var.currentIndex()
        next_row = current.row() + 1 if current.isValid() else 0
        if next_row < self._model_var.visible_row_count():
            return self._model_var.doc_row_at(next_row)
        return -1

    def set_busy(self, busy: bool) -> None:
        """Show or hide the blocking progress overlay (min 250 ms).

        Args:
            busy: True while a worker runs.
        """
        self.is_busy = busy
        if busy:
            self._overlay_var.show_busy()
        else:
            self._overlay_var.hide_busy()

    # -- ICsvView: dialogs ----------------------------------------------------------------

    def ask_unsaved_choice(self) -> SaveChoiceEnum:
        """Ask what to do with unsaved modifications (spec F)."""
        return csv_dialogs_view.ask_unsaved_choice(self)

    def ask_conflict_choice(self) -> SaveChoiceEnum:
        """Ask what to do when the file changed externally (spec D.5)."""
        return csv_dialogs_view.ask_conflict_choice(self)

    def ask_save_as_path(self, current_path: str) -> str:
        """Open the native save dialog.

        Args:
            current_path: Initial location.

        Returns:
            The chosen path, or an empty string on cancel.
        """
        return csv_dialogs_view.ask_save_as_path(self, current_path)

    def ask_mass_comment(self) -> str | None:
        """Ask the comment to apply to the selected rows (None on cancel)."""
        return csv_dialogs_view.ask_mass_comment(self)

    def open_mass_tags(self, callback: Callable[[frozenset[str] | None], None]) -> None:
        """Open the modeless tag composer next to the button."""
        button = self._mass_tags_button_var
        anchor_pos = button.mapToGlobal(button.rect().bottomLeft())
        open_mass_tags(self, callback, anchor_pos)

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

    def show_critical(self, title: str, message: str) -> None:
        """Show a blocking error popup (critical project load failure).

        Args:
            title: Dialog title.
            message: Dialog body.
        """
        QMessageBox.critical(self, title, message)

    # -- ICsvView: bindings ------------------------------------------------------------------
    # See CsvBindingsMixin (csv_bindings_view.py) for bind_* callback registration.

    # -- base view contract ---------------------------------------------------------------------

    def set_enabled(self, enabled: bool) -> None:
        """Grey out or re-enable the module.

        Args:
            enabled: The new enabled state.
        """
        self.setEnabled(enabled)

    def notify_error(self, rs: ValidationResult) -> None:
        """Surface issues in the inline banner.

        Args:
            rs: The issues to display.
        """
        self.append_banner_issues(rs)

    def clear(self) -> None:
        """Reset the panel to its no-document state."""
        self._document = None
        self._column_nicknames = {}
        self._delegate_var.set_csv_path("")
        self._model_var.set_document(None, [])
        self.clear_banner()
        self._url_edit_var.clear()
        self._url_feedback_var.clear()
        self.set_save_enabled(False)

    def notify_refresh(self, context: object) -> None:
        """Refresh the table (context unused).

        Args:
            context: Presenter-defined refresh payload.
        """
        _ = context
        self.refresh_table()

    # -- internals --------------------------------------------------------------------------------

    def _emit(self, key: str, *args: object) -> None:
        """Invoke a bound callback if present."""
        callback = self._callbacks.get(key)
        # is_loading suppresses cascading recomputations while the view rebuilds (§13.4).
        if callback is not None and not self.is_loading:
            callback(*args)

    def _handle_project_selected(self, _index: int) -> None:
        """Forward a project combo selection."""
        id_project = str(self._project_combo_var.currentData() or "")
        if id_project:
            self._emit("project_selected", id_project)

    def _apply_filters(self) -> None:
        """Push the current tag and text filters into the table model."""
        if self.is_loading:
            return
        # Tag filters are OR-combined between themselves, then AND-combined
        # with the free text filter (spec B.4.2).
        filter_text = self._filter_bar_var.filter_text()
        self._model_var.apply_filters(self._filter_bar_var.active_tags(), filter_text)
        self._refresh_counts()
        self._filter_bar_var.set_filter_counter(self._model_var.visible_row_count() if filter_text else None)
        self._reset_search()

    def _refresh_counts(self) -> None:
        """Refresh the footer counters and the tag filter checkbox counts."""
        total = len(self._document) if self._document is not None else 0
        self._footer_var.set_counts(total, self._model_var.visible_row_count())
        self._filter_bar_var.set_tag_counts(self._model_var.tag_counts())

    def _submit_url(self) -> None:
        """Forward the URL submission (Enter key or button)."""
        url = self._url_edit_var.text().strip()
        if url:
            self._emit("url_submitted", url)

    def _focus_search(self) -> None:
        """Give the focus to the search field (Ctrl+F)."""
        self._filter_bar_var.focus_search()

    def _reset_search(self) -> None:
        """Recompute the search matches after a text or filter change."""
        self._search_nav_var.reset()

    def _navigate_search(self, delta: int) -> None:
        """Move to the next/previous search match (wraps around)."""
        self._search_nav_var.navigate(delta)

    def _handle_delete_clicked(self, view_row: int) -> None:
        """Forward a per-row 'X' click with its document row."""
        doc_row = self._model_var.doc_row_at(view_row)
        if doc_row >= 0:
            self._emit("row_delete_requested", doc_row)

    def _handle_sort_changed(self, _logical: int, _order: Qt.SortOrder) -> None:
        """Recompute search matches: column sort reorders `_view_rows`."""
        if not self.is_loading:
            self._reset_search()

    def _handle_cell_entered(self, index: QModelIndex) -> None:
        """Track the hovered row for the row-wide highlight."""
        self._delegate_var.set_hovered_row(index.row())
        self._table_var.viewport().update()

    def _handle_cell_clicked(self, index: QModelIndex) -> None:
        """Open the tag selector or activate a link on single click."""
        if not index.isValid() or self._document is None:
            return
        column_name = self._model_var.column_name_at(index.column())
        doc_row = self._model_var.doc_row_at(index.row())
        if doc_row < 0:
            return
        if column_name == C_COL_CUSTOM_TAGS:
            self._open_row_tag_editor(index, doc_row)
            return
        value = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        if is_link_value(value):
            self._emit("link_activated", value)

    def _open_row_tag_editor(self, index: QModelIndex, doc_row: int) -> None:
        """Open the shared tag composer next to the clicked cell, pre-filled with the row's tags."""
        rect = self._table_var.visualRect(index)
        anchor_pos = self._table_var.viewport().mapToGlobal(rect.bottomLeft())
        tags: frozenset[TagEnum] = self._document.tag_sets[doc_row] if self._document is not None else frozenset()
        open_row_tags(self, tags, lambda labels: self._handle_row_tags_result(doc_row, labels), anchor_pos)

    def _handle_row_tags_result(self, doc_row: int, labels: frozenset[str] | None) -> None:
        """Forward the tag composer result for one row, if confirmed."""
        if labels is not None:
            self._emit("row_tags_edited", doc_row, labels)

    def _open_column_manager(self) -> None:
        """Open the column manager dialog and forward the result."""
        if self._document is None:
            return
        current = [
            name
            for col in range(1, self._model_var.columnCount())
            if (name := self._model_var.column_name_at(col))
        ]
        result = ask_visible_columns(self, list(self._document.header), current, self._column_nicknames)
        if result is not None:
            visible_columns, nicknames = result
            self._emit("visible_columns_changed", visible_columns)
            self._emit("column_nicknames_changed", nicknames)


# EOF
