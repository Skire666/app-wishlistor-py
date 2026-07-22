"""A project: CSV path, metadata, column mapping and display preferences."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Self

from wishlistor.shared.constants_util import (
    C_CSV_PRIMARY_KEY,
    C_MIN_SEARCH_INDEX_COLUMNS,
    C_MIN_VISIBLE_COLUMNS,
    C_ROW_HEIGHT_DEFAULT,
    C_ROW_HEIGHT_MAX,
    C_ROW_HEIGHT_MIN,
    C_TAG_WEIGHT_MAX,
    C_TAG_WEIGHT_MIN,
    C_TEXT_FIELD_MAX_LEN,
    C_TEXT_FIELD_MIN_LEN,
)
from wishlistor.shared.enums.copy_mode_enum import CopyModeEnum
from wishlistor.shared.enums.severity_enum import SeverityEnum
from wishlistor.shared.errors.project_error import ErrorCodeProject
from wishlistor.shared.tag_util import C_DEFAULT_TAG_WEIGHTS
from wishlistor.shared.typing.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from wishlistor.shared.typing.int_util import safe_int_from_str
from wishlistor.shared.typing.json_util import as_object_list, as_str_list, as_str_object_dict
from wishlistor.shared.validation_result import ValidationResult


def _read_str(data: dict[str, object], key: str) -> str:
    """Return a string value from a raw dictionary, or an empty string."""
    value = data.get(key)
    return value if isinstance(value, str) else ""


def _read_str_list(data: dict[str, object], key: str) -> list[str]:
    """Return a list of strings from a raw dictionary, or an empty list."""
    return as_str_list(data.get(key))


def _read_column_default_values(data: dict[str, object]) -> list[tuple[str, str]]:
    """Return the (column, default value) pairs, tolerating malformed entries."""
    raw = as_object_list(data.get("column_default_values"))
    if raw is None:
        return []
    result: list[tuple[str, str]] = []
    for item in raw:
        typed = as_str_object_dict(item)
        if typed is None:
            continue
        column = _read_str(typed, "column")
        default_value = _read_str(typed, "default_value")
        if column or default_value:
            result.append((column, default_value))
    return result


class ProjectModel:
    """One CSV project with its column mapping and display preferences."""

    def __init__(self) -> None:
        """Initialize an empty project with default values."""
        self._id_project: str = ""
        self._name: str = ""
        self._csv_path: str = ""
        self._website: str = ""
        self._category: str = ""
        self._created_at: str = ""
        self._modified_at: str = ""
        self._last_opened: str = ""
        self._row_height: int = C_ROW_HEIGHT_DEFAULT
        self._tag_weights: dict[str, float] = dict(C_DEFAULT_TAG_WEIGHTS)
        self._primary_column: str = C_CSV_PRIMARY_KEY
        self._released_column: str = ""
        self._popularity_column: str = ""
        self._scoring_column: str = ""
        self._search_index_columns: list[str] = []
        self._visible_columns: list[str] = []
        self._column_order: list[str] = []
        self._column_widths: dict[str, int] = {}
        self._column_nicknames: dict[str, str] = {}
        self._column_default_values: list[tuple[str, str]] = []
        self._sort_column: str = ""
        self._sort_descending: bool = False

    # -- identity and properties -----------------------------------------------

    @property
    def id_project(self) -> str:
        """Unique identifier of the project."""
        return self._id_project

    @id_project.setter
    def id_project(self, value: str) -> None:
        """Set the unique identifier of the project."""
        self._id_project = value

    @property
    def name(self) -> str:
        """Display name of the project (1..64 characters)."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the display name."""
        self._name = value

    @property
    def csv_path(self) -> str:
        """Path to the CSV file managed by the project."""
        return self._csv_path

    @csv_path.setter
    def csv_path(self, value: str) -> None:
        """Set the CSV file path."""
        self._csv_path = value

    @property
    def website(self) -> str:
        """Target website label (1..64 characters)."""
        return self._website

    @website.setter
    def website(self, value: str) -> None:
        """Set the target website label."""
        self._website = value

    @property
    def category(self) -> str:
        """Project category label (1..64 characters)."""
        return self._category

    @category.setter
    def category(self, value: str) -> None:
        """Set the project category label."""
        self._category = value

    @property
    def created_at(self) -> str:
        """Creation timestamp of the project."""
        return self._created_at

    @property
    def modified_at(self) -> str:
        """Last modification timestamp of the project."""
        return self._modified_at

    @property
    def last_opened(self) -> str:
        """Timestamp of the last time the project was opened."""
        return self._last_opened

    @last_opened.setter
    def last_opened(self, value: str) -> None:
        """Set the last opened timestamp."""
        self._last_opened = value

    @property
    def row_height(self) -> int:
        """CSV table row height in pixels (10..200)."""
        return self._row_height

    @row_height.setter
    def row_height(self, value: int) -> None:
        """Set the CSV table row height."""
        self._row_height = value

    @property
    def tag_weights(self) -> dict[str, float]:
        """Per-tag weights (fraction of N) used by the custom-tags rank."""
        return self._tag_weights

    @tag_weights.setter
    def tag_weights(self, value: dict[str, float]) -> None:
        """Set the per-tag weights."""
        self._tag_weights = dict(value)

    @property
    def primary_column(self) -> str:
        """Reference column holding unique, never-empty row keys."""
        return self._primary_column

    @primary_column.setter
    def primary_column(self, value: str) -> None:
        """Set the reference column."""
        self._primary_column = value

    @property
    def released_column(self) -> str:
        """Mapped publication-date column (may be empty)."""
        return self._released_column

    @released_column.setter
    def released_column(self, value: str) -> None:
        """Set the publication-date column."""
        self._released_column = value

    @property
    def popularity_column(self) -> str:
        """Mapped popularity column (may be empty)."""
        return self._popularity_column

    @popularity_column.setter
    def popularity_column(self, value: str) -> None:
        """Set the popularity column."""
        self._popularity_column = value

    @property
    def scoring_column(self) -> str:
        """Mapped notation column (may be empty)."""
        return self._scoring_column

    @scoring_column.setter
    def scoring_column(self, value: str) -> None:
        """Set the notation column."""
        self._scoring_column = value

    @property
    def search_index_columns(self) -> list[str]:
        """Columns concatenated into the search/filter index string."""
        return self._search_index_columns

    @search_index_columns.setter
    def search_index_columns(self, value: list[str]) -> None:
        """Set the indexed columns."""
        self._search_index_columns = list(value)

    @property
    def visible_columns(self) -> list[str]:
        """Columns currently displayed (display state only)."""
        return self._visible_columns

    @visible_columns.setter
    def visible_columns(self, value: list[str]) -> None:
        """Set the displayed columns."""
        self._visible_columns = list(value)

    @property
    def column_order(self) -> list[str]:
        """Display order of the columns."""
        return self._column_order

    @column_order.setter
    def column_order(self, value: list[str]) -> None:
        """Set the display order of the columns."""
        self._column_order = list(value)

    @property
    def column_default_values(self) -> list[tuple[str, str]]:
        """(column, default value key) pairs applied to empty cells on load/add (spec §2)."""
        return self._column_default_values

    @column_default_values.setter
    def column_default_values(self, value: list[tuple[str, str]]) -> None:
        """Set the column default-value assignments."""
        self._column_default_values = list(value)

    @property
    def column_widths(self) -> dict[str, int]:
        """User-resized column widths in pixels, keyed by column name."""
        return self._column_widths

    @column_widths.setter
    def column_widths(self, value: dict[str, int]) -> None:
        """Set the persisted column widths."""
        self._column_widths = dict(value)

    @property
    def column_nicknames(self) -> dict[str, str]:
        """Column name to display nickname mapping (falls back to the physical name)."""
        return self._column_nicknames

    @column_nicknames.setter
    def column_nicknames(self, value: dict[str, str]) -> None:
        """Set the column nickname mapping."""
        self._column_nicknames = dict(value)

    @property
    def sort_column(self) -> str:
        """Last user-sorted column name (empty for the natural row order)."""
        return self._sort_column

    @sort_column.setter
    def sort_column(self, value: str) -> None:
        """Set the last sorted column."""
        self._sort_column = value

    @property
    def sort_descending(self) -> bool:
        """True when the last sort was descending."""
        return self._sort_descending

    @sort_descending.setter
    def sort_descending(self, value: bool) -> None:
        """Set the last sort direction."""
        self._sort_descending = value

    # -- contract methods --------------------------------------------------------

    @property
    def fieldnames(self) -> list[str]:
        """All serialized attribute names."""
        return [
            "name",
            "csv_path",
            "website",
            "category",
            "created_at",
            "row_height",
            "tag_weights",
            "columns",
            "last_opened",
            "visible_columns",
            "column_order",
            "column_widths",
            "column_nicknames",
            "column_default_values",
            "sort_column",
            "sort_descending",
        ]

    def validate(self, context: object | None = None) -> ValidationResult:
        """Validate every project field against the spec bounds (B.3.1).

        Args:
            context: Unused; kept for the shared model contract.

        Returns:
            The accumulated validation issues (empty when everything is valid).
        """
        _ = context
        result = ValidationResult()
        self._validate_texts(result)
        if not C_ROW_HEIGHT_MIN <= self._row_height <= C_ROW_HEIGHT_MAX:
            context_data = {"minimum": C_ROW_HEIGHT_MIN, "maximum": C_ROW_HEIGHT_MAX}
            result.append(ErrorCodeProject.PRJ_1005, SeverityEnum.E_ERROR, context_data)
        if not self._primary_column:
            result.append(ErrorCodeProject.PRJ_1006, SeverityEnum.E_ERROR)
        self._validate_mapped_columns(result)
        if len(self._search_index_columns) < C_MIN_SEARCH_INDEX_COLUMNS:
            context_data = {"minimum": C_MIN_SEARCH_INDEX_COLUMNS}
            result.append(ErrorCodeProject.PRJ_1007, SeverityEnum.E_ERROR, context_data)
        if len(self._visible_columns) < C_MIN_VISIBLE_COLUMNS:
            context_data = {"minimum": C_MIN_VISIBLE_COLUMNS}
            result.append(ErrorCodeProject.PRJ_1008, SeverityEnum.E_ERROR, context_data)
        self._validate_weights(result)
        self._validate_column_default_values(result)
        return result

    def _validate_texts(self, result: ValidationResult) -> None:
        """Validate the free-text fields (path presence and 1..64 lengths)."""
        if not self._csv_path.strip():
            result.append(ErrorCodeProject.PRJ_1001, SeverityEnum.E_ERROR)
        checks = (
            (self._name, ErrorCodeProject.PRJ_1002),
            (self._website, ErrorCodeProject.PRJ_1003),
            (self._category, ErrorCodeProject.PRJ_1004),
        )
        for value, code in checks:
            if not C_TEXT_FIELD_MIN_LEN <= len(value.strip()) <= C_TEXT_FIELD_MAX_LEN:
                result.append(code, SeverityEnum.E_ERROR)

    def _validate_mapped_columns(self, result: ValidationResult) -> None:
        """Require the three rank source columns (they feed the __rank_* columns)."""
        checks = (
            (self._released_column, ErrorCodeProject.PRJ_1011),
            (self._popularity_column, ErrorCodeProject.PRJ_1012),
            (self._scoring_column, ErrorCodeProject.PRJ_1013),
        )
        for value, code in checks:
            if not value.strip():
                result.append(code, SeverityEnum.E_ERROR)

    def _validate_weights(self, result: ValidationResult) -> None:
        """Append an issue for every out-of-bounds tag weight."""
        for tag, weight in self._tag_weights.items():
            if not C_TAG_WEIGHT_MIN <= weight <= C_TAG_WEIGHT_MAX:
                context: dict[str, object] = {
                    "tag": tag,
                    "minimum": int(C_TAG_WEIGHT_MIN * 100),
                    "maximum": int(C_TAG_WEIGHT_MAX * 100),
                }
                result.append(ErrorCodeProject.PRJ_1009, SeverityEnum.E_ERROR, context)

    def _validate_column_default_values(self, result: ValidationResult) -> None:
        """Flag incomplete rows and columns assigned more than once (spec §4)."""
        columns_seen: dict[str, int] = {}
        for column, default_value in self._column_default_values:
            if not column or not default_value:
                result.append(ErrorCodeProject.PRJ_1015, SeverityEnum.E_ERROR)
                continue
            columns_seen[column] = columns_seen.get(column, 0) + 1
        for column, count in columns_seen.items():
            if count > 1:
                result.append(ErrorCodeProject.PRJ_1014, SeverityEnum.E_ERROR, {"column": column})
        if not self._column_default_values:
            result.append(ErrorCodeProject.PRJ_1016, SeverityEnum.E_WARNING)

    def to_dict(self) -> dict[str, object]:
        """Serialize the project to a JSON-compatible dictionary (spec shape)."""
        return {
            "name": self._name,
            "csv_path": self._csv_path,
            "website": self._website,
            "category": self._category,
            "created_at": self._created_at,
            "row_height": self._row_height,
            "tag_weights": dict(self._tag_weights),
            "columns": self._columns_to_dict(),
            "last_opened": self._last_opened,
            "visible_columns": list(self._visible_columns),
            "column_order": list(self._column_order),
            "column_widths": dict(self._column_widths),
            "column_nicknames": dict(self._column_nicknames),
            "column_default_values": [
                {"column": column, "default_value": default_value}
                for column, default_value in self._column_default_values
            ],
            "sort_column": self._sort_column,
            "sort_descending": self._sort_descending,
        }

    def _columns_to_dict(self) -> dict[str, object]:
        """Serialize the mapped-column block of `to_dict`."""
        return {
            "primary": self._primary_column,
            "released": self._released_column,
            "popularity": self._popularity_column,
            "scoring": self._scoring_column,
            "search_index": list(self._search_index_columns),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build an instance from a JSON dictionary, tolerating missing keys.

        Args:
            data: Raw dictionary read from the configuration file.

        Returns:
            A fully initialized instance (invalid fields fall back to defaults).
        """
        instance = cls()
        instance.name = _read_str(data, "name")
        instance.csv_path = _read_str(data, "csv_path")
        instance.website = _read_str(data, "website")
        instance.category = _read_str(data, "category")
        instance._created_at = _read_str(data, "created_at")
        instance.last_opened = _read_str(data, "last_opened")
        instance.row_height = safe_int_from_str(str(data.get("row_height", "")), C_ROW_HEIGHT_DEFAULT)
        instance._read_tag_weights(data)
        instance._read_columns(data)
        instance.visible_columns = _read_str_list(data, "visible_columns")
        instance.column_order = _read_str_list(data, "column_order")
        widths = as_str_object_dict(data.get("column_widths"))
        if widths is not None:
            instance.column_widths = {name: int(value) for name, value in widths.items() if isinstance(value, int)}
        nicknames = as_str_object_dict(data.get("column_nicknames"))
        if nicknames is not None:
            instance.column_nicknames = {
                name: value for name, value in nicknames.items() if isinstance(value, str) and value
            }
        instance.column_default_values = _read_column_default_values(data)
        instance.sort_column = _read_str(data, "sort_column")
        instance.sort_descending = bool(data.get("sort_descending"))
        return instance

    def _read_columns(self, data: dict[str, object]) -> None:
        """Read the nested `columns` mapping from a raw dictionary."""
        typed = as_str_object_dict(data.get("columns"))
        if typed is None:
            return
        self.primary_column = _read_str(typed, "primary")
        self.released_column = _read_str(typed, "released")
        self.popularity_column = _read_str(typed, "popularity")
        self.scoring_column = _read_str(typed, "scoring")
        self.search_index_columns = _read_str_list(typed, "search_index")

    def _read_tag_weights(self, data: dict[str, object]) -> None:
        """Read the `tag_weights` mapping from a raw dictionary, merging over the defaults."""
        weights = as_str_object_dict(data.get("tag_weights"))
        if weights is None:
            return
        merged = dict(C_DEFAULT_TAG_WEIGHTS)
        for key, value in weights.items():
            if isinstance(value, (int, float)) and key in merged:
                merged[key] = float(value)
        self.tag_weights = merged

    @classmethod
    def get_default(cls) -> Self:
        """Return a fully initialized default instance."""
        instance = cls()
        instance.mark_as_created()
        return instance

    def mark_as_created(self) -> None:
        """Stamp the creation and modification timestamps."""
        self._created_at = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        self._modified_at = self._created_at

    def mark_as_modified(self) -> None:
        """Stamp the modification timestamp."""
        self._modified_at = get_datetime_now_yyyy_mm_dd_hh_mm_ss()

    def copy(self, mode: CopyModeEnum) -> Self:
        """Duplicate the project.

        Args:
            mode: E_BUSINESS drops the identity; E_TECHNICAL clones it.

        Returns:
            The duplicated instance.
        """
        clone = type(self).from_dict(self.to_dict())
        clone._modified_at = self._modified_at
        if mode is not CopyModeEnum.E_BUSINESS:
            clone.id_project = self._id_project
        return clone

    def clear(self) -> None:
        """Reset the instance to its default state (identity included)."""
        fresh = type(self)()
        for key, value in vars(fresh).items():
            setattr(self, key, value)


# EOF
