# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from wishlistor.models.view_state_model import JournalRowState


class ILogBridge(Protocol):
    """Relays logging records to the UI thread as journal row states."""

    def bind_record(self, callback: Callable[[JournalRowState], None]) -> None:
        """Register the record callback (invoked on the UI thread).

        Args:
            callback: Called for every log record emitted by the application.
        """
        ...


# EOF
