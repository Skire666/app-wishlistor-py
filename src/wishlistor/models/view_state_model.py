"""Frozen snapshot types exchanged between Views and Presenters (AGENTS §3.2).

These are read-only value objects: no identity, no behaviour, no validation.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WindowGeometryState:
    """Main window size, position and maximized state, persisted between sessions."""

    width: int
    height: int
    x: int
    y: int
    is_maximized: bool = False


@dataclass(frozen=True)
class ProjectRowState:
    """One row of the project history table (module Projet)."""

    id_project: str
    name: str
    website: str
    category: str
    csv_path: str
    last_opened: str
    file_size_bytes: int
    file_size_label: str
    is_available: bool


@dataclass(frozen=True)
class ProjectFormState:
    """Snapshot of the project creation/edition form (spec B.3.1)."""

    csv_path: str = ""
    name: str = ""
    website: str = ""
    category: str = ""
    created_at: str = ""
    row_height: int = 0
    tag_weights: dict[str, float] = field(default_factory=dict)
    primary_column: str = ""
    released_column: str = ""
    popularity_column: str = ""
    scoring_column: str = ""
    search_index_columns: tuple[str, ...] = field(default_factory=tuple)
    visible_columns: tuple[str, ...] = field(default_factory=tuple)
    column_nicknames: dict[str, str] = field(default_factory=dict)
    column_default_values: tuple[tuple[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CsvViewState:
    """Snapshot of the CSV module interactive controls."""

    url_text: str = ""
    filter_text: str = ""
    search_text: str = ""
    active_tag_filters: frozenset[str] = field(default_factory=frozenset)
    checked_rows: tuple[int, ...] = field(default_factory=tuple)
    current_doc_row: int = -1


@dataclass(frozen=True)
class JournalRowState:
    """One row of the journal table (module Journal)."""

    date_label: str
    level: str
    source: str
    message: str


@dataclass(frozen=True)
class OptionsViewState:
    """Snapshot of the application options form (module Options)."""

    undo_max: int = 0
    default_tag_weights: dict[str, float] = field(default_factory=dict)
    special_display_columns: tuple[str, ...] = field(default_factory=tuple)
    font_size: int = 0
    shortcut_ctrl_o_tags: tuple[str, ...] = field(default_factory=tuple)
    shortcut_ctrl_n_tags: tuple[str, ...] = field(default_factory=tuple)
    shortcut_ctrl_t_tags: tuple[str, ...] = field(default_factory=tuple)


# EOF
