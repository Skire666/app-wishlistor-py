"""Inline field error marker: red frame + warning icon with tooltip (A.3).

The frame is drawn by the wrapper itself (no background tint), so native
widgets (spin boxes, combos, lists) keep their normal rendering. The icon
tooltip opens after 150 ms and stays visible while the cursor is over it.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QPainter, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolTip, QWidget

from wishlistor.shared.constants_util import C_COLOR_ERROR, C_ICON_SIZE_PX, C_ICON_WARNING_PATH

_TOOLTIP_DELAY_MS: int = 50
_TOOLTIP_STAY_MS: int = 3_600_000  # keep it visible while hovering
_BORDER_MARGIN_PX: int = 2


class FieldMarkerView(QWidget):
    """Wraps an input widget and shows an inline error icon with a tooltip."""

    def __init__(self, inner: QWidget, parent: QWidget, show_icon: bool = True, draw_border: bool = True) -> None:
        """Initialize the marker around *inner*.

        Args:
            inner: The input widget to decorate.
            parent: The owning widget.
            show_icon: False keeps the icon out of the layout (moved elsewhere).
            draw_border: False skips the red frame (e.g. an icon-only marker).
        """
        super().__init__(parent)
        self.setObjectName("field_marker")
        self._inner = inner
        self._message: str = ""
        self._show_icon = show_icon
        self._draw_border = draw_border
        self._icon_var = self._build_icon()
        self._tooltip_timer_var = self._build_tooltip_timer()
        self._build_layout(inner)

    def _build_icon(self) -> QLabel:
        """Build the hidden warning icon, wired to the tooltip event filter."""
        icon = QLabel(self)
        icon.setPixmap(
            QPixmap(C_ICON_WARNING_PATH).scaled(
                C_ICON_SIZE_PX,
                C_ICON_SIZE_PX,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        icon.hide()
        icon.installEventFilter(self)
        return icon

    def _build_tooltip_timer(self) -> QTimer:
        """Build the single-shot timer that opens the tooltip after a short delay."""
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(_TOOLTIP_DELAY_MS)
        timer.timeout.connect(self._show_tooltip)
        return timer

    def _build_layout(self, inner: QWidget) -> None:
        """Lay out the inner field and the optional trailing icon."""
        layout = QHBoxLayout(self)
        margin = _BORDER_MARGIN_PX
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.addWidget(inner, 1)
        if self._show_icon:
            layout.addWidget(self._icon_var, 0)

    @classmethod
    def icon_only(cls, parent: QWidget) -> FieldMarkerView:
        """Build a marker with no wrapped field, for a title-row icon (e.g. group header)."""
        spacer = QWidget(parent)
        spacer.setFixedSize(0, 0)
        return cls(spacer, parent, draw_border=False)

    @property
    def inner(self) -> QWidget:
        """The decorated input widget."""
        return self._inner

    def set_error(self, message: str) -> None:
        """Show or clear the inline error state.

        Args:
            message: Tooltip text; an empty string clears the error.
        """
        self._message = message
        if message and self._show_icon:
            self._icon_var.show()
        else:
            self._icon_var.hide()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        """Draw the red frame around the field when in error (no background)."""
        _ = event
        if not self._draw_border or not self._message:
            return
        pen = QPen(QColor(C_COLOR_ERROR))
        pen.setCosmetic(True)  # exactly 1 device pixel regardless of fractional DPI scaling
        painter = QPainter(self)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        painter.end()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 - Qt override
        """Open the tooltip 150 ms after hovering the icon, keep it while hovered."""
        if watched is self._icon_var:
            if event.type() == QEvent.Type.Enter and self._message:
                self._tooltip_timer_var.start()
            elif event.type() == QEvent.Type.Leave:
                self._tooltip_timer_var.stop()
                QToolTip.hideText()
            elif event.type() == QEvent.Type.ToolTip:
                # Swallow the native help event so it does not bubble up to an ancestor
                # QAbstractItemView (e.g. a table cell widget): its own tooltip handling
                # would call QToolTip.hideText() and close the tooltip shown above.
                return True
        return False

    def _show_tooltip(self) -> None:
        """Show the persistent tooltip at the cursor position."""
        if self._message and self._icon_var.underMouse():
            QToolTip.showText(
                QCursor.pos(), self._message, self._icon_var, self._icon_var.rect(), _TOOLTIP_STAY_MS
            )


# EOF
