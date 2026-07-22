# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol

from wishlistor.models.project_model import ProjectModel
from wishlistor.models.view_state_model import ProjectFormState, ProjectRowState
from wishlistor.shared.validation_result import ValidationResult


class IProjectService(Protocol):
    """Project management: listing, validation, creation, edition, deletion."""

    def generate_id(self) -> str:
        """Return a new unique project identifier."""
        ...

    def list_rows(self) -> list[ProjectRowState]:
        """Return the project history rows, most recently opened first."""
        ...

    def get_project(self, id_project: str) -> ProjectModel | None:
        """Return a project by id, or None.

        Args:
            id_project: The project identifier.
        """
        ...

    def default_form_state(self) -> ProjectFormState:
        """Return a pristine form state pre-filled with the default options."""
        ...

    def form_state_of(self, project: ProjectModel) -> ProjectFormState:
        """Return the form state matching an existing project.

        Args:
            project: The project to edit.
        """
        ...

    def read_headers(self, csv_path: str) -> tuple[list[str], ValidationResult]:
        """Read the CSV header for the mapping pickers.

        Args:
            csv_path: Path typed in the form.

        Returns:
            The column names (empty on failure) and the issues met.
        """
        ...

    def validate_form(self, state: ProjectFormState) -> tuple[ValidationResult, dict[str, str]]:
        """Validate the form, field by field.

        Args:
            state: Snapshot of the form.

        Returns:
            The full validation result and a field-name to message mapping
            for inline display.
        """
        ...

    def create_project(self, state: ProjectFormState) -> ProjectModel:
        """Create and persist a new project from a valid form state.

        Args:
            state: Validated snapshot of the form.

        Returns:
            The created project.
        """
        ...

    def update_project(self, id_project: str, state: ProjectFormState) -> ProjectModel | None:
        """Update and persist an existing project from a valid form state.

        Args:
            id_project: The project identifier.
            state: Validated snapshot of the form.

        Returns:
            The updated project, or None when the id is unknown.
        """
        ...

    def update_column_widths(self, id_project: str, widths: dict[str, int]) -> None:
        """Persist the user-resized column widths of a project.

        Args:
            id_project: The project identifier.
            widths: Column name to width (pixels) mapping.
        """
        ...

    def update_display_columns(self, id_project: str, columns: list[str]) -> None:
        """Persist a new visible-column set and order for a project.

        Args:
            id_project: The project identifier.
            columns: Visible column names, in display order.
        """
        ...

    def update_column_nicknames(self, id_project: str, nicknames: dict[str, str]) -> None:
        """Persist the column nickname mapping of a project ('Gestion des colonnes').

        Args:
            id_project: The project identifier.
            nicknames: Column name to display nickname mapping (full replacement).
        """
        ...

    def update_sort_order(self, id_project: str, column: str, descending: bool) -> None:
        """Persist the last user-applied sort order of a project's table.

        Args:
            id_project: The project identifier.
            column: Sorted column name (empty for the natural row order).
            descending: True when the sort is descending.
        """
        ...

    def project_table_column_widths(self) -> dict[str, int]:
        """Return the persisted column widths of the project history table."""
        ...

    def update_project_table_column_widths(self, widths: dict[str, int]) -> None:
        """Persist the user-resized column widths of the project history table.

        Args:
            widths: Column key to width (pixels) mapping.
        """
        ...

    def update_csv_path(self, id_project: str, new_path: str) -> None:
        """Update the CSV path of a project (after 'Enregistrer sous…').

        Args:
            id_project: The project identifier.
            new_path: The new CSV location.
        """
        ...

    def delete_project(self, id_project: str) -> None:
        """Remove a project from the history and persist the change.

        Args:
            id_project: The project identifier.
        """
        ...

    def mark_opened(self, id_project: str) -> None:
        """Stamp a project as just opened and persist the change.

        Args:
            id_project: The project identifier.
        """
        ...


# EOF
