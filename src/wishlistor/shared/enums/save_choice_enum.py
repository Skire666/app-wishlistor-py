# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class SaveChoiceEnum(Enum):
    """Enumerates user answers to save-related confirmation dialogs (spec F / D.5)."""

    E_UNSET = "UNSET"
    E_SAVE = "SAVE"
    E_SAVE_AS = "SAVE_AS"
    E_OVERWRITE = "OVERWRITE"
    E_DISCARD = "DISCARD"
    E_CANCEL = "CANCEL"
    E_UNKNOWN = "UNKNOWN"


# EOF
