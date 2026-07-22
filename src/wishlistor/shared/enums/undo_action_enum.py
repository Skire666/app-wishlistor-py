# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class UndoActionEnum(Enum):
    """Enumerates the kinds of undoable write actions (spec E)."""

    E_UNSET = "UNSET"
    E_CELL_EDIT = "CELL_EDIT"
    E_MASS_EDIT = "MASS_EDIT"
    E_ADD_ROW = "ADD_ROW"
    E_DELETE_ROWS = "DELETE_ROWS"
    E_UNKNOWN = "UNKNOWN"


# EOF
