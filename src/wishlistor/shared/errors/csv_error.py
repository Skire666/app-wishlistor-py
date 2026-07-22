# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from wishlistor.shared.errors.base_error_code import BaseErrorCode
from wishlistor.shared.exceptions.file_access_error import FileAccessError


class ErrorCodeCsv(BaseErrorCode):
    """Error codes for CSV loading, validation and saving."""

    # file access / structure
    CSV_1001 = "Le fichier CSV est introuvable ou illisible : {path}"
    CSV_1002 = "Le CSV est vide ou sans en-tête exploitable."
    CSV_1003 = "L'en-tête contient des noms de colonnes dupliqués ou vides : {columns}"
    CSV_1004 = "Colonne spéciale inconnue du glossaire : {column}"
    # reference column
    CSV_1005 = "La colonne de référence '{column}' n'existe pas dans le CSV."
    CSV_1006 = "La colonne de référence contient des doublons (lignes : {lines})."
    CSV_1007 = "La colonne de référence contient des valeurs vides (lignes : {lines})."
    # content anomalies
    CSV_1008 = "Ligne {line} : longueur incohérente ({found} champs pour {expected} attendus)."
    CSV_1009 = "Ligne {line} : la colonne '{column}' n'est pas une date ISO valide ('{value}')."
    CSV_1010 = "Ligne {line} : tag invalide ou en conflit supprimé de '__custom_tags__' : {segments}"
    CSV_1011 = "{count} valeur(s) manquante(s) substituée(s) dans la colonne '{column}'."
    CSV_1015 = "La colonne '{column}' est recalculée par l'application (valeurs du fichier ignorées)."
    CSV_1017 = "Colonne mappée '{column}' absente ou non définie : configuration du projet à compléter."
    # save
    CSV_1012 = "Le fichier a été modifié ou supprimé en dehors de l'application."
    CSV_1013 = "Impossible d'écrire le fichier (verrouillé ou permissions insuffisantes) : {path}"
    CSV_1014 = "Le fichier dépasse 100 Mo ({size}) : le chargement complet peut être long."
    # csv module
    CSV_1016 = "Cette valeur existe déjà dans la colonne de référence."
    CSV_1018 = "Le dossier n'existe pas ou n'est pas accessible : {path}"
    CSV_9999 = "Erreur inconnue lors du traitement du CSV."

    @staticmethod
    def try_simplify_exception(excp: Exception) -> ErrorCodeCsv | None:
        """Map a raw exception to a known CSV error code, if possible.

        Args:
            excp: The exception raised by a lower layer.

        Returns:
            The matching error code, or None when no mapping exists.
        """
        if isinstance(excp, FileAccessError):
            return ErrorCodeCsv.CSV_1001
        if isinstance(excp, OSError):
            return ErrorCodeCsv.CSV_1013
        return None


# EOF
