"""Application-wide constants: colors, special CSV columns, sizes and limits."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from datetime import datetime
from typing import Final

# -----------------------------------------------------------------------------
# Colors (dark theme)
# -----------------------------------------------------------------------------

C_COLOR_BACKGROUND_MAIN: Final[str] = "#1E1E1E"
C_COLOR_BACKGROUND_SECONDARY: Final[str] = "#252526"
C_COLOR_SURFACE: Final[str] = "#2D2D30"
C_COLOR_BORDER: Final[str] = "#3F3F46"
C_COLOR_BUTTON: Final[str] = "#3A6EA5"
C_COLOR_BUTTON_HOVER: Final[str] = "#4B82C3"
C_COLOR_BUTTON_DISABLED: Final[str] = "#555555"
C_COLOR_TEXT_PRIMARY: Final[str] = "#F3F3F3"
C_COLOR_TEXT_SECONDARY: Final[str] = "#B8B8B8"
C_COLOR_TEXT_DISABLED: Final[str] = "#7A7A7A"
C_COLOR_SUCCESS: Final[str] = "#4CAF50"
C_COLOR_ERROR: Final[str] = "#E53935"
C_COLOR_INFO: Final[str] = "#2196F3"
C_COLOR_WARNING: Final[str] = "#DD9000"
C_COLOR_SELECTION: Final[str] = "#16416C"
C_COLOR_ROWS_SHEET_HOVER: Final[str] = "#081F36"
C_COLOR_ROWS_SHEET_SELECTED: Final[str] = "#16416C"
C_COLOR_INPUT_BACKGROUND: Final[str] = "#333337"
C_COLOR_INPUT_BORDER: Final[str] = "#4A4A4F"
C_COLOR_LINK: Final[str] = "#4FC3F7"
C_COLOR_BLACK_FONT: Final[str] = "#000000"

# -----------------------------------------------------------------------------
# Special CSV columns (glossary)
# -----------------------------------------------------------------------------

C_PREFIX_CSV = "csv."
C_PREFIX_WSH = "wsh."  # wishlistor columns

C_CSV_PRIMARY_KEY: Final[str] = "csv.primary_key"
C_CSV_FIRST_CREATED: Final[str] = "csv.first_created"
C_CSV_LAST_MODIFIED: Final[str] = "csv.last_modified"

# edit
C_COL_CUSTOM_TAGS: Final[str] = "wsh.owner_tags"
C_COL_CUSTOM_COMMENTS: Final[str] = "wsh.owner_comments"
C_COL_CUSTOM_DATE_EDIT: Final[str] = "wsh.owner_date_edit"

# read only
C_COL_RANK_RELEASED: Final[str] = "wsh.rank_1_released"
C_COL_RANK_POPULARITY: Final[str] = "wsh.rank_2_popularity"
C_COL_RANK_NOTATION: Final[str] = "wsh.rank_3_notation100"
C_COL_RANK_CUSTOM_TAGS: Final[str] = "wsh.rank_4_owner_tags"
C_COL_RANK_1234_SUMMED: Final[str] = "wsh.rank_1234_summed"
C_COL_RANK_23_SUMMED: Final[str] = "wsh.rank_23_summed"

# Rank columns, in canonical order (all computed by the application).
C_RANK_COLUMNS: Final[tuple[str, ...]] = (
    C_COL_RANK_RELEASED,
    C_COL_RANK_POPULARITY,
    C_COL_RANK_NOTATION,
    C_COL_RANK_CUSTOM_TAGS,
    C_COL_RANK_1234_SUMMED,
    C_COL_RANK_23_SUMMED,
)

# Special columns offered by default in the display pickers.
C_DEFAULT_SPECIAL_DISPLAY_COLUMNS: Final[tuple[str, ...]] = (C_COL_CUSTOM_TAGS, C_COL_CUSTOM_COMMENTS)

# -----------------------------------------------------------------------------
# CSV format
# -----------------------------------------------------------------------------

C_CSV_DELIMITER: Final[str] = ";"
C_CSV_ENCODING_READ: Final[str] = "utf-8-sig"  # tolerate a BOM on read
C_CSV_ENCODING_WRITE: Final[str] = "utf-8"  # never write a BOM
C_TAG_SEPARATOR: Final[str] = "||"
C_CSV_BIG_FILE_BYTES: Final[int] = 100 * 1024 * 1024  # 100 MB warning threshold

C_DEFAULT_DATETIME_STR_CSV: Final[str] = "1900-01-01 00:00:00"
C_DEFAULT_NUMERIC_VALUE: Final[str] = "0"

# -----------------------------------------------------------------------------
# Options bounds and defaults
# -----------------------------------------------------------------------------

C_DEFAULT_DATETIME: datetime = datetime(1900, 1, 1)

C_UNDO_MIN: Final[int] = 1
C_UNDO_MAX: Final[int] = 30
C_UNDO_DEFAULT: Final[int] = 10

C_FONT_SIZE_MIN: Final[int] = 6
C_FONT_SIZE_MAX: Final[int] = 32
C_FONT_SIZE_DEFAULT: Final[int] = 12

C_ROW_HEIGHT_MIN: Final[int] = 10
C_ROW_HEIGHT_MAX: Final[int] = 200
C_ROW_HEIGHT_DEFAULT: Final[int] = 61

C_TEXT_FIELD_MIN_LEN: Final[int] = 1
C_TEXT_FIELD_MAX_LEN: Final[int] = 64

C_MIN_SEARCH_INDEX_COLUMNS: Final[int] = 1
C_MIN_VISIBLE_COLUMNS: Final[int] = 3

C_TAG_WEIGHT_MIN: Final[float] = -1.0
C_TAG_WEIGHT_MAX: Final[float] = 1.0

# -----------------------------------------------------------------------------
# Keyboard shortcuts (the key combinations are fixed; the tags are configurable)
# -----------------------------------------------------------------------------

C_SHORTCUT_CTRL_O: Final[str] = "ctrl_o"
C_SHORTCUT_CTRL_N: Final[str] = "ctrl_n"
C_SHORTCUT_CTRL_T: Final[str] = "ctrl_t"
C_DEFAULT_SHORTCUT_O_TAGS: Final[tuple[str, ...]] = ("A faire", "Favoris")
C_DEFAULT_SHORTCUT_N_TAGS: Final[tuple[str, ...]] = ("Ignoré",)
C_DEFAULT_SHORTCUT_T_TAGS: Final[tuple[str, ...]] = ("Terminé",)

# -----------------------------------------------------------------------------
# UI behaviour
# -----------------------------------------------------------------------------

C_WINDOW_MIN_WIDTH: Final[int] = 200
C_WINDOW_MIN_HEIGHT: Final[int] = 200
C_WINDOW_DEFAULT_WIDTH: Final[int] = 1280
C_WINDOW_DEFAULT_HEIGHT: Final[int] = 800

C_OVERLAY_MIN_DISPLAY_MS: Final[int] = 250
C_ICON_SIZE_PX: Final[int] = 26
C_CHECKBOX_INDICATOR_SIZE_PX: Final[int] = 18  # Fusion default (14px)
C_ICON_PLACEHOLDER_PATH: Final[str] = "./ress/placeholder.png"
C_ICON_WARNING_PATH: Final[str] = "./ress/fatcow_warning.png"
C_SEPARATOR_WIDTH_PX: Final[int] = 100
C_BANNER_VISIBLE_LINES: Final[int] = 3

C_IMAGE_CACHE_MAX_BYTES: Final[int] = 256 * 1024 * 1024  # 256 MB pixmap cache
C_IMAGE_FILE_CACHE_MAX_BYTES: Final[int] = 64 * 1024 * 1024  # 64 MB raw image bytes cache
C_IMAGE_DATA_URI_PREFIX: Final[str] = "data:image/"
C_IMAGE_DATA_OSB_IMAGE: Final[str] = "![["  # link obsdian : ![[./img/GUID.jpeg]]
C_URL_PREFIX: Final[str] = "http"
C_WINDOWS_DRIVE_PREFIXES: Final[tuple[str, ...]] = ("C:\\", "D:\\", "E:\\", "F:\\", "G:\\", "H:\\")

# -----------------------------------------------------------------------------
# Pill & hover metrics (shared by the CSV cell delegate and tag-colored widgets)
# -----------------------------------------------------------------------------

C_CELL_TEXT_PADDING_PX: Final[int] = 4
C_TAG_PILL_PADDING_PX: Final[int] = 6  # espace horizontal en plus entre le contrôle et le texte du pill
C_TAG_PILL_SPACING_PX: Final[int] = 4  # espace entre pills
C_TAG_PILL_RADIUS_PX: Final[int] = 4
C_TAG_PILL_HOVER_DARKEN_RATIO: Final[float] = 0.10  # survol = fond mélangé à 10 % de noir

# -----------------------------------------------------------------------------
# Runtime files
# -----------------------------------------------------------------------------

C_CONFIG_FILE_PATH: Final[str] = "./config-wishlistor.json"
C_LOG_FOLDER_PATH: Final[str] = "./tmp_app_logs"
C_LOG_FILE_NAME: Final[str] = "wishlistor.log"
C_LOG_MAX_BYTES: Final[int] = 2 * 1024 * 1024  # 2 MB per file
C_LOG_BACKUP_COUNT: Final[int] = 4  # 5 files max (1 active + 4 backups)

# EOF
