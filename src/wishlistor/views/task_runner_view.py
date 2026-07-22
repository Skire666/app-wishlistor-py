"""QThreadPool-based task runner implementing ITaskRunner (AGENTS §16.2)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class _TaskSignals(QObject):
    """Signal holder used to marshal worker results back to the UI thread."""

    finished = Signal(object)
    failed = Signal(object)


class _Task(QRunnable):
    """One-shot runnable executing a callable and emitting its outcome."""

    def __init__(self, work: Callable[[], object], signals: _TaskSignals) -> None:
        """Initialize the runnable.

        Args:
            work: Callable executed off the UI thread.
            signals: Signal holder owned by the runner.
        """
        super().__init__()
        self._work = work
        self._signals = signals

    def run(self) -> None:
        """Execute the work and emit finished/failed (never raises)."""
        try:
            result = self._work()
        except Exception as excp:  # noqa: BLE001 - the worker must never crash the pool
            self._signals.failed.emit(excp)
            return
        self._signals.finished.emit(result)


class TaskRunnerView(QObject):
    """Runs work on the global thread pool, reporting on the UI thread."""

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the runner.

        Args:
            parent: Optional owner QObject.
        """
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._active: list[_TaskSignals] = []

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
        signals = _TaskSignals()
        self._active.append(signals)  # keep alive until completion

        @Slot(object)
        def _on_finished(result: object) -> None:
            self._release(signals)
            on_success(result)

        @Slot(object)
        def _on_failed(excp: object) -> None:
            self._release(signals)
            if isinstance(excp, Exception):
                on_error(excp)

        signals.finished.connect(_on_finished)
        signals.failed.connect(_on_failed)
        self._pool.start(_Task(work, signals))

    def _release(self, signals: _TaskSignals) -> None:
        """Drop the signal holder once its task completed."""
        if signals in self._active:
            self._active.remove(signals)


# EOF
