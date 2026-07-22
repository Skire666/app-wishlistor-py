# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol

from wishlistor.models.view_state_model import OptionsViewState, WindowGeometryState
from wishlistor.shared.validation_result import ValidationResult


class IOptionsService(Protocol):
    """Application options: reading, validated auto-save, factory reset."""

    def current_state(self) -> OptionsViewState:
        """Return the current options as a view state."""
        ...

    def last_saved_label(self) -> str:
        """Return the display label of the last options save date."""
        ...

    def update(self, state: OptionsViewState) -> tuple[ValidationResult, dict[str, str]]:
        """Validate then persist the options (atomic write on success).

        Args:
            state: Snapshot of the options form.

        Returns:
            The validation result and a field-name to message mapping.
        """
        ...

    def factory_reset(self) -> None:
        """Reset the whole configuration to defaults and persist it."""
        ...

    def save_window_geometry(self, geometry: WindowGeometryState) -> None:
        """Persist the main window geometry.

        Args:
            geometry: Size and position to remember.
        """
        ...


# EOF
