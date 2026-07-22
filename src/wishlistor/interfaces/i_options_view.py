# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from wishlistor.interfaces.i_base_view import IBaseView
from wishlistor.models.view_state_model import OptionsViewState


class IOptionsView(IBaseView, Protocol):
    """Options module: application settings with inline validation."""

    def snapshot(self) -> OptionsViewState:
        """Return the current content of the options form."""
        ...

    def show_state(self, state: OptionsViewState, last_save_label: str) -> None:
        """Populate the options form.

        Args:
            state: Values to display.
            last_save_label: Display label of the last options save.
        """
        ...

    def set_last_save_label(self, label: str) -> None:
        """Refresh the last-save date label.

        Args:
            label: The new label.
        """
        ...

    def show_field_errors(self, errors: dict[str, str]) -> None:
        """Show inline, per-field validation feedback.

        Args:
            errors: Field name to French message mapping (empty clears all).
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

    def bind_options_edited(self, callback: Callable[[], None]) -> None:
        """Register the auto-save callback fired on every edit."""
        ...

    def bind_factory_reset_clicked(self, callback: Callable[[], None]) -> None:
        """Register the factory reset button callback."""
        ...


# EOF
