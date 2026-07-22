# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol

from wishlistor.models.csv_document_model import CsvDocumentModel
from wishlistor.models.project_model import ProjectModel
from wishlistor.shared.validation_result import ValidationResult


class ICsvService(Protocol):
    """CSV document business logic: load, save, edits, ranks, undo/redo."""

    def load(self, project: ProjectModel) -> tuple[CsvDocumentModel | None, ValidationResult]:
        """Load the project CSV entirely in memory and normalize it.

        Args:
            project: The project whose CSV must be loaded.

        Returns:
            The document (None when the load is aborted) and every issue met.
        """
        ...

    def save(self, document: CsvDocumentModel, force: bool) -> tuple[bool, ValidationResult]:
        """Save the document atomically, preserving the original row order.

        Args:
            document: The document to write.
            force: When False, an external modification aborts with CSV_1012.

        Returns:
            (saved, issues); ``saved`` is False on conflict or write failure.
        """
        ...

    def save_as(self, document: CsvDocumentModel, new_path: str) -> ValidationResult:
        """Save the document under a new path (the caller updates the project).

        Args:
            document: The document to write.
            new_path: Destination file path.

        Returns:
            The issues met while writing (empty on success).
        """
        ...

    def add_url(self, document: CsvDocumentModel, project: ProjectModel, url: str) -> tuple[int, ValidationResult]:
        """Append a new row for *url*, unless it already exists (strict equality).

        Args:
            document: The open document.
            project: The owning project (mapping and weights).
            url: The reference value typed by the user.

        Returns:
            (row index, issues): the appended row index, or the existing row
            index with a CSV_1016 error when the value is already present.
        """
        ...

    def edit_cell(
        self, document: CsvDocumentModel, project: ProjectModel, row_index: int, column_name: str, value: str
    ) -> bool:
        """Apply a single-cell edit as one undoable action.

        Args:
            document: The open document.
            project: The owning project (rank recomputation).
            row_index: Row index in file order.
            column_name: Edited column name.
            value: New cell value.

        Returns:
            True when the value actually changed.
        """
        ...

    def mass_edit_cells(
        self,
        document: CsvDocumentModel,
        project: ProjectModel,
        row_indexes: list[int],
        column_name: str,
        value: str,
    ) -> bool:
        """Apply the same value to one column of many rows, as one undoable action.

        Args:
            document: The open document.
            project: The owning project (rank recomputation).
            row_indexes: Target rows in file order.
            column_name: Edited column name.
            value: New cell value.

        Returns:
            True when at least one cell changed.
        """
        ...

    def delete_rows(self, document: CsvDocumentModel, project: ProjectModel, row_indexes: list[int]) -> None:
        """Delete rows as one undoable action, then recompute the ranks.

        Args:
            document: The open document.
            project: The owning project.
            row_indexes: Target rows in file order.
        """
        ...

    def undo(self, document: CsvDocumentModel, project: ProjectModel) -> bool:
        """Undo the latest write action, restoring the exact previous state.

        Args:
            document: The open document.
            project: The owning project.

        Returns:
            True when something was undone.
        """
        ...

    def redo(self, document: CsvDocumentModel, project: ProjectModel) -> bool:
        """Redo the latest undone action.

        Args:
            document: The open document.
            project: The owning project.

        Returns:
            True when something was redone.
        """
        ...

    def is_clean(self) -> bool:
        """Return True when the document matches its last saved state."""
        ...

    def recompute_ranks(self, document: CsvDocumentModel, project: ProjectModel) -> ValidationResult:
        """Recompute every rank column after substituting missing source values.

        Args:
            document: The open document.
            project: The owning project (mapping and weights).

        Returns:
            The substitution warnings.
        """
        ...

    def reset_history(self, limit: int) -> None:
        """Clear the undo history and apply a new depth limit (project switch).

        Args:
            limit: Maximum history depth.
        """
        ...


# EOF
