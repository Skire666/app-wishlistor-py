"""Project presenter: history list and creation/edition form flow (B.3)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from wishlistor.interfaces.i_project_service import IProjectService
from wishlistor.interfaces.i_project_view import IProjectView
from wishlistor.shared import i18n_fra
from wishlistor.shared.validation_result import ValidationResult


class ProjectPresenter:
    """Wires the project view to the project service."""

    def __init__(
        self,
        view: IProjectView,
        project_service: IProjectService,
        on_open_project: Callable[[str], None],
        on_project_updated: Callable[[str], None],
        on_row_height_preview: Callable[[int], None],
        on_edit_cancelled: Callable[[], None],
        can_leave_csv: Callable[[], bool],
        on_open_created: Callable[[str], None],
    ) -> None:
        """Initialize the presenter.

        Args:
            view: The project view.
            project_service: The project business logic.
            on_open_project: Called with a project id to open it in the CSV module.
            on_project_updated: Called after an existing project was edited.
            on_row_height_preview: Called live while the row height spin changes.
            on_edit_cancelled: Called when an edition (Options du projet) is cancelled.
            can_leave_csv: Unsaved-changes guard; False keeps the current CSV.
            on_open_created: Opens a freshly created project (guard already ran).
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._view = view
        self._project_service = project_service
        self._on_open_project = on_open_project
        self._on_project_updated = on_project_updated
        self._on_row_height_preview = on_row_height_preview
        self._on_edit_cancelled = on_edit_cancelled
        self._can_leave_csv = can_leave_csv
        self._on_open_created = on_open_created
        self._editing_id: str = ""  # empty while creating a new project

    def start(self) -> None:
        """Bind the view callbacks and show the history."""
        self._view.bind_create_clicked(self._handle_create_clicked)
        self._view.bind_project_clicked(self._handle_project_clicked)
        self._view.bind_project_deleted(self._handle_project_deleted)
        self._view.bind_form_submitted(self._handle_form_submitted)
        self._view.bind_form_cancelled(self._handle_form_cancelled)
        self._view.bind_csv_path_edited(self._handle_csv_path_edited)
        self._view.bind_form_edited(self._handle_form_edited)
        self._view.bind_row_height_changed(self._handle_row_height_changed)
        self._view.bind_column_widths_changed(self._handle_column_widths_changed)
        self._view.apply_column_widths(self._project_service.project_table_column_widths())
        self.refresh_list()

    def refresh_list(self) -> None:
        """Reload the history table."""
        self._view.show_rows(self._project_service.list_rows())
        self._view.show_list()

    def open_edit_form(self, id_project: str) -> None:
        """Open the form pre-filled with an existing project (Options du projet).

        Args:
            id_project: The project to edit.
        """
        project = self._project_service.get_project(id_project)
        if project is None:
            return
        self._editing_id = id_project
        headers, _result = self._project_service.read_headers(project.csv_path)
        self._view.show_form(self._project_service.form_state_of(project), headers, True)
        self._validate_form_now()

    # -- handlers -------------------------------------------------------------------

    def _handle_create_clicked(self) -> None:
        """Guard the open CSV, then replace the history with a pristine form."""
        started = time.perf_counter()
        if not self._can_leave_csv():
            self._logger.info("Création de projet annulée : modifications CSV non résolues.")
            return
        self._editing_id = ""
        self._view.show_form(self._project_service.default_form_state(), [], False)
        self._validate_form_now()
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'créer un projet' (ouverture du formulaire) terminée en %s ms", elapsed_ms)

    def _handle_project_clicked(self, id_project: str) -> None:
        """Open the clicked project in the CSV module."""
        started = time.perf_counter()
        self._on_open_project(id_project)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'ouvrir le projet %s' terminée en %s ms", id_project, elapsed_ms)

    def _handle_project_deleted(self, id_project: str) -> None:
        """Remove a project from the history ('Effacer'), after a modal confirmation."""
        project = self._project_service.get_project(id_project)
        name = project.name if project is not None else ""
        message = i18n_fra.PROJECT_DELETE_CONFIRM_MESSAGE.format(name=name)
        if not self._view.confirm(i18n_fra.PROJECT_DELETE_CONFIRM_TITLE, message):
            return
        started = time.perf_counter()
        try:
            self._project_service.delete_project(id_project)
            self.refresh_list()
        except Exception:
            self._logger.exception("Échec de la suppression du projet %s.", id_project)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'effacer le projet' terminée en %s ms", elapsed_ms)

    def _handle_csv_path_edited(self, csv_path: str) -> None:
        """Refresh the column pickers from the typed CSV path."""
        headers, result = self._project_service.read_headers(csv_path)
        self._view.set_form_columns(headers)
        if result.has_errors_or_fatals():
            self._view.show_field_errors({"csv_path": result.concat_issues_by_severity(1)})

    def _handle_form_edited(self) -> None:
        """Real-time, field-by-field validation feedback."""
        self._validate_form_now()

    def _validate_form_now(self) -> None:
        """Validate the form as it stands and show the resulting field errors."""
        _result, field_errors = self._project_service.validate_form(self._view.snapshot())
        self._view.show_field_errors(field_errors)

    def _handle_column_widths_changed(self, widths: dict[str, int]) -> None:
        """Persist the user-resized column widths of the history table."""
        self._project_service.update_project_table_column_widths(widths)

    def _handle_row_height_changed(self, row_height: int) -> None:
        """Apply the row height live on the CSV table (edition mode only)."""
        if self._editing_id:
            self._on_row_height_preview(row_height)

    def _handle_form_submitted(self) -> None:
        """Validate then create or update the project."""
        started = time.perf_counter()
        try:
            self._submit_form()
        except Exception:
            self._logger.exception("Échec de l'enregistrement du projet.")
            self._view.notify_error(ValidationResult())
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'enregistrer le projet' terminée en %s ms", elapsed_ms)

    def _submit_form(self) -> None:
        """Create or update the project from the validated form."""
        state = self._view.snapshot()
        result, field_errors = self._project_service.validate_form(state)
        self._view.show_field_errors(field_errors)
        if result.has_errors_or_fatals():
            return
        if self._editing_id:
            updated = self._project_service.update_project(self._editing_id, state)
            self.refresh_list()
            if updated is not None:
                self._on_project_updated(self._editing_id)
        else:
            project = self._project_service.create_project(state)
            self.refresh_list()
            self._on_open_created(project.id_project)  # the unsaved guard already ran
        if result.has_warnings():
            self._view.notify_error(result)  # e.g. no column default value configured (spec §5)

    def _handle_form_cancelled(self) -> None:
        """Return to the history (or to the CSV module when editing) without saving."""
        was_editing = bool(self._editing_id)
        self._editing_id = ""
        self._view.show_list()
        if was_editing:
            self._on_edit_cancelled()


# EOF
