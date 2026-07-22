"""Reusable colored tag-pill checkbox, shared by CSV filters, the tag editor and options."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen, QPolygonF
from PySide6.QtWidgets import QCheckBox, QStyle, QStyleOptionButton, QWidget

from wishlistor.shared.constants_util import (
    C_CELL_TEXT_PADDING_PX,
    C_FONT_SIZE_DEFAULT,
    C_TAG_PILL_HOVER_DARKEN_RATIO,
    C_TAG_PILL_PADDING_PX,
    C_TAG_PILL_RADIUS_PX,
)


def _darkened(color: str) -> str:
    """Return *color* blended with the hover darken ratio of black."""
    base = QColor(color)
    ratio = 1 - C_TAG_PILL_HOVER_DARKEN_RATIO
    return QColor(round(base.red() * ratio), round(base.green() * ratio), round(base.blue() * ratio)).name()


class TagPillView(QCheckBox):
    """A checkbox rendered as a rounded, tag-colored pill (base + hover states)."""

    def __init__(self, label: str, color: str, parent: QWidget | None = None) -> None:
        """Initialize the pill.

        Args:
            label: Checkbox text.
            color: Tag background color, as a hex string.
            parent: The owning widget.
        """
        super().__init__(label, parent)
        self.setStyleSheet(
            f"QCheckBox {{ background-color: {color}; color: #FFFFFF; border-radius: {C_TAG_PILL_RADIUS_PX}px; "
            f"padding: {C_CELL_TEXT_PADDING_PX}px {C_TAG_PILL_PADDING_PX}px; "
            f"font-size: {C_FONT_SIZE_DEFAULT}pt; }} "
            f"QCheckBox:hover {{ background-color: {_darkened(color)}; }} "
            f"QCheckBox::indicator {{ background-color: #000000; }}"
        )

    def hitButton(self, pos: QPoint) -> bool:  # noqa: N802 - Qt override
        """Make the whole colored pill clickable, not just the native indicator+label area."""
        return self.rect().contains(pos)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        """Paint the pill, then a white checkmark over the indicator (QSS-styled indicators drop the native one)."""
        super().paintEvent(event)
        if not self.isChecked():
            return
        option = QStyleOptionButton()
        self.initStyleOption(option)
        rect = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, option, self)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#FFFFFF"))
        pen.setWidthF(max(1.5, rect.width() * 0.15))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        check = QPolygonF(
            [
                QPointF(rect.left() + rect.width() * 0.20, rect.top() + rect.height() * 0.55),
                QPointF(rect.left() + rect.width() * 0.42, rect.top() + rect.height() * 0.75),
                QPointF(rect.left() + rect.width() * 0.80, rect.top() + rect.height() * 0.28),
            ]
        )
        painter.drawPolyline(check)


# EOF
