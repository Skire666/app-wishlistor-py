"""Journal presenter: feeds the journal table from the logging bridge (B.5)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import time

from wishlistor.interfaces.i_journal_view import IJournalView
from wishlistor.interfaces.i_log_bridge import ILogBridge
from wishlistor.models.view_state_model import JournalRowState
from wishlistor.shared.constants_util import C_LOG_FOLDER_PATH
from wishlistor.shared.operating_system_util import open_folder


class JournalPresenter:
    """Wires the log bridge to the journal view."""

    def __init__(self, view: IJournalView, log_bridge: ILogBridge) -> None:
        """Initialize the presenter.

        Args:
            view: The journal view.
            log_bridge: The UI-thread log record source.
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._view = view
        self._log_bridge = log_bridge
        self._counts: dict[str, int] = {}

    def start(self) -> None:
        """Bind the view callbacks and start receiving records."""
        self._view.bind_levels_changed(self._handle_levels_changed)
        self._view.bind_clear_clicked(self._handle_clear)
        self._view.bind_open_folder_clicked(self._handle_open_folder)
        self._log_bridge.bind_record(self._handle_record)

    def _handle_record(self, entry: JournalRowState) -> None:
        """Append a record to the table and refresh the level counters."""
        self._counts[entry.level] = self._counts.get(entry.level, 0) + 1
        self._view.append_entry(entry)
        self._view.set_level_counts(self._counts)

    def _handle_levels_changed(self, levels: frozenset[str]) -> None:
        """Apply the level filter chosen by the user."""
        self._view.apply_level_filter(levels)

    def _handle_clear(self) -> None:
        """Empty the displayed journal (files are untouched)."""
        started = time.perf_counter()
        self._counts = {}
        self._view.clear_entries()
        self._view.set_level_counts(self._counts)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'vider le journal' terminée en %s ms", elapsed_ms)

    def _handle_open_folder(self) -> None:
        """Open the log folder in the system file explorer."""
        started = time.perf_counter()
        try:
            open_folder(C_LOG_FOLDER_PATH)
        except Exception:
            self._logger.exception("Impossible d'ouvrir le dossier des logs.")
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        self._logger.info("Action 'ouvrir le dossier des logs' terminée en %s ms", elapsed_ms)


# EOF
