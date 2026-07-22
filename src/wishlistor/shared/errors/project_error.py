# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from wishlistor.shared.errors.base_error_code import BaseErrorCode


class ErrorCodeProject(BaseErrorCode):
    """Error codes for project form validation and project management."""

    PRJ_1001 = "Le chemin est obligatoire et doit pointer vers un fichier CSV existant."
    PRJ_1002 = "Le nom du projet doit contenir entre 1 et 64 caractères."
    PRJ_1003 = "Le site web cible doit contenir entre 1 et 64 caractères."
    PRJ_1004 = "La catégorie du projet doit contenir entre 1 et 64 caractères."
    PRJ_1005 = "La hauteur de ligne doit être comprise entre {minimum} et {maximum} pixels."
    PRJ_1006 = "Choisissez une colonne de référence parmi les colonnes du CSV."
    PRJ_1007 = "Sélectionnez au moins {minimum} colonne(s) à indexer pour la recherche."
    PRJ_1008 = "Sélectionnez au moins {minimum} colonnes à afficher."
    PRJ_1009 = "Le poids du tag '{tag}' doit être compris entre {minimum}% et {maximum}%."
    PRJ_1010 = "Projet introuvable : {id}"
    PRJ_1011 = "La colonne date de publication est obligatoire (calcul de __rank_1_released__)."
    PRJ_1012 = "La colonne popularité est obligatoire (calcul de __rank_2_popularity__)."
    PRJ_1013 = "La colonne notation est obligatoire (calcul de __rank_3_notation100__)."
    PRJ_1014 = "La colonne '{column}' est sélectionnée plusieurs fois dans les valeurs par défaut."
    PRJ_1015 = "Chaque ligne de valeurs par défaut doit avoir une colonne et une valeur sélectionnées."
    PRJ_1016 = "Aucune valeur par défaut de colonne n'est configurée pour ce projet."
    PRJ_9999 = "Erreur inconnue lors de la gestion du projet."

    @staticmethod
    def try_simplify_exception(excp: Exception) -> ErrorCodeProject | None:
        """Map a raw exception to a known project error code, if possible.

        Args:
            excp: The exception raised by a lower layer.

        Returns:
            The matching error code, or None when no mapping exists.
        """
        _ = excp
        return None


# EOF
