"""Blocking progress overlay with a minimum display time of 250 ms (spec A.4)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import time

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from wishlistor.shared.constants_util import C_OVERLAY_MIN_DISPLAY_MS
from wishlistor.shared.i18n_fra import COMMON_LOADING

_BACKGROUND_ALPHA: int = 170
_PROGRESS_WIDTH_PX: int = 240


class BusyOverlayView(QWidget):
    """Covers its parent, blocking interactions while a worker runs."""

    def __init__(self, parent: QWidget) -> None:
        """Initialize the overlay over *parent*.

        Args:
            parent: The widget (frame) to block while busy.
        """
        super().__init__(parent)
        self.setObjectName("busy_overlay")
        self._target = parent
        self._shown_at: float = 0.0
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel(COMMON_LOADING, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress = QProgressBar(self)
        progress.setRange(0, 0)  # indeterminate
        progress.setFixedWidth(_PROGRESS_WIDTH_PX)
        layout.addWidget(label)
        layout.addWidget(progress)
        parent.installEventFilter(self)
        self.hide()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 - Qt override
        """Track the parent geometry so the overlay always covers it."""
        if watched is self._target and event.type() in {QEvent.Type.Resize, QEvent.Type.Show}:
            self.setGeometry(self._target.rect())
        return False

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        """Paint the translucent backdrop."""
        _ = event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, _BACKGROUND_ALPHA))
        painter.end()

    def show_busy(self) -> None:
        """Show the overlay and start the minimum-display timer."""
        self._shown_at = time.monotonic()
        self.setGeometry(self._target.rect())
        self.raise_()
        self.show()

    def hide_busy(self) -> None:
        """Hide the overlay, keeping it visible at least 250 ms."""
        elapsed_ms = int((time.monotonic() - self._shown_at) * 1000)
        remaining = max(0, C_OVERLAY_MIN_DISPLAY_MS - elapsed_ms)
        if remaining <= 0:
            self.hide()
        else:
            QTimer.singleShot(remaining, self.hide)


# EOF
