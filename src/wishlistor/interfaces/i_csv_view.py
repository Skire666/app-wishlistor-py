# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from wishlistor.interfaces.i_base_view import IBaseView
from wishlistor.models.csv_document_model import CsvDocumentModel
from wishlistor.models.view_state_model import CsvViewState
from wishlistor.shared.enums.save_choice_enum import SaveChoiceEnum
from wishlistor.shared.validation_result import ValidationResult


class ICsvView(IBaseView, Protocol):
    """CSV module: table, filters, search, URL insertion, mass actions, save."""

    # -- presenter -> view -------------------------------------------------------

    def snapshot(self) -> CsvViewState:
        """Return the current state of the interactive controls."""
        ...

    def set_projects(self, entries: list[tuple[str, str]], current_id: str) -> None:
        """Fill the project combo box.

        Args:
            entries: (project id, display label) pairs, recency first.
            current_id: Project id to select (empty for none).
        """
        ...

    def show_no_project(self, message: str) -> None:
        """Show the inline invitation instead of the table.

        Args:
            message: French invitation text.
        """
        ...

    def show_document(self, document: CsvDocumentModel, visible_columns: list[str], row_height: int) -> None:
        """Display a freshly loaded document.

        Args:
            document: The loaded document (shared reference, read for display).
            visible_columns: Column names to show, in display order.
            row_height: Row height in pixels.
        """
        ...

    def refresh_table(self) -> None:
        """Re-read the document and repaint the table (keeps filters and sort)."""
        ...

    def set_row_height(self, row_height: int) -> None:
        """Apply a new row height in real time.

        Args:
            row_height: Row height in pixels.
        """
        ...

    def set_visible_columns(self, visible_columns: list[str]) -> None:
        """Apply a new visible-column set and order.

        Args:
            visible_columns: Column names to show, in display order.
        """
        ...

    def set_column_nicknames(self, nicknames: dict[str, str]) -> None:
        """Apply the column nickname mapping to the table header.

        Args:
            nicknames: Column name to display nickname mapping.
        """
        ...

    def apply_column_widths(self, widths: dict[str, int]) -> None:
        """Restore the persisted user column widths.

        Args:
            widths: Column name to width (pixels) mapping.
        """
        ...

    def auto_size_columns(self) -> None:
        """First-open sizing: fit each column to its content, capped at 200 px."""
        ...

    def apply_sort_order(self, column: str, descending: bool) -> None:
        """Restore the persisted sort order.

        Args:
            column: Sorted column name (empty leaves the natural row order).
            descending: True for a descending sort.
        """
        ...

    def set_mass_actions_enabled(self, enabled: bool) -> None:
        """Enable or grey out the mass action buttons (tags, comment, delete).

        Args:
            enabled: True when at least one row is checked.
        """
        ...

    def set_save_enabled(self, enabled: bool) -> None:
        """Enable or grey out the save button.

        Args:
            enabled: True when unsaved modifications exist.
        """
        ...

    def set_last_save_label(self, label: str) -> None:
        """Refresh the 'Dernière sauvegarde' label.

        Args:
            label: Display text ('--' when never saved).
        """
        ...

    def set_file_mtime_label(self, label: str) -> None:
        """Refresh the on-disk mtime label of the footer.

        Args:
            label: Display text.
        """
        ...

    def set_url_feedback(self, message: str, is_error: bool) -> None:
        """Show the verification label next to the URL field.

        Args:
            message: Feedback text (empty clears it).
            is_error: True renders the error color.
        """
        ...

    def append_banner_issues(self, rs: ValidationResult) -> None:
        """Append warnings and errors to the inline footer banner.

        Args:
            rs: Issues to list.
        """
        ...

    def clear_banner(self) -> None:
        """Empty the inline footer banner."""
        ...

    def focus_doc_row(self, row_index: int) -> None:
        """Highlight and scroll to a document row (if currently visible).

        Args:
            row_index: Row index in file order.
        """
        ...

    def peek_next_doc_row(self) -> int:
        """Return the document row right after the current one, in the display order still in effect.

        Meant to be called before an edit that may re-sort the table, so the
        Presenter can capture "the next row" before the sort moves rows around.

        Returns:
            The document row index, or -1 when there is no next visible row.
        """
        ...

    def set_busy(self, busy: bool) -> None:
        """Show or hide the blocking progress overlay (min 250 ms).

        Args:
            busy: True while a worker runs.
        """
        ...

    # -- dialogs (presenter decides, view renders) ---------------------------------

    def ask_unsaved_choice(self) -> SaveChoiceEnum:
        """Ask what to do with unsaved modifications (spec F)."""
        ...

    def ask_conflict_choice(self) -> SaveChoiceEnum:
        """Ask what to do when the file changed externally (spec D.5)."""
        ...

    def ask_save_as_path(self, current_path: str) -> str:
        """Open the native save dialog.

        Args:
            current_path: Initial location.

        Returns:
            The chosen path, or an empty string on cancel.
        """
        ...

    def ask_mass_comment(self) -> str | None:
        """Ask the comment to apply to the selected rows (None on cancel)."""
        ...

    def open_mass_tags(self, callback: Callable[[frozenset[str] | None], None]) -> None:
        """Open the modeless tag composer for the selected rows.

        Args:
            callback: Called with the composed tag labels, or None on cancel.
        """
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

    def show_critical(self, title: str, message: str) -> None:
        """Show a blocking error popup (critical project load failure).

        Args:
            title: Dialog title.
            message: Dialog body.
        """
        ...

    # -- view -> presenter bindings ---------------------------------------------------

    def bind_project_selected(self, callback: Callable[[str], None]) -> None:
        """Register the project combo callback (receives the project id)."""
        ...

    def bind_open_folder_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Ouvrir dossier' hyperlink callback."""
        ...

    def bind_project_options_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Options du projet' button callback."""
        ...

    def bind_url_submitted(self, callback: Callable[[str], None]) -> None:
        """Register the URL submission callback (Enter key or button)."""
        ...

    def bind_mass_tags_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Modifier les tags' button callback."""
        ...

    def bind_mass_comment_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Modifier le commentaire' button callback."""
        ...

    def bind_delete_rows_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Supprimer la ligne' button callback."""
        ...

    def bind_selection_changed(self, callback: Callable[[int], None]) -> None:
        """Register the checked-row-count callback (mass action enabling)."""
        ...

    def bind_cell_edited(self, callback: Callable[[int, str, str], None]) -> None:
        """Register the cell edit callback (doc row, column name, new value)."""
        ...

    def bind_row_tags_edited(self, callback: Callable[[int, frozenset[str]], None]) -> None:
        """Register the tag selector callback (doc row, final tag labels)."""
        ...

    def bind_link_activated(self, callback: Callable[[str], None]) -> None:
        """Register the link-cell click callback (receives the cell value)."""
        ...

    def bind_save_clicked(self, callback: Callable[[], None]) -> None:
        """Register the save button / Ctrl+S callback."""
        ...

    def bind_undo(self, callback: Callable[[], None]) -> None:
        """Register the Ctrl+Z callback."""
        ...

    def bind_redo(self, callback: Callable[[], None]) -> None:
        """Register the Ctrl+Y callback."""
        ...

    def bind_shortcut_tags(self, callback: Callable[[str], None]) -> None:
        """Register the Ctrl+O / Ctrl+N / Ctrl+T callback (receives the shortcut id).

        The key combinations are fixed; the tags they check come from the
        application options.
        """
        ...

    def bind_visible_columns_changed(self, callback: Callable[[list[str]], None]) -> None:
        """Register the column-management callback (new visible order)."""
        ...

    def bind_column_nicknames_changed(self, callback: Callable[[dict[str, str]], None]) -> None:
        """Register the column-nickname edition callback ('Gestion des colonnes')."""
        ...

    def bind_column_widths_changed(self, callback: Callable[[dict[str, int]], None]) -> None:
        """Register the user column-resize callback (debounced by the view)."""
        ...

    def bind_sort_order_changed(self, callback: Callable[[str, bool], None]) -> None:
        """Register the user sort-order callback (column name, descending)."""
        ...

    def bind_row_delete_requested(self, callback: Callable[[int], None]) -> None:
        """Register the per-row 'X' delete callback (receives the doc row)."""
        ...


# EOF
