"""French user-facing strings. The single source of display text (AGENTS.md §6).

Templates use ``str.format`` placeholders; callers format them with named args.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Final

from wishlistor.shared.enums.default_value_enum import DefaultValueEnum

# -----------------------------------------------------------------------------
# Application / sidebar
# -----------------------------------------------------------------------------

APP_TITLE: Final[str] = "Wishlistor"
SIDEBAR_PROJECT: Final[str] = "Projet"
SIDEBAR_CSV: Final[str] = "CSV"
SIDEBAR_JOURNAL: Final[str] = "Journal"
SIDEBAR_OPTIONS: Final[str] = "Options"

# -----------------------------------------------------------------------------
# Common
# -----------------------------------------------------------------------------

COMMON_YES: Final[str] = "Oui"
COMMON_NO: Final[str] = "Non"
COMMON_EMPTY_VALUE: Final[str] = "--"
COMMON_CANCEL: Final[str] = "Annuler"
COMMON_SAVE: Final[str] = "Sauvegarder (Ctrl+S)"
COMMON_SAVE_AS: Final[str] = "Enregistrer sous…"
COMMON_OVERWRITE: Final[str] = "Écraser"
COMMON_QUIT_WITHOUT_SAVING: Final[str] = "Continuer sans sauvegarder"
COMMON_MOVE_UP: Final[str] = "▲"
COMMON_MOVE_DOWN: Final[str] = "▼"
COMMON_MOVE_UP_TOOLTIP: Final[str] = "Déplacer vers le haut"
COMMON_MOVE_DOWN_TOOLTIP: Final[str] = "Déplacer vers le bas"
COMMON_BROWSE: Final[str] = "..."
COMMON_LOADING: Final[str] = "Opération en cours…"
COMMON_COPY: Final[str] = "Copier"
COMMON_COLUMN_SELECT_HEADER: Final[str] = "Sél."
COMMON_COLUMN_NAME_HEADER: Final[str] = "Nom CSV"
COMMON_COLUMN_NICKNAME_HEADER: Final[str] = "Surnom"

# -----------------------------------------------------------------------------
# Project module
# -----------------------------------------------------------------------------

PROJECT_TITLE: Final[str] = "Liste des projets"
PROJECT_CREATE_BUTTON: Final[str] = "Créer un projet"
PROJECT_COL_NAME: Final[str] = "Nom du projet"
PROJECT_COL_WEBSITE: Final[str] = "Site web cible"
PROJECT_COL_CATEGORY: Final[str] = "Catégorie du projet"
PROJECT_COL_CSV_PATH: Final[str] = "Chemin du CSV"
PROJECT_COL_LAST_OPENED: Final[str] = "Date de dernière ouverture"
PROJECT_COL_FILE_SIZE: Final[str] = "Taille du fichier"
PROJECT_COL_AVAILABLE: Final[str] = "Disponible ?"
PROJECT_COL_ACTION: Final[str] = "Action"
PROJECT_DELETE_BUTTON: Final[str] = "Effacer"
PROJECT_ROW_COUNT: Final[str] = "{count} projet(s) disponible(s)"
PROJECT_FILE_MISSING: Final[str] = "Fichier introuvable"
PROJECT_DELETE_CONFIRM_TITLE: Final[str] = "Effacer le projet"
PROJECT_DELETE_CONFIRM_MESSAGE: Final[str] = "Effacer définitivement le projet « {name} » de l'historique ?"

# -----------------------------------------------------------------------------
# Project form
# -----------------------------------------------------------------------------

FORM_TITLE_CREATE: Final[str] = "Créer un projet"
FORM_TITLE_EDIT: Final[str] = "Options du projet"
FORM_GROUP_INFO: Final[str] = "Informations"
FORM_GROUP_TAGS: Final[str] = "Tags"
FORM_GROUP_COLUMNS: Final[str] = "Colonnes"
FORM_GROUP_DISPLAY: Final[str] = "Affichage"
FORM_GROUP_DEFAULT_VALUES: Final[str] = "Valeurs par défaut des colonnes"
FORM_FIELD_CSV_PATH: Final[str] = "Chemin vers le CSV"
FORM_FIELD_NAME: Final[str] = "Nom du projet"
FORM_FIELD_WEBSITE: Final[str] = "Site web cible"
FORM_FIELD_CATEGORY: Final[str] = "Catégorie du projet"
FORM_FIELD_CREATED_AT: Final[str] = "Date de création"
FORM_FIELD_ROW_HEIGHT: Final[str] = "Hauteur de ligne (px)"
FORM_FIELD_TAG_WEIGHTS: Final[str] = "Poids des tags (%)"
FORM_FIELD_PRIMARY: Final[str] = "Colonne de référence"
FORM_FIELD_RELEASED: Final[str] = "Date de publication"
FORM_FIELD_POPULARITY: Final[str] = "Popularité"
FORM_FIELD_SCORING: Final[str] = "Notation"
FORM_FIELD_SEARCH_INDEX: Final[str] = "Colonnes à indexer pour la recherche"
FORM_COLUMNS_ALL_DEFAULT: Final[str] = (
    "Ces colonnnes seront toutes avec des valeurs par défaut :\nPublication 1900... + Popularité 0 + Notation 0"
)
FORM_SUBMIT_CREATE: Final[str] = "Créer"
FORM_SUBMIT_VALIDATE: Final[str] = "Valider"
FORM_NO_SELECTION: Final[str] = "(aucune)"
FORM_DEFAULT_VALUES_COL_COLUMN: Final[str] = "Colonne"
FORM_DEFAULT_VALUES_COL_VALUE: Final[str] = "Valeur par défaut"
FORM_DEFAULT_VALUES_ADD: Final[str] = "+ Ajouter"
FORM_DEFAULT_VALUES_REMOVE: Final[str] = "Supprimer"
FORM_DEFAULT_VALUES_REMOVE_ICON: Final[str] = "✕"
FORM_DEFAULT_VALUE_LABELS: Final[dict[DefaultValueEnum, str]] = {
    DefaultValueEnum.E_DATE_1900: "Date 1900-01-01 (CSV)",
    DefaultValueEnum.E_DATE_TODAY: "Date du jour (CSV)",
    DefaultValueEnum.E_COUNT_ZERO: "0 (nombre)",
    DefaultValueEnum.E_TOTAL_ROW_COUNT: "Nombre total de lignes",
    DefaultValueEnum.E_EXTRACTOR_E0: 'Enum "e0"',
}

# -----------------------------------------------------------------------------
# CSV module
# -----------------------------------------------------------------------------

CSV_TITLE: Final[str] = "Gestion du CSV"
CSV_OPEN_FOLDER: Final[str] = "Ouvrir dossier"
CSV_PROJECT_OPTIONS: Final[str] = "Options du projet"
CSV_NO_PROJECT: Final[str] = "Aucun projet ouvert. Ouvrez ou créez un projet depuis le module Projet."
CSV_FILTER_EMPTY_TAGS: Final[str] = "Tags vide"
CSV_FILTER_BUTTON: Final[str] = "Filtrer"
CSV_FILTER_CLEAR: Final[str] = "Effacer"
CSV_FILTER_COUNT: Final[str] = "{count} trouvé(s)"
CSV_SEARCH_PLACEHOLDER: Final[str] = "Recherche…"
CSV_SEARCH_PREVIOUS: Final[str] = "Précédent"
CSV_SEARCH_NEXT: Final[str] = "Suivant"
CSV_SEARCH_NO_RESULT: Final[str] = "0 trouvé"
CSV_SEARCH_COUNTER: Final[str] = "{index} / {total}"
CSV_URL_PLACEHOLDER: Final[str] = "URL à ajouter"
CSV_URL_ADD_BUTTON: Final[str] = "Ajouter l'URL"
CSV_URL_ALREADY_PRESENT: Final[str] = "Déjà présent"
CSV_URL_ADDED: Final[str] = "Ajouté"
CSV_EDIT_TAGS_BUTTON: Final[str] = "Modifier les tags"
CSV_EDIT_COMMENT_BUTTON: Final[str] = "Modifier le commentaire"
CSV_DELETE_ROW_BUTTON: Final[str] = "Supprimer la ligne"
CSV_SELECTED_COUNT: Final[str] = "Sélectionné : {count}"
CSV_SELECT_ALL: Final[str] = "Tout sélectionner"
CSV_INVERT_SELECTION: Final[str] = "Inverser la sélection"
CSV_DESELECT_ALL: Final[str] = "Dé-sélectionner"
CSV_DELETE_ROW_TOOLTIP: Final[str] = "Supprimer cette ligne"
CSV_MANAGE_COLUMNS: Final[str] = "Gestion des colonnes"
CSV_TOTAL_ROWS: Final[str] = "Lignes totales : {count}"
CSV_SHOWN_ROWS: Final[str] = "Affichées : {count}"
CSV_FILE_MTIME: Final[str] = "Modifié le : {mtime}"
CSV_LAST_SAVE: Final[str] = "Dernière sauvegarde"
CSV_COMMENT_PROMPT: Final[str] = "Nouveau commentaire pour les lignes sélectionnées :"
CSV_INVALID_IMAGE: Final[str] = "image invalide"
CSV_SELECTION_HEADER: Final[str] = "Sélection"
CSV_UNSAVED_TITLE: Final[str] = "Modifications non sauvegardées"
CSV_UNSAVED_MESSAGE: Final[str] = "Des modifications ne sont pas sauvegardées. Que voulez-vous faire ?"
CSV_CONFLICT_TITLE: Final[str] = "Fichier modifié en dehors de l'application"
CSV_CONFLICT_MESSAGE: Final[str] = (
    "Le fichier CSV a été modifié ou supprimé depuis son chargement. Écraser le fichier, "
    "enregistrer sous un nouvel emplacement, ou annuler ?"
)
CSV_CRITICAL_TITLE: Final[str] = "Erreur critique"
CSV_SAVE_DIALOG_TITLE: Final[str] = "Enregistrer le CSV sous…"
CSV_OPEN_DIALOG_TITLE: Final[str] = "Choisir un fichier CSV"
CSV_FILE_DIALOG_FILTER: Final[str] = "Fichiers CSV (*.csv);;Tous les fichiers (*.*)"
CSV_DELETE_CONFIRM_TITLE: Final[str] = "Supprimer les lignes"
CSV_DELETE_CONFIRM_MESSAGE: Final[str] = "Supprimer définitivement {count} ligne(s) du tableau ?"

# -----------------------------------------------------------------------------
# Journal module
# -----------------------------------------------------------------------------

JOURNAL_TITLE: Final[str] = "Journalisation des événements"
JOURNAL_OPEN_LOG_FOLDER: Final[str] = "Ouvrir le dossier des logs"
JOURNAL_CLEAR_BUTTON: Final[str] = "Vider l'affichage"
JOURNAL_COL_DATE: Final[str] = "Date"
JOURNAL_COL_LEVEL: Final[str] = "Niveau de logs"
JOURNAL_COL_SOURCE: Final[str] = "Source"
JOURNAL_COL_MESSAGE: Final[str] = "Message"
JOURNAL_LEVEL_COUNT: Final[str] = "{level} (x{count})"

# -----------------------------------------------------------------------------
# Options module
# -----------------------------------------------------------------------------

OPTIONS_TITLE: Final[str] = "Paramétrage de l'application"
OPTIONS_LAST_SAVE: Final[str] = "Dernière sauvegarde des options : {date}"
OPTIONS_FACTORY_RESET: Final[str] = "Remettre réglage d'usine"
OPTIONS_FACTORY_RESET_TITLE: Final[str] = "Réglages d'usine"
OPTIONS_FACTORY_RESET_MESSAGE: Final[str] = (
    "Toute la configuration sera réinitialisée, historique des projets inclus. Continuer ?"
)
OPTIONS_UNDO_MAX: Final[str] = "Retour en arrière (annulations possibles)"
OPTIONS_DEFAULT_TAG_WEIGHTS: Final[str] = "Poids par défaut des tags (%)"
OPTIONS_SPECIAL_COLUMNS: Final[str] = "Colonnes spéciales proposées à l'affichage"
OPTIONS_SPECIAL_COLUMNS_ADD: Final[str] = "Ajouter"
OPTIONS_SPECIAL_COLUMNS_REMOVE: Final[str] = "Supprimer"
OPTIONS_FONT_SIZE: Final[str] = "Taille de police"
OPTIONS_SHORTCUTS: Final[str] = "Raccourcis clavier (tags cochés sur la ligne courante)"
OPTIONS_SHORTCUT_CTRL_O: Final[str] = "Ctrl+O"
OPTIONS_SHORTCUT_CTRL_N: Final[str] = "Ctrl+N"
OPTIONS_SHORTCUT_CTRL_T: Final[str] = "Ctrl+T"

# EOF
