# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class TagEnum(Enum):
    """Enumerates the hardcoded, frozen set of row tags (spec B.4.3 / D.4)."""

    E_UNSET = "UNSET"
    E_FAVORIS = "Favoris"
    E_A_FAIRE = "A faire"
    E_EN_COURS = "En cours"
    E_TERMINE = "Terminé"
    E_ABANDONNE = "Abandonné"
    E_ARCHIVE = "Archivé"
    E_IGNORE = "Ignoré"
    E_UNKNOWN = "UNKNOWN"


# EOF
