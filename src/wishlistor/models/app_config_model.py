"""Model of `./config-wishlistor.json` (options, window, projects). Singleton."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Self

from wishlistor.models.options_model import OptionsModel
from wishlistor.models.project_collection_model import ProjectCollectionModel
from wishlistor.models.view_state_model import WindowGeometryState
from wishlistor.shared.constants_util import C_WINDOW_DEFAULT_HEIGHT, C_WINDOW_DEFAULT_WIDTH
from wishlistor.shared.enums.copy_mode_enum import CopyModeEnum
from wishlistor.shared.typing.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from wishlistor.shared.typing.int_util import safe_int_from_str
from wishlistor.shared.typing.json_util import as_str_object_dict
from wishlistor.shared.validation_result import ValidationResult


class AppConfigModel:
    """Whole application configuration, exposed as the single tolerated singleton."""

    _instance: AppConfigModel | None = None

    def __init__(self) -> None:
        """Initialize the configuration with default values."""
        self._id_config: str = "config"
        self._options: OptionsModel = OptionsModel()
        self._projects: ProjectCollectionModel = ProjectCollectionModel()
        self._window: WindowGeometryState = WindowGeometryState(
            width=C_WINDOW_DEFAULT_WIDTH, height=C_WINDOW_DEFAULT_HEIGHT, x=100, y=100
        )
        self._project_table_column_widths: dict[str, int] = {}
        self._created_at: str = ""
        self._modified_at: str = ""

    # -- singleton access ---------------------------------------------------------

    @classmethod
    def get_instance(cls) -> AppConfigModel:
        """Return the shared instance, creating a default one on first call."""
        if cls._instance is None:
            cls._instance = cls.get_default()
        return cls._instance

    @classmethod
    def set_instance(cls, instance: AppConfigModel) -> None:
        """Install the shared instance (composition root only).

        Args:
            instance: The configuration instance to share.
        """
        cls._instance = instance

    # -- properties -----------------------------------------------------------------

    @property
    def id_config(self) -> str:
        """Unique identifier of the configuration."""
        return self._id_config

    @property
    def options(self) -> OptionsModel:
        """Application options."""
        return self._options

    @options.setter
    def options(self, value: OptionsModel) -> None:
        """Set the application options."""
        self._options = value

    @property
    def projects(self) -> ProjectCollectionModel:
        """Project collection."""
        return self._projects

    @projects.setter
    def projects(self, value: ProjectCollectionModel) -> None:
        """Set the project collection."""
        self._projects = value

    @property
    def window(self) -> WindowGeometryState:
        """Persisted main window geometry."""
        return self._window

    @window.setter
    def window(self, value: WindowGeometryState) -> None:
        """Set the persisted main window geometry."""
        self._window = value

    @property
    def project_table_column_widths(self) -> dict[str, int]:
        """Persisted column widths of the project history table."""
        return self._project_table_column_widths

    @project_table_column_widths.setter
    def project_table_column_widths(self, value: dict[str, int]) -> None:
        """Set the persisted column widths of the project history table."""
        self._project_table_column_widths = dict(value)

    # -- contract methods --------------------------------------------------------------

    @property
    def fieldnames(self) -> list[str]:
        """All serialized attribute names."""
        return ["options", "window", "project_table_column_widths", "recent_projects", "projects"]

    def validate(self, context: object | None = None) -> ValidationResult:
        """Validate the options and every project.

        Args:
            context: Forwarded to nested validations.

        Returns:
            The accumulated validation issues.
        """
        result = self._options.validate(context)
        result.extend(self._projects.validate(context))
        return result

    def to_dict(self) -> dict[str, object]:
        """Serialize the whole configuration to a JSON-compatible dictionary."""
        window: dict[str, object] = {
            "width": self._window.width,
            "height": self._window.height,
            "x": self._window.x,
            "y": self._window.y,
            "maximized": self._window.is_maximized,
        }
        return {
            "options": self._options.to_dict(),
            "window": window,
            "project_table_column_widths": dict(self._project_table_column_widths),
            **self._projects.serialize(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        """Build a configuration from raw JSON data, tolerating corruption.

        Args:
            data: Raw dictionary read from the configuration file.

        Returns:
            A fully initialized configuration.
        """
        instance = cls()
        raw_options = as_str_object_dict(data.get("options"))
        if raw_options is not None:
            instance.options = OptionsModel.from_dict(raw_options)
        instance.projects = ProjectCollectionModel.deserialize(data)
        raw_window = as_str_object_dict(data.get("window"))
        if raw_window is not None:
            instance.window = WindowGeometryState(
                width=safe_int_from_str(str(raw_window.get("width", "")), C_WINDOW_DEFAULT_WIDTH),
                height=safe_int_from_str(str(raw_window.get("height", "")), C_WINDOW_DEFAULT_HEIGHT),
                x=safe_int_from_str(str(raw_window.get("x", "")), 100),
                y=safe_int_from_str(str(raw_window.get("y", "")), 100),
                is_maximized=raw_window.get("maximized") is True,
            )
        raw_widths = as_str_object_dict(data.get("project_table_column_widths"))
        if raw_widths is not None:
            instance.project_table_column_widths = {
                name: int(value) for name, value in raw_widths.items() if isinstance(value, int)
            }
        return instance

    @classmethod
    def get_default(cls) -> Self:
        """Return a fully initialized default configuration."""
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
        """Duplicate the configuration.

        Args:
            mode: Copy semantics forwarded to nested models.

        Returns:
            The duplicated configuration.
        """
        clone = type(self)()
        clone.options = self._options.copy(mode)
        clone.projects = self._projects.copy(mode)
        clone.window = self._window
        clone.project_table_column_widths = dict(self._project_table_column_widths)
        return clone

    def clear(self) -> None:
        """Reset everything to factory defaults (projects history included)."""
        self._options.clear()
        self._projects.clear()
        self._window = WindowGeometryState(
            width=C_WINDOW_DEFAULT_WIDTH, height=C_WINDOW_DEFAULT_HEIGHT, x=100, y=100
        )
        self._project_table_column_widths = {}
        self.mark_as_modified()


# EOF
