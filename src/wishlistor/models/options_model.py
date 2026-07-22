"""Global application options (module Options), persisted in the config JSON."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Self

from wishlistor.shared.constants_util import (
    C_DEFAULT_SHORTCUT_N_TAGS,
    C_DEFAULT_SHORTCUT_O_TAGS,
    C_DEFAULT_SHORTCUT_T_TAGS,
    C_DEFAULT_SPECIAL_DISPLAY_COLUMNS,
    C_FONT_SIZE_DEFAULT,
    C_FONT_SIZE_MAX,
    C_FONT_SIZE_MIN,
    C_TAG_WEIGHT_MAX,
    C_TAG_WEIGHT_MIN,
    C_UNDO_DEFAULT,
    C_UNDO_MAX,
    C_UNDO_MIN,
)
from wishlistor.shared.enums.copy_mode_enum import CopyModeEnum
from wishlistor.shared.enums.severity_enum import SeverityEnum
from wishlistor.shared.errors.config_error import ErrorCodeConfig
from wishlistor.shared.tag_util import C_DEFAULT_TAG_WEIGHTS
from wishlistor.shared.typing.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from wishlistor.shared.typing.int_util import safe_int_from_str
from wishlistor.shared.typing.json_util import as_str_list, as_str_object_dict
from wishlistor.shared.validation_result import ValidationResult


class OptionsModel:
    """Application-level options with validation and JSON (de)serialization."""

    def __init__(self) -> None:
        """Initialize the options with their default values."""
        self._id_options: str = "options"
        self._undo_max: int = C_UNDO_DEFAULT
        self._default_tag_weights: dict[str, float] = dict(C_DEFAULT_TAG_WEIGHTS)
        self._special_display_columns: list[str] = list(C_DEFAULT_SPECIAL_DISPLAY_COLUMNS)
        self._theme: str = "dark"
        self._font_size: int = C_FONT_SIZE_DEFAULT
        self._shortcut_ctrl_o_tags: list[str] = list(C_DEFAULT_SHORTCUT_O_TAGS)
        self._shortcut_ctrl_n_tags: list[str] = list(C_DEFAULT_SHORTCUT_N_TAGS)
        self._shortcut_ctrl_t_tags: list[str] = list(C_DEFAULT_SHORTCUT_T_TAGS)
        self._created_at: str = ""
        self._modified_at: str = ""

    # -- identity and simple properties ---------------------------------------

    @property
    def id_options(self) -> str:
        """Unique identifier of the options singleton entry."""
        return self._id_options

    @property
    def undo_max(self) -> int:
        """Maximum number of undo steps (1..30)."""
        return self._undo_max

    @undo_max.setter
    def undo_max(self, value: int) -> None:
        """Set the maximum number of undo steps."""
        self._undo_max = value

    @property
    def default_tag_weights(self) -> dict[str, float]:
        """Default tag weights (fraction of N) used to pre-fill project forms."""
        return self._default_tag_weights

    @default_tag_weights.setter
    def default_tag_weights(self, value: dict[str, float]) -> None:
        """Set the default tag weights."""
        self._default_tag_weights = dict(value)

    @property
    def special_display_columns(self) -> list[str]:
        """Special columns offered in the display pickers."""
        return self._special_display_columns

    @special_display_columns.setter
    def special_display_columns(self, value: list[str]) -> None:
        """Set the special display columns."""
        self._special_display_columns = list(value)

    @property
    def theme(self) -> str:
        """UI theme name (only 'dark' is shipped)."""
        return self._theme

    @theme.setter
    def theme(self, value: str) -> None:
        """Set the UI theme name."""
        self._theme = value

    @property
    def font_size(self) -> int:
        """Application font size in points."""
        return self._font_size

    @font_size.setter
    def font_size(self, value: int) -> None:
        """Set the application font size."""
        self._font_size = value

    @property
    def shortcut_ctrl_o_tags(self) -> list[str]:
        """Tag labels checked by Ctrl+O on the current row."""
        return self._shortcut_ctrl_o_tags

    @shortcut_ctrl_o_tags.setter
    def shortcut_ctrl_o_tags(self, value: list[str]) -> None:
        """Set the Ctrl+O tag labels."""
        self._shortcut_ctrl_o_tags = list(value)

    @property
    def shortcut_ctrl_n_tags(self) -> list[str]:
        """Tag labels checked by Ctrl+N on the current row."""
        return self._shortcut_ctrl_n_tags

    @shortcut_ctrl_n_tags.setter
    def shortcut_ctrl_n_tags(self, value: list[str]) -> None:
        """Set the Ctrl+N tag labels."""
        self._shortcut_ctrl_n_tags = list(value)

    @property
    def shortcut_ctrl_t_tags(self) -> list[str]:
        """Tag labels checked by Ctrl+T on the current row."""
        return self._shortcut_ctrl_t_tags

    @shortcut_ctrl_t_tags.setter
    def shortcut_ctrl_t_tags(self, value: list[str]) -> None:
        """Set the Ctrl+T tag labels."""
        self._shortcut_ctrl_t_tags = list(value)

    @property
    def created_at(self) -> str:
        """Creation timestamp (ISO string)."""
        return self._created_at

    @property
    def modified_at(self) -> str:
        """Last modification timestamp (ISO string)."""
        return self._modified_at

    # -- contract methods ------------------------------------------------------

    @property
    def fieldnames(self) -> list[str]:
        """All serialized attribute names."""
        return [
            "undo_max",
            "default_tag_weights",
            "special_display_columns",
            "theme",
            "font_size",
            "shortcut_ctrl_o_tags",
            "shortcut_ctrl_n_tags",
            "shortcut_ctrl_t_tags",
        ]

    def validate(self, context: object | None = None) -> ValidationResult:
        """Validate bounds of every option value.

        Args:
            context: Unused; kept for the shared model contract.

        Returns:
            The accumulated validation issues (empty when everything is valid).
        """
        _ = context
        result = ValidationResult()
        if not C_UNDO_MIN <= self._undo_max <= C_UNDO_MAX:
            result.append(
                ErrorCodeConfig.CFG_1003, SeverityEnum.E_ERROR, {"minimum": C_UNDO_MIN, "maximum": C_UNDO_MAX}
            )
        if not C_FONT_SIZE_MIN <= self._font_size <= C_FONT_SIZE_MAX:
            result.append(
                ErrorCodeConfig.CFG_1004,
                SeverityEnum.E_ERROR,
                {"minimum": C_FONT_SIZE_MIN, "maximum": C_FONT_SIZE_MAX},
            )
        self._validate_weights(result)
        self._validate_shortcuts(result)
        return result

    def _validate_shortcuts(self, result: ValidationResult) -> None:
        """Reject shortcut tag labels that are not part of the frozen tag set."""
        checks = (
            (self._shortcut_ctrl_o_tags, ErrorCodeConfig.CFG_1007),
            (self._shortcut_ctrl_n_tags, ErrorCodeConfig.CFG_1008),
            (self._shortcut_ctrl_t_tags, ErrorCodeConfig.CFG_1009),
        )
        for labels, code in checks:
            for label in labels:
                if label not in C_DEFAULT_TAG_WEIGHTS:
                    result.append(code, SeverityEnum.E_ERROR, {"tag": label})

    def _validate_weights(self, result: ValidationResult) -> None:
        """Append an issue for every out-of-bounds tag weight."""
        for tag, weight in self._default_tag_weights.items():
            if not C_TAG_WEIGHT_MIN <= weight <= C_TAG_WEIGHT_MAX:
                context: dict[str, object] = {
                    "tag": tag,
                    "minimum": int(C_TAG_WEIGHT_MIN * 100),
                    "maximum": int(C_TAG_WEIGHT_MAX * 100),
                }
                result.append(ErrorCodeConfig.CFG_1005, SeverityEnum.E_ERROR, context)

    def to_dict(self) -> dict[str, object]:
        """Serialize the options to a JSON-compatible dictionary."""
        return {
            "undo_max": self._undo_max,
            "default_tag_weights": dict(self._default_tag_weights),
            "special_display_columns": list(self._special_display_columns),
            "theme": self._theme,
            "font_size": self._font_size,
            "shortcut_ctrl_o_tags": list(self._shortcut_ctrl_o_tags),
            "shortcut_ctrl_n_tags": list(self._shortcut_ctrl_n_tags),
            "shortcut_ctrl_t_tags": list(self._shortcut_ctrl_t_tags),
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
        instance.undo_max = safe_int_from_str(str(data.get("undo_max", "")), C_UNDO_DEFAULT)
        instance.font_size = safe_int_from_str(str(data.get("font_size", "")), C_FONT_SIZE_DEFAULT)
        theme = data.get("theme")
        if isinstance(theme, str) and theme:
            instance.theme = theme
        weights = as_str_object_dict(data.get("default_tag_weights"))
        if weights is not None:
            merged = dict(C_DEFAULT_TAG_WEIGHTS)
            for key, value in weights.items():
                if isinstance(value, (int, float)) and key in merged:
                    merged[key] = float(value)
            instance.default_tag_weights = merged
        columns = data.get("special_display_columns")
        if columns is not None:
            instance.special_display_columns = as_str_list(columns)
        cls._apply_shortcut_tags(instance, data)
        return instance

    @staticmethod
    def _apply_shortcut_tags(instance: OptionsModel, data: dict[str, object]) -> None:
        """Restore the shortcut tag labels present in *data*, tolerating missing keys."""
        fields = ("shortcut_ctrl_o_tags", "shortcut_ctrl_n_tags", "shortcut_ctrl_t_tags")
        for field in fields:
            value = data.get(field)
            if value is not None:
                setattr(instance, field, as_str_list(value))

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
        """Duplicate the options.

        Args:
            mode: E_BUSINESS or E_TECHNICAL (identical here: options have a fixed identity).

        Returns:
            The duplicated instance.
        """
        _ = mode
        clone = type(self).from_dict(self.to_dict())
        clone._created_at = self._created_at
        clone._modified_at = self._modified_at
        return clone

    def clear(self) -> None:
        """Reset the instance to its default state."""
        fresh = type(self)()
        self._undo_max = fresh.undo_max
        self._default_tag_weights = dict(fresh.default_tag_weights)
        self._special_display_columns = list(fresh.special_display_columns)
        self._theme = fresh.theme
        self._font_size = fresh.font_size
        self._shortcut_ctrl_o_tags = list(fresh.shortcut_ctrl_o_tags)
        self._shortcut_ctrl_n_tags = list(fresh.shortcut_ctrl_n_tags)
        self._shortcut_ctrl_t_tags = list(fresh.shortcut_ctrl_t_tags)


# EOF
