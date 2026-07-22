"""CSV document business logic: load, normalize, save, edits, undo (spec D/E)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import uuid

from wishlistor.interfaces.i_csv_repository import ICsvRepository
from wishlistor.interfaces.i_undo_service import IUndoService
from wishlistor.models.csv_document_model import CsvDocumentModel
from wishlistor.models.project_model import ProjectModel
from wishlistor.models.undo_action_model import CellChange, RowSnapshot, UndoActionModel
from wishlistor.services.rank_service import RankService
from wishlistor.shared.constants_util import (
    C_COL_CUSTOM_COMMENTS,
    C_COL_CUSTOM_TAGS,
    C_CSV_BIG_FILE_BYTES,
    C_CSV_FIRST_CREATED,
    C_CSV_LAST_MODIFIED,
    C_RANK_COLUMNS,
)
from wishlistor.shared.enums.severity_enum import SeverityEnum
from wishlistor.shared.enums.undo_action_enum import UndoActionEnum
from wishlistor.shared.errors.csv_error import ErrorCodeCsv
from wishlistor.shared.exceptions.csv_structure_error import CsvStructureError
from wishlistor.shared.exceptions.file_access_error import FileAccessError
from wishlistor.shared.tag_util import clean_tags, serialize_tags
from wishlistor.shared.validation_result import ValidationResult

_MAX_LINE_WARNINGS: int = 50
_MAX_LISTED_LINES: int = 20
_MTIME_TOLERANCE: float = 1e-6


def _format_lines(lines: list[int]) -> str:
    """Format faulty line numbers for display, truncated past 20 entries."""
    shown = ", ".join(str(line) for line in lines[:_MAX_LISTED_LINES])
    if len(lines) > _MAX_LISTED_LINES:
        return f"{shown}… (+{len(lines) - _MAX_LISTED_LINES})"
    return shown


class CsvService:
    """Loads, normalizes, edits and saves CSV documents."""

    def __init__(
        self, csv_repository: ICsvRepository, rank_service: RankService, undo_service: IUndoService
    ) -> None:
        """Initialize the service.

        Args:
            csv_repository: Raw CSV file access.
            rank_service: Rank computation engine.
            undo_service: Write-action history.
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._csv_repository = csv_repository
        self._rank_service = rank_service
        self._undo_service = undo_service

    @staticmethod
    def generate_id() -> str:
        """Return a new unique identifier for a document session."""
        return str(uuid.uuid4())

    # -- load -------------------------------------------------------------------

    def load(self, project: ProjectModel) -> tuple[CsvDocumentModel | None, ValidationResult]:
        """Load the project CSV entirely in memory and normalize it.

        Args:
            project: The project whose CSV must be loaded.

        Returns:
            The document (None when the load is aborted) and every issue met.
        """
        result = ValidationResult()
        path = project.csv_path
        stats = self._check_file_stats(path, result)
        if stats is None:
            return None, result
        raw = self._read_file(path, result)
        if raw is None:
            return None, result
        header, rows = raw
        if not self._check_header(header, result):
            return None, result
        self._normalize_row_lengths(header, rows, result)
        document = self._build_document(path, header, rows, result)
        if not self._check_primary(document, project, result):
            return None, result
        self._clean_all_tags(document, result)
        document.set_search_columns(project.search_index_columns)
        result.extend(self._rank_service.compute_all(document, project))
        document.set_file_stats(stats[0], stats[1])
        document.is_dirty = False
        self._undo_service.clear()
        self._logger.info("CSV chargé : %s lignes, %s colonnes (%s)", len(document), len(header), path)
        return document, result

    def _check_file_stats(self, path: str, result: ValidationResult) -> tuple[float, int] | None:
        """Check the file presence and report the 100 MB warning (spec D.2)."""
        stats = self._csv_repository.file_stats(path)
        if stats is None:
            result.append(ErrorCodeCsv.CSV_1001, SeverityEnum.E_ERROR, {"path": path})
            return None
        if stats[1] > C_CSV_BIG_FILE_BYTES:
            size_label = f"{stats[1] / (1024 * 1024):.0f} Mo"
            result.append(ErrorCodeCsv.CSV_1014, SeverityEnum.E_WARNING, {"size": size_label})
        return stats

    def _read_file(self, path: str, result: ValidationResult) -> tuple[list[str], list[list[str]]] | None:
        """Read the raw file, converting repository exceptions to error codes."""
        try:
            return self._csv_repository.read_all(path)
        except CsvStructureError:
            result.append(ErrorCodeCsv.CSV_1002, SeverityEnum.E_ERROR)
        except FileAccessError:
            result.append(ErrorCodeCsv.CSV_1001, SeverityEnum.E_ERROR, {"path": path})
        return None

    def _check_header(self, header: list[str], result: ValidationResult) -> bool:
        """Reject duplicated/empty column names and unknown dunder columns."""
        seen: set[str] = set()
        bad: list[str] = []
        for name in header:
            if not name.strip() or name in seen:
                bad.append(name or "(vide)")
            seen.add(name)
        if bad:
            result.append(ErrorCodeCsv.CSV_1003, SeverityEnum.E_ERROR, {"columns": ", ".join(bad)})
            return False
        return True

    def _normalize_row_lengths(self, header: list[str], rows: list[list[str]], result: ValidationResult) -> None:
        """Pad or truncate inconsistent rows, warning with their line numbers."""
        expected = len(header)
        warned = 0
        for line, row in enumerate(rows, start=2):
            found = len(row)
            if found == expected:
                continue
            if warned < _MAX_LINE_WARNINGS:
                context = {"line": line, "found": found, "expected": expected}
                result.append(ErrorCodeCsv.CSV_1008, SeverityEnum.E_WARNING, context)
                warned += 1
            if found < expected:
                row.extend([""] * (expected - found))
            else:
                del row[expected:]

    def _build_document(
        self, path: str, header: list[str], rows: list[list[str]], result: ValidationResult
    ) -> CsvDocumentModel:
        """Assemble the document, adding the special columns when absent."""
        for name in (C_COL_CUSTOM_TAGS, C_COL_CUSTOM_COMMENTS):
            if name not in header:
                header.append(name)
                for row in rows:
                    row.append("")
        for name in C_RANK_COLUMNS:
            if name in header:
                result.append(ErrorCodeCsv.CSV_1015, SeverityEnum.E_WARNING, {"column": name})
            else:
                header.append(name)
                for row in rows:
                    row.append("")
        document = CsvDocumentModel()
        document.csv_path = path
        document.header = header
        document.rows.extend(rows)
        return document

    def _check_primary(self, document: CsvDocumentModel, project: ProjectModel, result: ValidationResult) -> bool:
        """Verify the reference column exists, is filled, and has no duplicates."""
        column_index = document.column_index(project.primary_column)
        if column_index < 0:
            result.append(ErrorCodeCsv.CSV_1005, SeverityEnum.E_ERROR, {"column": project.primary_column})
            return False
        empty_lines: list[int] = []
        duplicate_lines: list[int] = []
        seen: dict[str, int] = {}
        for line, row in enumerate(document.rows, start=2):
            value = row[column_index]
            if not value.strip():
                empty_lines.append(line)
            elif value in seen:
                duplicate_lines.append(line)
            else:
                seen[value] = line
        if duplicate_lines:
            result.append(ErrorCodeCsv.CSV_1006, SeverityEnum.E_ERROR, {"lines": _format_lines(duplicate_lines)})
        if empty_lines:
            result.append(ErrorCodeCsv.CSV_1007, SeverityEnum.E_ERROR, {"lines": _format_lines(empty_lines)})
        return not duplicate_lines and not empty_lines

    def _clean_all_tags(self, document: CsvDocumentModel, result: ValidationResult) -> None:
        """Strictly clean every `__custom_tags__` cell (spec D.4)."""
        column_index = document.column_index(C_COL_CUSTOM_TAGS)
        warned = 0
        for line, row in enumerate(document.rows, start=2):
            retained, dropped = clean_tags(row[column_index])
            row[column_index] = serialize_tags(retained)
            if dropped and warned < _MAX_LINE_WARNINGS:
                context: dict[str, object] = {"line": line, "segments": ", ".join(dropped)}
                result.append(ErrorCodeCsv.CSV_1010, SeverityEnum.E_WARNING, context)
                warned += 1

    # -- save -----------------------------------------------------------------------

    def save(self, document: CsvDocumentModel, force: bool) -> tuple[bool, ValidationResult]:
        """Save the document atomically, preserving the original row order.

        Args:
            document: The document to write.
            force: When False, an external modification aborts with CSV_1012.

        Returns:
            (saved, issues); ``saved`` is False on conflict or write failure.
        """
        result = ValidationResult()
        path = document.csv_path
        if not force and self._is_externally_modified(document):
            result.append(ErrorCodeCsv.CSV_1012, SeverityEnum.E_ERROR)
            return False, result
        try:
            mtime, size = self._csv_repository.write_atomic(path, document.header, document.rows)
        except FileAccessError:
            result.append(ErrorCodeCsv.CSV_1013, SeverityEnum.E_ERROR, {"path": path})
            return False, result
        document.set_file_stats(mtime, size)
        document.is_dirty = False
        self._undo_service.mark_clean()
        return True, result

    def _is_externally_modified(self, document: CsvDocumentModel) -> bool:
        """Return True when the on-disk file changed since the last load/save."""
        stats = self._csv_repository.file_stats(document.csv_path)
        if stats is None:
            return True
        return abs(stats[0] - document.mtime) > _MTIME_TOLERANCE or stats[1] != document.size_bytes

    def save_as(self, document: CsvDocumentModel, new_path: str) -> ValidationResult:
        """Save the document under a new path (the caller updates the project).

        Args:
            document: The document to write.
            new_path: Destination file path.

        Returns:
            The issues met while writing (empty on success).
        """
        result = ValidationResult()
        try:
            mtime, size = self._csv_repository.write_atomic(new_path, document.header, document.rows)
        except FileAccessError:
            result.append(ErrorCodeCsv.CSV_1013, SeverityEnum.E_ERROR, {"path": new_path})
            return result
        document.csv_path = new_path
        document.set_file_stats(mtime, size)
        document.is_dirty = False
        self._undo_service.mark_clean()
        return result

    # -- edits ------------------------------------------------------------------------

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
        result = ValidationResult()
        column_index = document.column_index(project.primary_column)
        if column_index < 0:
            result.append(ErrorCodeCsv.CSV_1005, SeverityEnum.E_ERROR, {"column": project.primary_column})
            return -1, result
        existing = document.find_in_column(column_index, url)
        if existing >= 0:
            result.append(ErrorCodeCsv.CSV_1016, SeverityEnum.E_ERROR)
            return existing, result
        values = [""] * len(document.header)
        values[column_index] = url
        row_index = len(document)
        document.insert_row(row_index, values)
        result.extend(self._rank_service.compute_all(document, project))
        snapshot = RowSnapshot(row_index=row_index, values=tuple(document.rows[row_index]))
        self._undo_service.push(UndoActionModel(kind=UndoActionEnum.E_ADD_ROW, rows=(snapshot,)))
        return row_index, result

    def edit_cell(
        self, document: CsvDocumentModel, project: ProjectModel, row_index: int, column_name: str, value: str
    ) -> bool:
        """Apply a single-cell edit as one undoable action.

        Args:
            document: The open document.
            project: The owning project.
            row_index: Row index in file order.
            column_name: Edited column name.
            value: New cell value.

        Returns:
            True when the value actually changed.
        """
        column_index = document.column_index(column_name)
        if column_index < 0 or column_name in C_RANK_COLUMNS:
            return False
        old = document.cell(row_index, column_index)
        if old == value:
            return False
        document.set_cell(row_index, column_index, value)
        change = CellChange(row_index=row_index, column_index=column_index, old_value=old, new_value=value)
        self._undo_service.push(UndoActionModel(kind=UndoActionEnum.E_CELL_EDIT, changes=(change,)))
        self._recompute_if_needed(document, project, column_name)
        return True

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
            project: The owning project.
            row_indexes: Target rows in file order.
            column_name: Edited column name.
            value: New cell value.

        Returns:
            True when at least one cell changed.
        """
        column_index = document.column_index(column_name)
        if column_index < 0 or column_name in C_RANK_COLUMNS:
            return False
        changes: list[CellChange] = []
        for row_index in row_indexes:
            old = document.cell(row_index, column_index)
            if old == value:
                continue
            document.set_cell(row_index, column_index, value)
            change = CellChange(row_index=row_index, column_index=column_index, old_value=old, new_value=value)
            changes.append(change)
        if not changes:
            return False
        self._undo_service.push(UndoActionModel(kind=UndoActionEnum.E_MASS_EDIT, changes=tuple(changes)))
        self._recompute_if_needed(document, project, column_name)
        return True

    def delete_rows(self, document: CsvDocumentModel, project: ProjectModel, row_indexes: list[int]) -> None:
        """Delete rows as one undoable action, then recompute the ranks.

        Args:
            document: The open document.
            project: The owning project.
            row_indexes: Target rows in file order.
        """
        ordered = sorted(set(row_indexes))
        snapshots = tuple(RowSnapshot(row_index=i, values=tuple(document.rows[i])) for i in ordered)
        for row_index in reversed(ordered):
            document.remove_row(row_index)
        self._undo_service.push(UndoActionModel(kind=UndoActionEnum.E_DELETE_ROWS, rows=snapshots))
        self._rank_service.compute_all(document, project)

    def _recompute_if_needed(self, document: CsvDocumentModel, project: ProjectModel, column_name: str) -> None:
        """Recompute the ranks when the edited column feeds them."""
        sources = {C_COL_CUSTOM_TAGS, project.released_column, project.popularity_column, project.scoring_column}
        if column_name in sources or column_name in {C_CSV_FIRST_CREATED, C_CSV_LAST_MODIFIED}:
            self._rank_service.compute_all(document, project)

    # -- undo / redo ---------------------------------------------------------------------

    def undo(self, document: CsvDocumentModel, project: ProjectModel) -> bool:
        """Undo the latest write action, restoring the exact previous state.

        Args:
            document: The open document.
            project: The owning project.

        Returns:
            True when something was undone.
        """
        action = self._undo_service.undo()
        if action is None:
            return False
        if action.kind in {UndoActionEnum.E_CELL_EDIT, UndoActionEnum.E_MASS_EDIT}:
            for change in reversed(action.changes):
                document.set_cell(change.row_index, change.column_index, change.old_value)
        elif action.kind is UndoActionEnum.E_ADD_ROW:
            for snapshot in sorted(action.rows, key=lambda s: s.row_index, reverse=True):
                document.remove_row(snapshot.row_index)
        elif action.kind is UndoActionEnum.E_DELETE_ROWS:
            for snapshot in sorted(action.rows, key=lambda s: s.row_index):
                document.insert_row(snapshot.row_index, list(snapshot.values))
        self._finish_history_step(document, project)
        return True

    def redo(self, document: CsvDocumentModel, project: ProjectModel) -> bool:
        """Redo the latest undone action.

        Args:
            document: The open document.
            project: The owning project.

        Returns:
            True when something was redone.
        """
        action = self._undo_service.redo()
        if action is None:
            return False
        if action.kind in {UndoActionEnum.E_CELL_EDIT, UndoActionEnum.E_MASS_EDIT}:
            for change in action.changes:
                document.set_cell(change.row_index, change.column_index, change.new_value)
        elif action.kind is UndoActionEnum.E_ADD_ROW:
            for snapshot in sorted(action.rows, key=lambda s: s.row_index):
                document.insert_row(snapshot.row_index, list(snapshot.values))
        elif action.kind is UndoActionEnum.E_DELETE_ROWS:
            for snapshot in sorted(action.rows, key=lambda s: s.row_index, reverse=True):
                document.remove_row(snapshot.row_index)
        self._finish_history_step(document, project)
        return True

    def _finish_history_step(self, document: CsvDocumentModel, project: ProjectModel) -> None:
        """Recompute ranks and realign the dirty flag after an undo/redo."""
        self._rank_service.compute_all(document, project)
        document.is_dirty = not self._undo_service.is_at_clean_state()

    def is_clean(self) -> bool:
        """Return True when the document matches its last saved state."""
        return self._undo_service.is_at_clean_state()

    def recompute_ranks(self, document: CsvDocumentModel, project: ProjectModel) -> ValidationResult:
        """Recompute every rank column after substituting missing source values.

        Args:
            document: The open document.
            project: The owning project (mapping and weights).

        Returns:
            The substitution warnings.
        """
        return self._rank_service.compute_all(document, project)

    def reset_history(self, limit: int) -> None:
        """Clear the undo history and apply a new depth limit (project switch).

        Args:
            limit: Maximum history depth.
        """
        self._undo_service.clear()
        self._undo_service.set_limit(limit)


# EOF
