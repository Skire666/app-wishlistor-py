"""Project management: listing, form validation, creation, edition, deletion."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import uuid

from wishlistor.interfaces.i_config_repository import IConfigRepository
from wishlistor.interfaces.i_csv_repository import ICsvRepository
from wishlistor.models.app_config_model import AppConfigModel
from wishlistor.models.project_model import ProjectModel
from wishlistor.models.view_state_model import ProjectFormState, ProjectRowState
from wishlistor.shared.constants_util import C_ROW_HEIGHT_DEFAULT
from wishlistor.shared.enums.default_value_enum import DefaultValueEnum
from wishlistor.shared.enums.severity_enum import SeverityEnum
from wishlistor.shared.errors.csv_error import ErrorCodeCsv
from wishlistor.shared.errors.project_error import ErrorCodeProject
from wishlistor.shared.exceptions.csv_structure_error import CsvStructureError
from wishlistor.shared.exceptions.file_access_error import FileAccessError
from wishlistor.shared.i18n_fra import COMMON_EMPTY_VALUE
from wishlistor.shared.typing.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from wishlistor.shared.validation_result import ValidationResult

_SIZE_UNITS: tuple[str, ...] = ("o", "Ko", "Mo", "Go", "To")
_SIZE_STEP: float = 1024.0

# Maps project error codes to the form field carrying the inline feedback.
_FIELD_BY_CODE: dict[ErrorCodeProject, str] = {
    ErrorCodeProject.PRJ_1001: "csv_path",
    ErrorCodeProject.PRJ_1002: "name",
    ErrorCodeProject.PRJ_1003: "website",
    ErrorCodeProject.PRJ_1004: "category",
    ErrorCodeProject.PRJ_1005: "row_height",
    ErrorCodeProject.PRJ_1006: "primary_column",
    ErrorCodeProject.PRJ_1007: "search_index_columns",
    ErrorCodeProject.PRJ_1008: "visible_columns",
    ErrorCodeProject.PRJ_1009: "tag_weights",
    ErrorCodeProject.PRJ_1011: "released_column",
    ErrorCodeProject.PRJ_1012: "popularity_column",
    ErrorCodeProject.PRJ_1013: "scoring_column",
    ErrorCodeProject.PRJ_1014: "column_default_values",
    ErrorCodeProject.PRJ_1015: "column_default_values",
}


def _format_size(size_bytes: int) -> str:
    """Format a byte count into a human readable label with its unit."""
    value = float(size_bytes)
    for unit in _SIZE_UNITS:
        if value < _SIZE_STEP or unit == _SIZE_UNITS[-1]:
            if unit == "o":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= _SIZE_STEP
    return f"{int(value)} o"


class ProjectService:
    """Manages the project history and the creation/edition form logic."""

    def __init__(
        self, config_repository: IConfigRepository, csv_repository: ICsvRepository, config: AppConfigModel
    ) -> None:
        """Initialize the service.

        Args:
            config_repository: Configuration persistence.
            csv_repository: CSV metadata access (existence, size, header).
            config: The shared configuration model.
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config_repository = config_repository
        self._csv_repository = csv_repository
        self._config = config

    @staticmethod
    def generate_id() -> str:
        """Return a new unique project identifier."""
        return str(uuid.uuid4())

    # -- listing --------------------------------------------------------------------

    def list_rows(self) -> list[ProjectRowState]:
        """Return the project history rows, most recently opened first."""
        rows: list[ProjectRowState] = []
        for project in self._config.projects:
            stats = self._csv_repository.file_stats(project.csv_path)
            rows.append(
                ProjectRowState(
                    id_project=project.id_project,
                    name=project.name,
                    website=project.website,
                    category=project.category,
                    csv_path=project.csv_path,
                    last_opened=project.last_opened or COMMON_EMPTY_VALUE,
                    file_size_bytes=stats[1] if stats else -1,
                    file_size_label=_format_size(stats[1]) if stats else COMMON_EMPTY_VALUE,
                    is_available=stats is not None,
                )
            )
        return rows

    def get_project(self, id_project: str) -> ProjectModel | None:
        """Return a project by id, or None.

        Args:
            id_project: The project identifier.
        """
        return self._config.projects.read(id_project)

    # -- form -----------------------------------------------------------------------

    def default_form_state(self) -> ProjectFormState:
        """Return a pristine form state pre-filled with the default options."""
        options = self._config.options
        special = tuple(options.special_display_columns)
        return ProjectFormState(
            created_at=get_datetime_now_yyyy_mm_dd_hh_mm_ss(),
            row_height=C_ROW_HEIGHT_DEFAULT,
            tag_weights=dict(options.default_tag_weights),
            primary_column="",
            search_index_columns=special,
            visible_columns=special,
            column_default_values=(
                ("csv.index", DefaultValueEnum.E_TOTAL_ROW_COUNT.value),
                ("csv.best_extractor", DefaultValueEnum.E_EXTRACTOR_E0.value),
            ),
        )

    def form_state_of(self, project: ProjectModel) -> ProjectFormState:
        """Return the form state matching an existing project.

        Args:
            project: The project to edit.
        """
        return ProjectFormState(
            csv_path=project.csv_path,
            name=project.name,
            website=project.website,
            category=project.category,
            created_at=project.created_at,
            row_height=project.row_height,
            tag_weights=dict(project.tag_weights),
            primary_column=project.primary_column,
            released_column=project.released_column,
            popularity_column=project.popularity_column,
            scoring_column=project.scoring_column,
            search_index_columns=tuple(project.search_index_columns),
            visible_columns=tuple(project.column_order or project.visible_columns),
            column_nicknames=dict(project.column_nicknames),
            column_default_values=tuple(project.column_default_values),
        )

    def read_headers(self, csv_path: str) -> tuple[list[str], ValidationResult]:
        """Read the CSV header for the mapping pickers.

        Args:
            csv_path: Path typed in the form.

        Returns:
            The column names (empty on failure) and the issues met.
        """
        result = ValidationResult()
        if not self._csv_repository.file_exists(csv_path):
            result.append(ErrorCodeCsv.CSV_1001, SeverityEnum.E_ERROR, {"path": csv_path})
            return [], result
        try:
            header = self._csv_repository.read_header(csv_path)
        except FileAccessError, CsvStructureError:
            result.append(ErrorCodeCsv.CSV_1001, SeverityEnum.E_ERROR, {"path": csv_path})
            return [], result
        if not any(name.strip() for name in header):
            result.append(ErrorCodeCsv.CSV_1002, SeverityEnum.E_ERROR)
            return [], result
        return header, result

    def validate_form(self, state: ProjectFormState) -> tuple[ValidationResult, dict[str, str]]:
        """Validate the form, field by field.

        Args:
            state: Snapshot of the form.

        Returns:
            The full validation result and a field-name to message mapping.
        """
        candidate = self._model_from_state(ProjectModel(), state)
        result = candidate.validate()
        if state.csv_path.strip() and not self._csv_repository.file_exists(state.csv_path):
            result.append(ErrorCodeProject.PRJ_1001, SeverityEnum.E_ERROR)
        field_errors: dict[str, str] = {}
        for issue in result.issues:
            code = issue.code
            if isinstance(code, ErrorCodeProject):
                field = _FIELD_BY_CODE.get(code, "")
                if field and field not in field_errors:
                    field_errors[field] = issue.message
        return result, field_errors

    # -- persistence ------------------------------------------------------------------

    def create_project(self, state: ProjectFormState) -> ProjectModel:
        """Create and persist a new project from a valid form state.

        Args:
            state: Validated snapshot of the form.

        Returns:
            The created project.
        """
        project = ProjectModel.get_default()
        project.id_project = self.generate_id()
        self._model_from_state(project, state)
        self._config.projects.create(project)
        self._config_repository.save(self._config)
        self._logger.info("Projet créé : %s (%s)", project.name, project.id_project)
        return project

    def update_project(self, id_project: str, state: ProjectFormState) -> ProjectModel | None:
        """Update and persist an existing project from a valid form state.

        Args:
            id_project: The project identifier.
            state: Validated snapshot of the form.

        Returns:
            The updated project, or None when the id is unknown.
        """
        project = self._config.projects.read(id_project)
        if project is None:
            return None
        self._model_from_state(project, state)
        project.mark_as_modified()
        self._config.projects.update(project)
        self._config_repository.save(self._config)
        self._logger.info("Projet modifié : %s (%s)", project.name, id_project)
        return project

    def update_display_columns(self, id_project: str, columns: list[str]) -> None:
        """Persist a new visible-column set and order for a project.

        Args:
            id_project: The project identifier.
            columns: Visible column names, in display order.
        """
        project = self._config.projects.read(id_project)
        if project is None:
            return
        project.visible_columns = list(columns)
        project.column_order = list(columns)
        project.mark_as_modified()
        self._config.projects.update(project)
        self._config_repository.save(self._config)

    def update_column_widths(self, id_project: str, widths: dict[str, int]) -> None:
        """Persist the user-resized column widths of a project.

        Args:
            id_project: The project identifier.
            widths: Column name to width (pixels) mapping.
        """
        project = self._config.projects.read(id_project)
        if project is None:
            return
        project.column_widths = {**project.column_widths, **widths}
        project.mark_as_modified()
        self._config.projects.update(project)
        self._config_repository.save(self._config)

    def update_column_nicknames(self, id_project: str, nicknames: dict[str, str]) -> None:
        """Persist the column nickname mapping of a project ('Gestion des colonnes').

        Args:
            id_project: The project identifier.
            nicknames: Column name to display nickname mapping (full replacement).
        """
        project = self._config.projects.read(id_project)
        if project is None:
            return
        project.column_nicknames = dict(nicknames)
        project.mark_as_modified()
        self._config.projects.update(project)
        self._config_repository.save(self._config)

    def update_sort_order(self, id_project: str, column: str, descending: bool) -> None:
        """Persist the last user-applied sort order of a project's table.

        Args:
            id_project: The project identifier.
            column: Sorted column name (empty for the natural row order).
            descending: True when the sort is descending.
        """
        project = self._config.projects.read(id_project)
        if project is None:
            return
        project.sort_column = column
        project.sort_descending = descending
        project.mark_as_modified()
        self._config.projects.update(project)
        self._config_repository.save(self._config)

    def project_table_column_widths(self) -> dict[str, int]:
        """Return the persisted column widths of the project history table."""
        return self._config.project_table_column_widths

    def update_project_table_column_widths(self, widths: dict[str, int]) -> None:
        """Persist the user-resized column widths of the project history table.

        Args:
            widths: Column key to width (pixels) mapping.
        """
        self._config.project_table_column_widths = {**self._config.project_table_column_widths, **widths}
        self._config_repository.save(self._config)

    def update_csv_path(self, id_project: str, new_path: str) -> None:
        """Update the CSV path of a project (after 'Enregistrer sous…').

        Args:
            id_project: The project identifier.
            new_path: The new CSV location.
        """
        project = self._config.projects.read(id_project)
        if project is None:
            return
        project.csv_path = new_path
        project.mark_as_modified()
        self._config.projects.update(project)
        self._config_repository.save(self._config)

    def delete_project(self, id_project: str) -> None:
        """Remove a project from the history and persist the change.

        Args:
            id_project: The project identifier.
        """
        self._config.projects.delete(id_project)
        self._config_repository.save(self._config)
        self._logger.info("Projet retiré de la liste : %s", id_project)

    def mark_opened(self, id_project: str) -> None:
        """Stamp a project as just opened and persist the change.

        Args:
            id_project: The project identifier.
        """
        self._config.projects.touch(id_project)
        self._config_repository.save(self._config)

    @staticmethod
    def _model_from_state(project: ProjectModel, state: ProjectFormState) -> ProjectModel:
        """Copy the form state into a project model (identity untouched)."""
        project.csv_path = state.csv_path.strip()
        project.name = state.name.strip()
        project.website = state.website.strip()
        project.category = state.category.strip()
        project.row_height = state.row_height
        project.tag_weights = dict(state.tag_weights)
        project.primary_column = state.primary_column
        project.released_column = state.released_column
        project.popularity_column = state.popularity_column
        project.scoring_column = state.scoring_column
        project.search_index_columns = list(state.search_index_columns)
        project.visible_columns = list(state.visible_columns)
        project.column_order = list(state.visible_columns)
        project.column_nicknames = dict(state.column_nicknames)
        project.column_default_values = list(state.column_default_values)
        return project


# EOF
