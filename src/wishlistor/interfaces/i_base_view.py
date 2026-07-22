# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol

from wishlistor.shared.validation_result import ValidationResult


class IBaseView(Protocol):
    """Contract shared by every View (AGENTS §13.4)."""

    @property
    def is_dirty(self) -> bool:
        """True when the user made a data-changing edit."""
        ...

    @property
    def is_busy(self) -> bool:
        """True while a background operation blocks the view."""
        ...

    @property
    def is_loading(self) -> bool:
        """True while the view is building or loading itself."""
        ...

    def set_enabled(self, enabled: bool) -> None:
        """Grey out or re-enable the component.

        Args:
            enabled: The new enabled state.
        """
        ...

    def notify_error(self, rs: ValidationResult) -> None:
        """Surface a validation result to the user.

        Args:
            rs: The issues to display.
        """
        ...

    def clear(self) -> None:
        """Empty the in-memory GUI values."""
        ...

    def notify_refresh(self, context: object) -> None:
        """Refresh the UI according to the given context.

        Args:
            context: Presenter-defined refresh payload.
        """
        ...


# EOF
