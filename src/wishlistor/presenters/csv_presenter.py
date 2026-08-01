"""CSV presenter: project switching, worker-based load/save, edits, undo (B.4)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import PurePath
from typing import cast

from wishlistor.interfaces.i_csv_service import ICsvService
from wishlistor.interfaces.i_csv_view import ICsvView
from wishlistor.interfaces.i_project_service import IProjectService
from wishlistor.interfaces.i_task_runner import ITaskRunner
from wishlistor.models.app_config_model import AppConfigModel
from wishlistor.models.app_state_model import AppStateModel
from wishlistor.models.csv_document_model import CsvDocumentModel
from wishlistor.models.project_model import ProjectModel
from wishlistor.presenters.csv_edit_flow import CsvEditFlowMixin
from wishlistor.shared import i18n_fra
from wishlistor.shared.constants_util import C_URL_HTTP_PREFIX, C_URL_HTTPS_PREFIX
from wishlistor.shared.enums.save_choice_enum import SaveChoiceEnum
from wishlistor.shared.enums.severity_enum import SeverityEnum
from wishlistor.shared.errors.csv_error import ErrorCodeCsv
from wishlistor.shared.operating_system_util import open_folder, open_url_in_browser
from wishlistor.shared.typing.datetime_util import (
    C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS,
    get_datetime_now_yyyy_mm_dd_hh_mm_ss,
)
from wishlistor.shared.validation_result import ValidationResult

_OWNER: str = "csv"
_PAYLOAD_SIZE: int = 2  # every worker payload is a (result, ValidationResult) pair


class CsvPresenter(CsvEditFlowMixin):
    """Wires the CSV view to the CSV and project services."""

    def __init__(
        self,
        view: ICsvView,
        csv_service: ICsvService,
        project_service: IProjectService,
        task_runner: ITaskRunner,
        config: AppConfigModel,
        app_state: AppStateModel,
        on_edit_project: Callable[[str], None],
    ) -> None:
        """Initialize the presenter.

        Args:
            view: The CSV view.
            csv_service: The CSV business logic.
            project_service: The project business logic.
            task_runner: Background executor for load and save.
            config: The shared configuration model.
            app_state: The global application state.
            on_edit_project: Called with a project id to open its edition form.
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._view = view
        self._csv_service = csv_service
        self._project_service = project_service
        self._task_runner = task_runner
        self._config = config
        self._app_state = app_state
        self._on_edit_project = on_edit_project
        self._project: ProjectModel | None = None
        self._document: CsvDocumentModel | None = None
        self._action_started: float = 0.0

    # -- wiring ----------------------------------------------------------------------

    def start(self) -> None:
        """Bind every view callback and show the initial state."""
        view = self._view
        view.bind_project_selected(self.open_project)
        view.bind_open_folder_clicked(self._handle_open_folder)
        view.bind_project_options_clicked(self._handle_project_options)
        view.bind_url_submitted(self._handle_url_submitted)
        view.bind_mass_tags_clicked(self._handle_mass_tags)
        view.bind_mass_comment_clicked(self._handle_mass_comment)
        view.bind_delete_rows_clicked(self._handle_delete_rows)
        view.bind_selection_changed(self._handle_selection_changed)
        view.bind_cell_edited(self._handle_cell_edited)
        view.bind_row_tags_edited(self._handle_row_tags_edited)
        view.bind_link_activated(self._handle_link_activated)
        view.bind_save_clicked(self._handle_save)
        view.bind_undo(self._handle_undo)
        view.bind_redo(self._handle_redo)
        view.bind_shortcut_tags(self._handle_shortcut_tags)
        view.bind_visible_columns_changed(self._handle_visible_columns_changed)
        view.bind_column_nicknames_changed(self._handle_column_nicknames_changed)
        view.bind_column_widths_changed(self._handle_column_widths_changed)
        view.bind_sort_order_changed(self._handle_sort_order_changed)
        view.bind_row_delete_requested(self._handle_row_delete_requested)
        self.refresh_projects()
        view.show_no_project(i18n_fra.CSV_NO_PROJECT)

    def refresh_projects(self) -> None:
        """Reload the project combo (recency first)."""
        entries: list[tuple[str, str]] = []
        for project in self._config.projects:
            label = f"{project.name} — {project.website} — {project.category} — {project.csv_path}"
            entries.append((project.id_project, label))
        current = self._project.id_project if self._project is not None else ""
        self._view.set_projects(entries, current)

    # -- project opening ----------------------------------------------------------------

    def open_project(self, id_project: str, check_unsaved: bool = True) -> None:
        """Open a project: unsaved-changes guard, then background load.

        Args:
            id_project: The project to open.
            check_unsaved: False when the guard already ran (project creation).
        """
        if self._project is not None and id_project == self._project.id_project:
            return
        if check_unsaved and not self._resolve_unsaved_changes():
            self.refresh_projects()  # revert the combo selection
            return
        project = self._project_service.get_project(id_project)
        if project is None:
            return
        self._action_started = time.perf_counter()
        self._set_busy(True)
        self._csv_service.reset_history(self._config.options.undo_max)
        self._task_runner.run(
            lambda: self._csv_service.load(project),
            lambda payload: self._on_loaded(project, payload),
            self._on_task_failed,
        )

    def _on_loaded(self, project: ProjectModel, payload: object) -> None:
        """Install a freshly loaded document (UI thread)."""
        self._set_busy(False)
        document, result = _as_load_payload(payload)
        self._view.clear_banner()
        self._view.append_banner_issues(result)
        if document is None:
            self._on_load_failed(project, result)
            return
        self._project = project
        self._document = document
        self._project_service.mark_opened(project.id_project)
        self.refresh_projects()
        columns = project.column_order or project.visible_columns
        self._view.show_document(document, list(columns), project.row_height)
        self._view.set_column_nicknames(project.column_nicknames)
        if project.column_widths:
            self._view.apply_column_widths(project.column_widths)
        else:
            self._view.auto_size_columns()  # first open only, never over user settings
        self._view.apply_sort_order(project.sort_column, project.sort_descending)
        self._view.set_file_mtime_label(_mtime_label(document))
        self._view.set_save_enabled(False)
        self._view.set_last_save_label(i18n_fra.COMMON_EMPTY_VALUE)
        elapsed_ms = round((time.perf_counter() - self._action_started) * 1000)
        self._logger.info("Action 'charger le CSV' terminée en %s ms", elapsed_ms)

    def _on_load_failed(self, project: ProjectModel, result: ValidationResult) -> None:
        """Report a load failure and send the user to fix the project options."""
        self._view.show_critical(i18n_fra.CSV_CRITICAL_TITLE, result.concat_issues_by_severity(5))
        self._view.show_no_project(i18n_fra.CSV_NO_PROJECT)
        self._project = None
        self._document = None
        self._on_edit_project(project.id_project)

    def _on_task_failed(self, excp: Exception) -> None:
        """Report an unexpected worker failure (UI thread)."""
        self._set_busy(False)
        self._logger.error("Échec inattendu d'une tâche CSV : %s", excp)
        self._view.show_critical(i18n_fra.CSV_CRITICAL_TITLE, str(ErrorCodeCsv.CSV_9999.value))

    # -- saving -----------------------------------------------------------------------------

    def _handle_save(self) -> None:
        """Save the document in a worker (Ctrl+S or button)."""
        document = self._document
        if document is None or not document.is_dirty:
            return
        self._action_started = time.perf_counter()
        self._set_busy(True)
        self._task_runner.run(
            lambda: self._csv_service.save(document, False), self._on_save_result, self._on_task_failed
        )

    def _on_save_result(self, payload: object) -> None:
        """Handle a save outcome: success, external conflict, or write failure."""
        self._set_busy(False)
        saved, result = _as_save_payload(payload)
        if saved:
            self._after_save_success()
            return
        if result.count_severities_by_code(ErrorCodeCsv.CSV_1012) > 0:
            self._resolve_save_conflict()
        else:
            self._view.append_banner_issues(result)
            self._save_as_flow()

    def _resolve_save_conflict(self) -> None:
        """Ask the user what to do about an external modification (D.5)."""
        document = self._document
        if document is None:
            return
        choice = self._view.ask_conflict_choice()
        if choice is SaveChoiceEnum.E_OVERWRITE:
            self._set_busy(True)
            self._task_runner.run(
                lambda: self._csv_service.save(document, True), self._on_save_result, self._on_task_failed
            )
        elif choice is SaveChoiceEnum.E_SAVE_AS:
            self._save_as_flow()

    def _save_as_flow(self) -> None:
        """Save under a new location chosen through the native dialog."""
        document = self._document
        project = self._project
        if document is None or project is None:
            return
        new_path = self._view.ask_save_as_path(document.csv_path)
        if not new_path:
            return
        result = self._csv_service.save_as(document, new_path)
        if result.has_errors_or_fatals():
            self._view.append_banner_issues(result)
            return
        self._project_service.update_csv_path(project.id_project, new_path)
        self.refresh_projects()
        self._after_save_success()

    def _after_save_success(self) -> None:
        """Refresh the footer after a successful save."""
        document = self._document
        if document is None:
            return
        self._view.set_save_enabled(False)
        self._view.set_last_save_label(get_datetime_now_yyyy_mm_dd_hh_mm_ss())
        self._view.set_file_mtime_label(_mtime_label(document))
        elapsed_ms = round((time.perf_counter() - self._action_started) * 1000)
        self._logger.info("Action 'sauvegarder le CSV' terminée en %s ms", elapsed_ms)

    def _save_blocking(self) -> bool:
        """Synchronous save used by the close/switch guard; True when saved."""
        document = self._document
        if document is None:
            return True
        saved, result = self._csv_service.save(document, False)
        if saved:
            self._after_save_success()
            return True
        if result.count_severities_by_code(ErrorCodeCsv.CSV_1012) > 0:
            choice = self._view.ask_conflict_choice()
            if choice is SaveChoiceEnum.E_OVERWRITE:
                saved, _result = self._csv_service.save(document, True)
                return saved
            if choice is SaveChoiceEnum.E_SAVE_AS:
                return self._save_as_blocking()
            return False
        self._view.append_banner_issues(result)
        return False

    def _save_as_blocking(self) -> bool:
        """Synchronous 'save as' for the close/switch guard; True when saved."""
        document = self._document
        project = self._project
        if document is None or project is None:
            return True
        new_path = self._view.ask_save_as_path(document.csv_path)
        if not new_path:
            return False
        result = self._csv_service.save_as(document, new_path)
        if result.has_errors_or_fatals():
            self._view.append_banner_issues(result)
            return False
        self._project_service.update_csv_path(project.id_project, new_path)
        return True

    def can_close(self) -> bool:
        """Data-loss guard shared by the window close and project switch (spec F)."""
        return self._resolve_unsaved_changes()

    def _resolve_unsaved_changes(self) -> bool:
        """Ask about unsaved changes; True when the caller may proceed."""
        document = self._document
        if document is None or not document.is_dirty:
            return True
        choice = self._view.ask_unsaved_choice()
        if choice is SaveChoiceEnum.E_SAVE:
            return self._save_blocking()
        if choice is SaveChoiceEnum.E_SAVE_AS:
            return self._save_as_blocking()
        return choice is SaveChoiceEnum.E_DISCARD

    # -- edits ------------------------------------------------------------------------------
    # See csv_edit_flow.CsvEditFlowMixin for URL add, cell/tag edits, mass actions,
    # delete rows and undo/redo (extracted from this file, see MIR121 in AGENTS.md).

    # -- navigation and display ---------------------------------------------------------------

    def _handle_selection_changed(self, count: int) -> None:
        """Enable the mass actions when at least one row is checked."""
        self._view.set_mass_actions_enabled(count > 0)

    def _handle_open_folder(self) -> None:
        """Open the parent folder of the current CSV in the file explorer."""
        project = self._project
        if project is None:
            return
        try:
            open_folder(str(PurePath(project.csv_path).parent))
        except Exception:
            self._logger.exception("Impossible d'ouvrir le dossier du CSV.")
            self._notify_folder_error(str(PurePath(project.csv_path).parent))

    def _handle_link_activated(self, value: str) -> None:
        """Open a clicked URL in the browser, or a drive path in the explorer."""
        if value.startswith((C_URL_HTTP_PREFIX, C_URL_HTTPS_PREFIX)):
            open_url_in_browser(value)
            return
        try:
            # "file://", "E://", ...  # ruff:ignore[commented-out-code]
            open_folder(value)
        except Exception:
            self._logger.exception("Impossible d'ouvrir le dossier '%s'.", value)
            self._notify_folder_error(value)

    def _notify_folder_error(self, path: str) -> None:
        """Report an unreachable folder in the inline banner."""
        result = ValidationResult()
        result.append(ErrorCodeCsv.CSV_1018, SeverityEnum.E_ERROR, {"path": path})
        self._view.append_banner_issues(result)

    def _handle_project_options(self) -> None:
        """Open the project edition form (module Projet)."""
        if self._project is not None:
            self._on_edit_project(self._project.id_project)

    def _handle_visible_columns_changed(self, columns: list[str]) -> None:
        """Persist and apply a new visible-column order."""
        project = self._project
        if project is None:
            return
        self._project_service.update_display_columns(project.id_project, columns)
        self._view.set_visible_columns(columns)
        if project.column_widths:
            self._view.apply_column_widths(project.column_widths)
        self._view.apply_sort_order(project.sort_column, project.sort_descending)

    def _handle_column_nicknames_changed(self, nicknames: dict[str, str]) -> None:
        """Persist and apply new column nicknames from 'Gestion des colonnes'."""
        project = self._project
        if project is None:
            return
        project.column_nicknames = dict(nicknames)
        self._project_service.update_column_nicknames(project.id_project, nicknames)
        self._view.set_column_nicknames(nicknames)

    def _handle_column_widths_changed(self, widths: dict[str, int]) -> None:
        """Persist the user-resized column widths."""
        project = self._project
        if project is None:
            return
        project.column_widths = {**project.column_widths, **widths}
        self._project_service.update_column_widths(project.id_project, widths)

    def _handle_sort_order_changed(self, column: str, descending: bool) -> None:
        """Persist the user-applied sort order."""
        project = self._project
        if project is None:
            return
        project.sort_column = column
        project.sort_descending = descending
        self._project_service.update_sort_order(project.id_project, column, descending)

    # -- cross-module hooks ----------------------------------------------------------------------

    def refresh_project_settings(self, id_project: str) -> None:
        """Re-apply mapping, weights and display after 'Options du projet'.

        Args:
            id_project: The edited project.
        """
        project = self._project
        document = self._document
        if project is None or document is None or project.id_project != id_project:
            # Not the currently open document (e.g. the previous load had failed): (re)load it.
            self.open_project(id_project)
            return
        updated = self._project_service.get_project(id_project)
        if updated is None:
            return
        self._project = updated
        document.set_search_columns(updated.search_index_columns)
        result = self._csv_service.recompute_ranks(document, updated)
        self._view.append_banner_issues(result)
        self._view.set_visible_columns(list(updated.column_order or updated.visible_columns))
        self._view.set_column_nicknames(updated.column_nicknames)
        self._view.set_row_height(updated.row_height)
        self._view.refresh_table()
        self.refresh_projects()

    def preview_row_height(self, row_height: int) -> None:
        """Apply the row height live while the form spin changes.

        Args:
            row_height: Row height in pixels.
        """
        self._view.set_row_height(row_height)

    def handle_factory_reset(self) -> None:
        """Drop the current document after a configuration reset."""
        self._project = None
        self._document = None
        self._csv_service.reset_history(self._config.options.undo_max)
        self._view.clear()
        self.refresh_projects()
        self._view.show_no_project(i18n_fra.CSV_NO_PROJECT)

    # -- helpers -------------------------------------------------------------------------------------

    def _set_busy(self, busy: bool) -> None:
        """Toggle the overlay and the global busy flag."""
        self._view.set_busy(busy)
        self._app_state.set_busy(_OWNER, busy)


def _as_load_payload(payload: object) -> tuple[CsvDocumentModel | None, ValidationResult]:
    """Narrow the worker payload of a load task."""
    if isinstance(payload, tuple) and len(payload) == _PAYLOAD_SIZE:
        pair = cast("tuple[object, object]", payload)
        document = pair[0]
        result = pair[1]
        if isinstance(result, ValidationResult) and (document is None or isinstance(document, CsvDocumentModel)):
            return document, result
    return None, ValidationResult()


def _as_save_payload(payload: object) -> tuple[bool, ValidationResult]:
    """Narrow the worker payload of a save task."""
    if isinstance(payload, tuple) and len(payload) == _PAYLOAD_SIZE:
        pair = cast("tuple[object, object]", payload)
        saved = pair[0]
        result = pair[1]
        if isinstance(saved, bool) and isinstance(result, ValidationResult):
            return saved, result
    return False, ValidationResult()


def _mtime_label(document: CsvDocumentModel) -> str:
    """Format the on-disk mtime label of the footer."""
    stamp = datetime.fromtimestamp(document.mtime).strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS)
    return i18n_fra.CSV_FILE_MTIME.format(mtime=stamp)


# EOF
