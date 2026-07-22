"""Row-level CSV edit actions (URL add, cell/tag edits, mass actions, delete, undo/redo).

Mixed into CsvPresenter — extracted from csv_presenter.py to keep it maintainable
(Furripe MIR121: low maintainability index on the full presenter).
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import time

from wishlistor.interfaces.i_csv_service import ICsvService
from wishlistor.interfaces.i_csv_view import ICsvView
from wishlistor.models.app_config_model import AppConfigModel
from wishlistor.models.app_state_model import AppStateModel
from wishlistor.models.csv_document_model import CsvDocumentModel
from wishlistor.models.project_model import ProjectModel
from wishlistor.shared import i18n_fra
from wishlistor.shared.constants_util import (
    C_COL_CUSTOM_COMMENTS,
    C_COL_CUSTOM_TAGS,
    C_CSV_PRIMARY_KEY,
    C_SHORTCUT_CTRL_N,
    C_SHORTCUT_CTRL_O,
    C_SHORTCUT_CTRL_T,
)
from wishlistor.shared.enums.severity_enum import SeverityEnum
from wishlistor.shared.enums.tag_enum import TagEnum
from wishlistor.shared.errors.csv_error import ErrorCodeCsv
from wishlistor.shared.tag_util import apply_check, serialize_tags, tag_from_label
from wishlistor.shared.validation_result import ValidationResult

_OWNER: str = "csv"


class CsvEditFlowMixin:
    """Row-level edit actions for CsvPresenter, split out to keep it maintainable.

    Declares the host attributes it relies on (set by ``CsvPresenter.__init__``);
    it is never instantiated on its own.
    """

    _logger: logging.Logger
    _view: ICsvView
    _csv_service: ICsvService
    _config: AppConfigModel
    _app_state: AppStateModel
    _document: CsvDocumentModel | None
    _project: ProjectModel | None

    def _handle_url_submitted(self, url: str) -> None:
        """Add a new row for the typed URL, or focus the existing one."""
        document, project = self._document, self._project
        if document is None or project is None:
            return
        started = time.perf_counter()
        row_index, result = self._csv_service.add_url(document, project, url)
        if result.count_severities_by_code(ErrorCodeCsv.CSV_1016) > 0:
            self._view.set_url_feedback(i18n_fra.CSV_URL_ALREADY_PRESENT, True)
            self._view.focus_doc_row(row_index)
        elif row_index >= 0:
            self._view.set_url_feedback(i18n_fra.CSV_URL_ADDED, False)
            self._view.append_banner_issues(_only_warnings(result))
            self._view.refresh_table()
            self._sync_dirty()
            self._view.focus_doc_row(row_index)
        else:
            self._view.append_banner_issues(result)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'ajouter une URL' terminée en %s ms", elapsed_ms)

    def _handle_cell_edited(self, row_index: int, column_name: str, value: str) -> None:
        """Apply a double-click cell edit."""
        document, project = self._document, self._project
        if document is None or project is None:
            return
        if self._csv_service.edit_cell(document, project, row_index, column_name, value):
            self._view.refresh_table()
            self._sync_dirty()

    def _handle_row_tags_edited(self, row_index: int, labels: frozenset[str]) -> None:
        """Apply the tag selector result on one row."""
        tags = {tag_from_label(label) for label in labels} - {TagEnum.E_UNKNOWN}
        self._handle_cell_edited(row_index, C_COL_CUSTOM_TAGS, serialize_tags(tags))

    def _handle_mass_tags(self) -> None:
        """Open the tag composer for every checked row (applies on confirm, one undo action)."""
        document, project = self._document, self._project
        if document is None or project is None:
            return
        self._view.open_mass_tags(self._apply_mass_tags)

    def _apply_mass_tags(self, labels: frozenset[str] | None) -> None:
        """Apply the composed tag set to every checked row once the composer confirms."""
        document, project = self._document, self._project
        if labels is None or document is None or project is None:
            return
        started = time.perf_counter()
        tags = {tag_from_label(label) for label in labels} - {TagEnum.E_UNKNOWN}
        rows = list(self._view.snapshot().checked_rows)
        if self._csv_service.mass_edit_cells(document, project, rows, C_COL_CUSTOM_TAGS, serialize_tags(tags)):
            self._view.refresh_table()
            self._sync_dirty()
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'modifier les tags en masse' terminée en %s ms", elapsed_ms)

    def _handle_mass_comment(self) -> None:
        """Apply a comment to every checked row (one undo action)."""
        document, project = self._document, self._project
        if document is None or project is None:
            return
        text = self._view.ask_mass_comment()
        if text is None:
            return
        started = time.perf_counter()
        rows = list(self._view.snapshot().checked_rows)
        if self._csv_service.mass_edit_cells(document, project, rows, C_COL_CUSTOM_COMMENTS, text):
            self._view.refresh_table()
            self._sync_dirty()
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'modifier le commentaire en masse' terminée en %s ms", elapsed_ms)

    def _handle_delete_rows(self) -> None:
        """Delete every checked row after a modal confirmation."""
        document, project = self._document, self._project
        if document is None or project is None:
            return
        rows = list(self._view.snapshot().checked_rows)
        if not rows:
            return
        message = i18n_fra.CSV_DELETE_CONFIRM_MESSAGE.format(count=len(rows))
        if not self._view.confirm(i18n_fra.CSV_DELETE_CONFIRM_TITLE, message):
            return
        started = time.perf_counter()
        self._csv_service.delete_rows(document, project, rows)
        self._view.refresh_table()
        self._sync_dirty()
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'supprimer %s ligne(s)' terminée en %s ms", len(rows), elapsed_ms)

    def _handle_undo(self) -> None:
        """Undo the latest write action (Ctrl+Z)."""
        document, project = self._document, self._project
        if document is None or project is None:
            return
        if self._csv_service.undo(document, project):
            self._view.refresh_table()
            self._sync_dirty()

    def _handle_redo(self) -> None:
        """Redo the latest undone action (Ctrl+Y)."""
        document, project = self._document, self._project
        if document is None or project is None:
            return
        if self._csv_service.redo(document, project):
            self._view.refresh_table()
            self._sync_dirty()

    def _handle_shortcut_tags(self, shortcut_id: str) -> None:
        """Check the configured tags on the current row, then move on (Ctrl+O/N/T)."""
        document = self._document
        if document is None:
            return
        row_index = self._view.snapshot().current_doc_row
        if row_index < 0:
            return
        options = self._config.options
        labels_by_shortcut = {
            C_SHORTCUT_CTRL_O: options.shortcut_ctrl_o_tags,
            C_SHORTCUT_CTRL_N: options.shortcut_ctrl_n_tags,
            C_SHORTCUT_CTRL_T: options.shortcut_ctrl_t_tags,
        }
        labels = labels_by_shortcut[shortcut_id]
        tags = document.tag_sets[row_index]
        for label in labels:
            tag = tag_from_label(label)
            if tag is not TagEnum.E_UNKNOWN:
                tags = apply_check(tags, tag)

        self._log_event_tags_from_shortcut(document, row_index, labels, tags)

        next_doc_row = self._view.peek_next_doc_row()
        self._handle_cell_edited(row_index, C_COL_CUSTOM_TAGS, serialize_tags(tags))
        self._view.focus_doc_row(next_doc_row if next_doc_row >= 0 else row_index)

    def _log_event_tags_from_shortcut(
        self, document: CsvDocumentModel, row_index: int, labels: list[str], tags: frozenset[TagEnum]
    ) -> None:
        """Log the tags applied to a row by a shortcut (Ctrl+O/N/T).

        Args:
            document: Document the edited row belongs to.
            row_index: Index of the edited row within the document.
            labels: Shortcut tag labels, as configured by the user.
            tags: Resulting tag set applied on the row.
        """
        col_index = document.column_index(C_CSV_PRIMARY_KEY)
        pk_used = document.rows[row_index][col_index] if col_index >= 0 else "?"
        tags_used = str([c.value for c in tags])
        self._logger.info("Shortcuts '%s' avec tags '%s' sur PK '%s'", labels, tags_used, pk_used)

    def _handle_row_delete_requested(self, row_index: int) -> None:
        """Delete one row from its 'X' button after a modal confirmation."""
        document, project = self._document, self._project
        if document is None or project is None or not 0 <= row_index < len(document):
            return
        message = i18n_fra.CSV_DELETE_CONFIRM_MESSAGE.format(count=1)
        if not self._view.confirm(i18n_fra.CSV_DELETE_CONFIRM_TITLE, message):
            return
        started = time.perf_counter()
        self._csv_service.delete_rows(document, project, [row_index])
        self._view.refresh_table()
        self._sync_dirty()
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'supprimer la ligne %s' terminée en %s ms", row_index, elapsed_ms)

    def _sync_dirty(self) -> None:
        """Align the save button and global dirty flag with the document."""
        document = self._document
        dirty = document.is_dirty if document is not None else False
        self._view.set_save_enabled(dirty)
        self._app_state.set_dirty(_OWNER, dirty)


def _only_warnings(result: ValidationResult) -> ValidationResult:
    """Return a copy of *result* keeping only the warnings."""
    filtered = ValidationResult()
    for issue in result.issues:
        if issue.severity is SeverityEnum.E_WARNING:
            filtered.append(issue.code, issue.severity, issue.context)
    return filtered


# EOF
