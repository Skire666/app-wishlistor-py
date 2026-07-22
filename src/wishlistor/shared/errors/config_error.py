# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from wishlistor.shared.errors.base_error_code import BaseErrorCode
from wishlistor.shared.exceptions.file_access_error import FileAccessError


class ErrorCodeConfig(BaseErrorCode):
    """Error codes for application configuration handling."""

    CFG_1001 = "Configuration absente ou corrompue : valeurs par défaut restaurées."
    CFG_1002 = "Impossible d'écrire la configuration : {path}"
    CFG_1003 = "Le retour en arrière doit être compris entre {minimum} et {maximum}."
    CFG_1004 = "La taille de police doit être comprise entre {minimum} et {maximum}."
    CFG_1005 = "Le poids par défaut du tag '{tag}' doit être compris entre {minimum}% et {maximum}%."
    CFG_1006 = "Nom de colonne spéciale invalide : '{column}' (format attendu : __nom__)."
    CFG_1007 = "Le raccourci Ctrl+O référence un tag inconnu : '{tag}'."
    CFG_1008 = "Le raccourci Ctrl+N référence un tag inconnu : '{tag}'."
    CFG_1009 = "Le raccourci Ctrl+T référence un tag inconnu : '{tag}'."
    CFG_9999 = "Erreur inconnue lors de la gestion de la configuration."

    @staticmethod
    def try_simplify_exception(excp: Exception) -> ErrorCodeConfig | None:
        """Map a raw exception to a known configuration error code, if possible.

        Args:
            excp: The exception raised by a lower layer.

        Returns:
            The matching error code, or None when no mapping exists.
        """
        if isinstance(excp, FileAccessError):
            return ErrorCodeConfig.CFG_1002
        return None


# EOF
