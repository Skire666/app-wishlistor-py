"""Logging handler relaying records to the UI thread as JournalRowState."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Slot

from wishlistor.models.view_state_model import JournalRowState
from wishlistor.shared.typing.datetime_util import C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS


class _RecordRelay(QObject):
    """Private QObject signal holder (avoids the QObject/Handler `emit` clash)."""

    record_received = Signal(object)


class LogBridgeView(logging.Handler):
    """logging.Handler feeding the Journal module through a queued Qt signal."""

    def __init__(self) -> None:
        """Initialize the handler and its UI-thread relay."""
        super().__init__()
        self._relay = _RecordRelay()
        self._callback: Callable[[JournalRowState], None] | None = None
        self._relay.record_received.connect(self._dispatch)

    def emit(self, record: logging.LogRecord) -> None:
        """Convert a log record and queue it to the UI thread.

        Args:
            record: The record emitted by the logging framework.
        """
        date_label = datetime.fromtimestamp(record.created).strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS)
        state = JournalRowState(
            date_label=date_label, level=record.levelname, source=record.name, message=record.getMessage()
        )
        self._relay.record_received.emit(state)

    def bind_record(self, callback: Callable[[JournalRowState], None]) -> None:
        """Register the record callback (invoked on the UI thread).

        Args:
            callback: Called for every log record emitted by the application.
        """
        self._callback = callback

    @Slot(object)
    def _dispatch(self, state: object) -> None:
        """Forward a queued record to the bound callback (UI thread)."""
        if self._callback is not None and isinstance(state, JournalRowState):
            self._callback(state)


# EOF
