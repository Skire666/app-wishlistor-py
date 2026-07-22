# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class ModuleEnum(Enum):
    """Enumerates the main application modules reachable from the sidebar."""

    E_UNSET = "UNSET"
    E_PROJECT = "PROJECT"
    E_CSV = "CSV"
    E_JOURNAL = "JOURNAL"
    E_OPTIONS = "OPTIONS"
    E_UNKNOWN = "UNKNOWN"


# EOF
