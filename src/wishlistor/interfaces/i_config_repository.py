# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol

from wishlistor.models.app_config_model import AppConfigModel
from wishlistor.shared.validation_result import ValidationResult


class IConfigRepository(Protocol):
    """Read/write access to `./config-wishlistor.json` (the only config store)."""

    def load(self) -> tuple[AppConfigModel, ValidationResult]:
        """Load the configuration, falling back to defaults when corrupt.

        Returns:
            The configuration and the issues met while reading it.
        """
        ...

    def save(self, config: AppConfigModel) -> ValidationResult:
        """Persist the configuration atomically.

        Args:
            config: The configuration to write.

        Returns:
            The issues met while writing (empty on success).
        """
        ...

    def invalidate_cache(self) -> None:
        """Drop the in-memory cache so the next load re-reads the file."""
        ...


# EOF
