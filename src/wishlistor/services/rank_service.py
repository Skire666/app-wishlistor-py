"""Rank columns computation and default-value substitutions (spec D.3).

Ranks are sequential 1..N. Missing or unparsable source values are substituted
with their default value (normalization), counted and reported as WARNINGs.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from wishlistor.models.csv_document_model import CsvDocumentModel
from wishlistor.models.project_model import ProjectModel
from wishlistor.shared.constants_util import (
    C_COL_RANK_23_SUMMED,
    C_COL_RANK_1234_SUMMED,
    C_COL_RANK_CUSTOM_TAGS,
    C_COL_RANK_NOTATION,
    C_COL_RANK_POPULARITY,
    C_COL_RANK_RELEASED,
    C_DEFAULT_DATETIME,
    C_DEFAULT_DATETIME_STR_CSV,
    C_DEFAULT_NUMERIC_VALUE,
)
from wishlistor.shared.default_value_util import default_value_from_key
from wishlistor.shared.enums.default_value_enum import DefaultValueEnum
from wishlistor.shared.enums.severity_enum import SeverityEnum
from wishlistor.shared.errors.csv_error import ErrorCodeCsv
from wishlistor.shared.typing.datetime_util import C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS
from wishlistor.shared.validation_result import ValidationResult


def _parse_date(value: str) -> datetime | None:
    """Parse an ISO datetime string, returning None on failure."""
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def _parse_number(value: str) -> float | None:
    """Parse a numeric cell ('.' or ',' decimal separator), None on failure."""
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return float(cleaned.replace(",", ".", 1))
    except ValueError:
        return None


class RankService:
    """Computes the five rank columns and normalizes their source columns."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def generate_id() -> str:
        """Return a new unique identifier for a rank computation batch."""
        return str(uuid.uuid4())

    def compute_all(self, document: CsvDocumentModel, project: ProjectModel) -> ValidationResult:
        """Substitute missing source values then recompute every rank column.

        Args:
            document: The open document (mutated in place).
            project: The owning project (mapping and tag weights).

        Returns:
            Substitution and mapping warnings.
        """
        result = ValidationResult()
        self._normalize_date_columns(document, project, result)
        released = self._rank_by_date(document, project.released_column, result)
        popularity = self._rank_by_number(document, project.popularity_column, result)
        notation = self._rank_by_number(document, project.scoring_column, result)
        tags_value = self._custom_tags_values(document, project)
        self._write_ranks(document, released, popularity, notation, tags_value)
        return result

    # -- substitutions -----------------------------------------------------------

    def _normalize_date_columns(
        self, document: CsvDocumentModel, project: ProjectModel, result: ValidationResult
    ) -> None:
        """Fill and normalize every `__date_*` column, then apply the project's column defaults."""
        self._apply_column_default_values(document, project)

    def _apply_column_default_values(self, document: CsvDocumentModel, project: ProjectModel) -> None:
        """Fill empty cells of user-configured columns with their default value (spec §6)."""
        for column, default_key in project.column_default_values:
            column_index = document.column_index(column)
            if column_index < 0 or not default_key:
                continue
            value = self._resolve_default_value(document, default_key)
            for row in document.rows:
                if not row[column_index].strip():
                    row[column_index] = value

    @staticmethod
    def _resolve_default_value(document: CsvDocumentModel, key: str) -> str:
        """Compute the literal substitution value for one default-value key."""
        choice = default_value_from_key(key)
        if choice is DefaultValueEnum.E_DATE_1900:
            return C_DEFAULT_DATETIME_STR_CSV
        if choice is DefaultValueEnum.E_DATE_TODAY:
            return datetime.now().strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS)
        if choice is DefaultValueEnum.E_COUNT_ZERO:
            return C_DEFAULT_NUMERIC_VALUE
        if choice is DefaultValueEnum.E_TOTAL_ROW_COUNT:
            return str(len(document.rows))
        if choice is DefaultValueEnum.E_EXTRACTOR_E0:
            return "e0"
        return ""

    def _report_substitutions(self, result: ValidationResult, column: str, count: int) -> None:
        """Log and report the number of substitutions applied to one column."""
        if count <= 0:
            return
        self._logger.warning("%s valeur(s) substituée(s) dans la colonne '%s'.", count, column)
        result.append(ErrorCodeCsv.CSV_1011, SeverityEnum.E_WARNING, {"count": count, "column": column})

    # -- rank computations ----------------------------------------------------------

    def _rank_by_date(self, document: CsvDocumentModel, column_name: str, result: ValidationResult) -> list[int]:
        """Rank rows from most recent (1) to oldest (N), substituting defaults."""
        column_index = self._mapped_index(document, column_name, result)
        count = len(document.rows)
        if column_index < 0:
            return list(range(1, count + 1))
        keys: list[datetime] = []
        substituted = 0
        for row in document.rows:
            parsed = _parse_date(row[column_index])
            if parsed is None:
                row[column_index] = C_DEFAULT_DATETIME_STR_CSV
                substituted += 1
                parsed = C_DEFAULT_DATETIME
            keys.append(parsed)  # push the datetime object, not the string
        self._report_substitutions(result, column_name, substituted)
        order = sorted(range(count), key=lambda i: keys[i], reverse=True)
        return self._order_to_ranks(order)

    def _rank_by_number(self, document: CsvDocumentModel, column_name: str, result: ValidationResult) -> list[int]:
        """Rank rows from lowest value (1) to highest (N), substituting defaults."""
        column_index = self._mapped_index(document, column_name, result)
        count = len(document.rows)
        if column_index < 0:
            return list(range(1, count + 1))
        keys: list[float] = []
        substituted = 0
        for row in document.rows:
            parsed = _parse_number(row[column_index])
            if parsed is None:
                row[column_index] = C_DEFAULT_NUMERIC_VALUE
                substituted += 1
                parsed = 0.0
            keys.append(parsed)
        self._report_substitutions(result, column_name, substituted)
        order = sorted(range(count), key=lambda i: keys[i])
        return self._order_to_ranks(order)

    def _mapped_index(self, document: CsvDocumentModel, column_name: str, result: ValidationResult) -> int:
        """Resolve a mapped source column, warning when unmapped or absent."""
        column_index = document.column_index(column_name) if column_name else -1
        if column_index < 0:
            display = column_name or "?"
            result.append(ErrorCodeCsv.CSV_1017, SeverityEnum.E_WARNING, {"column": display})
        return column_index

    @staticmethod
    def _order_to_ranks(order: list[int]) -> list[int]:
        """Convert a sorted row-index order into sequential per-row ranks."""
        ranks = [0] * len(order)
        for position, row_index in enumerate(order, start=1):
            ranks[row_index] = position
        return ranks

    @staticmethod
    def _custom_tags_values(document: CsvDocumentModel, project: ProjectModel) -> list[int]:
        """Compute the weighted tag value of every row (0 without tags)."""
        total = len(document.rows)
        weights = project.tag_weights
        values: list[int] = []
        for tags in document.tag_sets:
            weight = sum(weights.get(tag.value, 0.0) for tag in tags)
            values.append(round(weight * total))
        return values

    @staticmethod
    def _write_ranks(
        document: CsvDocumentModel,
        released: list[int],
        popularity: list[int],
        notation: list[int],
        tags_value: list[int],
    ) -> None:
        """Write the five rank columns into the document rows."""
        col_released = document.column_index(C_COL_RANK_RELEASED)
        col_popularity = document.column_index(C_COL_RANK_POPULARITY)
        col_notation = document.column_index(C_COL_RANK_NOTATION)
        col_tags = document.column_index(C_COL_RANK_CUSTOM_TAGS)
        col_1234_summed = document.column_index(C_COL_RANK_1234_SUMMED)
        col_23_summed = document.column_index(C_COL_RANK_23_SUMMED)
        for row_index, row in enumerate(document.rows):
            row[col_released] = str(released[row_index])
            row[col_popularity] = str(popularity[row_index])
            row[col_notation] = str(notation[row_index])
            row[col_tags] = str(tags_value[row_index])
            summed = released[row_index] + popularity[row_index] + notation[row_index] + tags_value[row_index]
            row[col_1234_summed] = str(summed)
            row[col_23_summed] = str(popularity[row_index] + notation[row_index])


# EOF
