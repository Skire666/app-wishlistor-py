"""Application options business logic: validated auto-save, factory reset."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import uuid

from wishlistor.interfaces.i_config_repository import IConfigRepository
from wishlistor.models.app_config_model import AppConfigModel
from wishlistor.models.options_model import OptionsModel
from wishlistor.models.view_state_model import OptionsViewState, WindowGeometryState
from wishlistor.shared.errors.config_error import ErrorCodeConfig
from wishlistor.shared.i18n_fra import COMMON_EMPTY_VALUE
from wishlistor.shared.typing.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from wishlistor.shared.validation_result import ValidationResult

# Maps configuration error codes to the form field carrying the inline feedback.
_FIELD_BY_CODE: dict[ErrorCodeConfig, str] = {
    ErrorCodeConfig.CFG_1003: "undo_max",
    ErrorCodeConfig.CFG_1004: "font_size",
    ErrorCodeConfig.CFG_1005: "default_tag_weights",
    ErrorCodeConfig.CFG_1006: "special_display_columns",
    ErrorCodeConfig.CFG_1007: "shortcut_ctrl_o_tags",
    ErrorCodeConfig.CFG_1008: "shortcut_ctrl_n_tags",
    ErrorCodeConfig.CFG_1009: "shortcut_ctrl_t_tags",
}


class OptionsService:
    """Reads and persists the application options."""

    def __init__(self, config_repository: IConfigRepository, config: AppConfigModel) -> None:
        """Initialize the service.

        Args:
            config_repository: Configuration persistence.
            config: The shared configuration model.
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config_repository = config_repository
        self._config = config
        self._last_saved_label: str = COMMON_EMPTY_VALUE

    @staticmethod
    def generate_id() -> str:
        """Return a new unique identifier for an options save batch."""
        return str(uuid.uuid4())

    def current_state(self) -> OptionsViewState:
        """Return the current options as a view state."""
        options = self._config.options
        return OptionsViewState(
            undo_max=options.undo_max,
            default_tag_weights=dict(options.default_tag_weights),
            special_display_columns=tuple(options.special_display_columns),
            font_size=options.font_size,
            shortcut_ctrl_o_tags=tuple(options.shortcut_ctrl_o_tags),
            shortcut_ctrl_n_tags=tuple(options.shortcut_ctrl_n_tags),
            shortcut_ctrl_t_tags=tuple(options.shortcut_ctrl_t_tags),
        )

    def last_saved_label(self) -> str:
        """Return the display label of the last options save date."""
        return self._last_saved_label

    def update(self, state: OptionsViewState) -> tuple[ValidationResult, dict[str, str]]:
        """Validate then persist the options (atomic write on success).

        Args:
            state: Snapshot of the options form.

        Returns:
            The validation result and a field-name to message mapping.
        """
        candidate = OptionsModel()
        candidate.undo_max = state.undo_max
        candidate.default_tag_weights = dict(state.default_tag_weights)
        candidate.special_display_columns = list(state.special_display_columns)
        candidate.theme = self._config.options.theme
        candidate.font_size = state.font_size
        candidate.shortcut_ctrl_o_tags = list(state.shortcut_ctrl_o_tags)
        candidate.shortcut_ctrl_n_tags = list(state.shortcut_ctrl_n_tags)
        candidate.shortcut_ctrl_t_tags = list(state.shortcut_ctrl_t_tags)
        result = candidate.validate()
        field_errors = self._map_field_errors(result)
        if result.has_errors_or_fatals():
            return result, field_errors
        candidate.mark_as_modified()
        self._config.options = candidate
        self._config.mark_as_modified()
        self._config_repository.save(self._config)
        self._last_saved_label = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        self._logger.info("Options sauvegardées.")
        return result, field_errors

    @staticmethod
    def _map_field_errors(result: ValidationResult) -> dict[str, str]:
        """Build the field-name to first-message mapping for inline display."""
        field_errors: dict[str, str] = {}
        for issue in result.issues:
            code = issue.code
            if isinstance(code, ErrorCodeConfig):
                field = _FIELD_BY_CODE.get(code, "")
                if field and field not in field_errors:
                    field_errors[field] = issue.message
        return field_errors

    def factory_reset(self) -> None:
        """Reset the whole configuration to defaults and persist it."""
        self._config.clear()
        self._config_repository.save(self._config)
        self._last_saved_label = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        self._logger.warning("Configuration remise aux réglages d'usine.")

    def save_window_geometry(self, geometry: WindowGeometryState) -> None:
        """Persist the main window geometry.

        Args:
            geometry: Size and position to remember.
        """
        self._config.window = geometry
        self._config.mark_as_modified()
        self._config_repository.save(self._config)


# EOF
