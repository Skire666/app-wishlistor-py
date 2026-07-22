# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


class ITaskRunner(Protocol):
    """Executes long-running work off the UI thread (AGENTS §16.1).

    Implementations must invoke the callbacks on the UI thread.
    """

    def run(
        self,
        work: Callable[[], object],
        on_success: Callable[[object], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        """Run *work* on a background thread and report the outcome.

        Args:
            work: Callable executed off the UI thread.
            on_success: Called on the UI thread with the work result.
            on_error: Called on the UI thread with the raised exception.
        """
        ...


# EOF
