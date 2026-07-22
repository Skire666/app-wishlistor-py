# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class CopyModeEnum(Enum):
    """Enumerates the copy semantics of Model.copy() (AGENTS.md §13.2)."""

    E_UNSET = "UNSET"
    E_BUSINESS = "BUSINESS"  # functional copy, new identity
    E_TECHNICAL = "TECHNICAL"  # identical clone (same identity)
    E_UNKNOWN = "UNKNOWN"


# EOF
