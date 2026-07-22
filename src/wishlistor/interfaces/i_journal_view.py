# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from wishlistor.interfaces.i_base_view import IBaseView
from wishlistor.models.view_state_model import JournalRowState


class IJournalView(IBaseView, Protocol):
    """Journal module: read-only session log table, newest first."""

    def snapshot(self) -> frozenset[str]:
        """Return the level names currently checked."""
        ...

    def append_entry(self, entry: JournalRowState) -> None:
        """Prepend a log entry to the table (newest on top).

        Args:
            entry: The record to display.
        """
        ...

    def set_level_counts(self, counts: dict[str, int]) -> None:
        """Refresh the per-level counters next to the checkboxes.

        Args:
            counts: Level name to record count mapping.
        """
        ...

    def apply_level_filter(self, levels: frozenset[str]) -> None:
        """Show only the rows whose level is in *levels*.

        Args:
            levels: Level names to keep visible.
        """
        ...

    def clear_entries(self) -> None:
        """Empty the displayed table (files are not touched)."""
        ...

    def bind_levels_changed(self, callback: Callable[[frozenset[str]], None]) -> None:
        """Register the level checkbox callback."""
        ...

    def bind_clear_clicked(self, callback: Callable[[], None]) -> None:
        """Register the 'Vider l'affichage' button callback."""
        ...

    def bind_open_folder_clicked(self, callback: Callable[[], None]) -> None:
        """Register the log-folder hyperlink callback."""
        ...


# EOF
