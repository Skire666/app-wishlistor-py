# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class BaseErrorCode(Enum):
    """Common base for every ErrorCode enum (see shared/errors/)."""

    def __str__(self) -> str:
        """Return a textual representation of the ErrorCode."""
        return f"#{self.name}"


# EOF
