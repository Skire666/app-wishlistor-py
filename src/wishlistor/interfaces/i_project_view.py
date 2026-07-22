# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from wishlistor.interfaces.i_base_view import IBaseView
from wishlistor.models.view_state_model import ProjectFormState, ProjectRowState


class IProjectView(IBaseView, Protocol):
    """Project module: history table and inline creation/edition form."""

    def snapshot(self) -> ProjectFormState:
        """Return the current content of the project form."""
        ...

    def show_rows(self, rows: list[ProjectRowState]) -> None:
        """Display the project history table.

        Args:
            rows: Rows to display, most recently opened first.
        """
        ...

    def show_list(self) -> None:
        """Switch back to the history panel."""
        ...

    def show_form(self, state: ProjectFormState, headers: list[str], is_edit: bool) -> None:
        """Replace the history panel with the inline form.

        Args:
            state: Initial form values.
            headers: CSV columns available for the mapping pickers.
            is_edit: True when editing an existing project.
        """
        ...

    def set_form_columns(self, headers: list[str]) -> None:
        """Refresh the column pickers after the CSV path changed.

        Args:
            headers: CSV columns (special columns are appended by the view).
        """
        ...

    def show_field_errors(self, errors: dict[str, str]) -> None:
        """Show inline, per-field validation feedback.

        Args:
            errors: Field name to French message mapping (empty clears all).
        """
        ...

    def bind_create_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Créer un projet' button callback."""
        ...

    def bind_project_clicked(self, callback: Callable[[str], None]) -> None:
        """Register the history row click callback (opens the project)."""
        ...

    def bind_project_deleted(self, callback: Callable[[str], None]) -> None:
        """Register the per-row 'Effacer' button callback."""
        ...

    def bind_form_submitted(self, callback: Callable[[], None]) -> None:
        """Register the form submit callback."""
        ...

    def bind_form_cancelled(self, callback: Callable[[], None]) -> None:
        """Register the form cancel callback."""
        ...

    def bind_csv_path_edited(self, callback: Callable[[str], None]) -> None:
        """Register the CSV path edition callback (debounced by the view)."""
        ...

    def bind_form_edited(self, callback: Callable[[], None]) -> None:
        """Register the real-time form change callback (field validation)."""
        ...

    def bind_row_height_changed(self, callback: Callable[[int], None]) -> None:
        """Register the live row-height change callback."""
        ...

    def apply_column_widths(self, widths: dict[str, int]) -> None:
        """Restore the persisted user column widths of the history table.

        Args:
            widths: Column key to width (pixels) mapping.
        """
        ...

    def bind_column_widths_changed(self, callback: Callable[[dict[str, int]], None]) -> None:
        """Register the debounced column-resize persistence callback."""
        ...

    def confirm(self, title: str, message: str) -> bool:
        """Ask a destructive-action confirmation (modal).

        Args:
            title: Dialog title.
            message: Dialog body.

        Returns:
            True when the user confirmed.
        """
        ...


# EOF
