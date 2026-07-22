"""Cell delegate for the CSV table: images, links, tag pills, hover, stripes."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import base64
from collections.abc import Callable
from pathlib import PurePath
from typing import ClassVar, cast

from PySide6.QtCore import QAbstractItemModel, QEvent, QModelIndex, QPersistentModelIndex, QRect, Qt
from PySide6.QtGui import QBrush, QColor, QFontMetrics, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QStyle, QStyledItemDelegate, QStyleOptionButton, QStyleOptionViewItem

from wishlistor.interfaces.i_image_repository import IImageRepository
from wishlistor.shared.constants_util import (
    C_CELL_TEXT_PADDING_PX,
    C_COL_CUSTOM_TAGS,
    C_COLOR_ERROR,
    C_COLOR_LINK,
    C_COLOR_ROWS_SHEET_HOVER,
    C_COLOR_ROWS_SHEET_SELECTED,
    C_COLOR_SELECTION,
    C_COLOR_TEXT_PRIMARY,
    C_IMAGE_CACHE_MAX_BYTES,
    C_IMAGE_DATA_OSB_IMAGE,
    C_IMAGE_DATA_URI_PREFIX,
    C_TAG_PILL_PADDING_PX,
    C_TAG_PILL_RADIUS_PX,
    C_TAG_PILL_SPACING_PX,
    C_TAG_SEPARATOR,
    C_URL_PREFIX,
    C_WINDOWS_DRIVE_PREFIXES,
)
from wishlistor.shared.i18n_fra import CSV_INVALID_IMAGE
from wishlistor.shared.tag_util import C_TAG_COLORS, tag_from_label
from wishlistor.views.csv_table_model_view import CsvTableModelView

_CHECK_COLUMN: int = 0

_ModelIndex = QModelIndex | QPersistentModelIndex


def is_link_value(value: str) -> bool:
    """Return True when a cell value must render as a clickable link."""
    return value.startswith((C_URL_PREFIX, *C_WINDOWS_DRIVE_PREFIXES))


class _PixmapCache:
    """Byte-bounded FIFO cache of decoded pixmaps, keyed by data URI or raw bytes (spec C)."""

    def __init__(self, max_bytes: int) -> None:
        """Initialize the cache.

        Args:
            max_bytes: Total pixmap memory budget.
        """
        self._max_bytes = max_bytes
        self._entries: dict[str | bytes, QPixmap | None] = {}
        self._bytes: int = 0

    def get(self, data_uri: str) -> QPixmap | None:
        """Return the decoded pixmap of *data_uri* (None when invalid).

        Args:
            data_uri: The full `data:image/...;base64,...` cell value.
        """
        return self._get(data_uri, lambda: _decode_data_uri(data_uri))

    def get_from_raw(self, raw: bytes) -> QPixmap | None:
        """Return the decoded pixmap of *raw* image bytes (None when invalid).

        Args:
            raw: The raw bytes read from an image file.
        """
        return self._get(raw, lambda: _decode_raw_bytes(raw))

    def _get(self, key: str | bytes, decode: Callable[[], QPixmap | None]) -> QPixmap | None:
        """Return the cached pixmap for *key*, decoding and storing it on first access."""
        if key in self._entries:
            return self._entries[key]
        pixmap = decode()
        self._entries[key] = pixmap
        if pixmap is not None:
            self._bytes += pixmap.width() * pixmap.height() * 4
            self._evict()
        return pixmap

    def _evict(self) -> None:
        """Drop the oldest entries until the budget is respected."""
        while self._bytes > self._max_bytes and self._entries:
            key = next(iter(self._entries))
            pixmap = self._entries.pop(key)
            if pixmap is not None:
                self._bytes -= pixmap.width() * pixmap.height() * 4


def _decode_raw_bytes(raw: bytes) -> QPixmap | None:
    """Decode raw image bytes into a pixmap, or None on failure."""
    pixmap = QPixmap()
    if not pixmap.loadFromData(raw):
        return None
    return pixmap


def _decode_data_uri(data_uri: str) -> QPixmap | None:
    """Decode a base64 image data URI into a pixmap, or None on failure."""
    separator = data_uri.find(",")
    if separator < 0:
        return None
    try:
        raw = base64.b64decode(data_uri[separator + 1 :], validate=False)
    except ValueError, TypeError:
        return None
    return _decode_raw_bytes(raw)


class CsvCellDelegateView(QStyledItemDelegate):
    """Paints stripes, row hover, centered checkboxes, images, links and pills."""

    _cache: ClassVar[_PixmapCache] = _PixmapCache(C_IMAGE_CACHE_MAX_BYTES)

    def __init__(self, image_repository: IImageRepository) -> None:
        """Initialize the delegate.

        Args:
            image_repository: Reads image bytes referenced by file-based image cells.
        """
        super().__init__()
        self._image_repository = image_repository
        self._csv_path_var: str = ""
        self._hovered_row: int = -1
        self._on_delete_clicked: Callable[[int], None] | None = None

    def bind_delete_clicked(self, callback: Callable[[int], None]) -> None:
        """Register the per-row delete callback (receives the view row).

        Args:
            callback: Called when the trailing 'X' cell is clicked.
        """
        self._on_delete_clicked = callback

    def set_csv_path(self, csv_path: str) -> None:
        """Update the CSV file location used to resolve relative image paths.

        Args:
            csv_path: Absolute path to the currently opened CSV file.
        """
        self._csv_path_var = csv_path

    @staticmethod
    def _is_delete_column(index: _ModelIndex) -> bool:
        """Return True for the trailing per-row delete column."""
        return index.column() > _CHECK_COLUMN and index.column() == index.model().columnCount() - 1

    def set_hovered_row(self, view_row: int) -> None:
        """Track the hovered view row for the row-wide highlight.

        Args:
            view_row: The hovered row, or -1 when the cursor left the table.
        """
        self._hovered_row = view_row

    # -- painting -------------------------------------------------------------------

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: _ModelIndex) -> None:
        """Paint one cell."""
        self.initStyleOption(option, index)
        self._paint_background(painter, option, index)
        if index.column() == _CHECK_COLUMN:
            self._paint_checkbox(painter, option, index)
            return
        if self._is_delete_column(index):
            self._paint_text(painter, option, "✕", QColor(C_COLOR_ERROR), underline=False, centered=True)
            return
        value = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        model = cast("CsvTableModelView", index.model())
        column_name = model.column_name_at(index.column())
        if value.startswith(C_IMAGE_DATA_URI_PREFIX):
            self._paint_image_from_base64_uri(painter, option, value)
        elif value.startswith(C_IMAGE_DATA_OSB_IMAGE):
            self._paint_image_from_file(painter, option, value)
        elif column_name == C_COL_CUSTOM_TAGS:
            self._paint_tags(painter, option, value)
        elif is_link_value(value):
            self._paint_text(painter, option, value, QColor(C_COLOR_LINK), underline=True)
        else:
            self._paint_text(painter, option, value, QColor(C_COLOR_TEXT_PRIMARY), underline=False)

    def _paint_background(self, painter: QPainter, option: QStyleOptionViewItem, index: _ModelIndex) -> None:
        """Fill the stripe background, then the hover/selection overlays."""
        background = index.data(Qt.ItemDataRole.BackgroundRole)
        if isinstance(background, QBrush):
            painter.fillRect(option.rect, background)
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(C_COLOR_ROWS_SHEET_SELECTED))
        elif index.row() == self._hovered_row:
            hover = QColor(C_COLOR_ROWS_SHEET_HOVER)
            painter.fillRect(option.rect, hover)

    def _paint_checkbox(self, painter: QPainter, option: QStyleOptionViewItem, index: _ModelIndex) -> None:
        """Paint a centered checkbox reflecting the CheckStateRole."""
        state = index.data(Qt.ItemDataRole.CheckStateRole)
        button = QStyleOptionButton()
        style = QApplication.style()
        size = style.pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth, button)
        button.rect = QRect(
            option.rect.x() + (option.rect.width() - size) // 2,
            option.rect.y() + (option.rect.height() - size) // 2,
            size,
            size,
        )
        checked = state in {Qt.CheckState.Checked, Qt.CheckState.Checked.value}
        button.state = QStyle.StateFlag.State_Enabled | (
            QStyle.StateFlag.State_On if checked else QStyle.StateFlag.State_Off
        )
        style.drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorCheckBox, button, painter)

    def _paint_image_from_base64_uri(self, painter: QPainter, option: QStyleOptionViewItem, value: str) -> None:
        """Paint a decoded data-URI image scaled to the row height."""
        pixmap = self._cache.get(value)
        self._paint_pixmap_or_fallback(painter, option, pixmap)

    def _paint_image_from_file(self, painter: QPainter, option: QStyleOptionViewItem, value: str) -> None:
        """Paint an image read from disk, resolved relative to the CSV file location."""
        path_to_image = value[3:-2]  # ![[./img/GUID.jpeg]] -> ./img/GUID.jpeg
        absolute_path = str(PurePath(self._csv_path_var).parent / path_to_image)
        raw = self._image_repository.read_image_bytes(absolute_path)
        pixmap = self._cache.get_from_raw(raw) if raw is not None else None
        self._paint_pixmap_or_fallback(painter, option, pixmap)

    def _paint_pixmap_or_fallback(
        self, painter: QPainter, option: QStyleOptionViewItem, pixmap: QPixmap | None
    ) -> None:
        """Paint *pixmap* scaled to the row height, or the invalid-image label."""
        if pixmap is None or pixmap.isNull():
            self._paint_text(painter, option, CSV_INVALID_IMAGE, QColor(C_COLOR_TEXT_PRIMARY), underline=False)
            return
        target_height = max(1, option.rect.height() - 2)
        scaled = pixmap.scaledToHeight(target_height, Qt.TransformationMode.SmoothTransformation)
        painter.drawPixmap(option.rect.x() + 1, option.rect.y() + 1, scaled)

    def _paint_tags(self, painter: QPainter, option: QStyleOptionViewItem, value: str) -> None:
        """Paint the tags as colored pills, wrapped and vertically centered in the row."""
        labels = [label for label in value.split(C_TAG_SEPARATOR) if label]
        if not labels:
            return
        metrics = QFontMetrics(option.font)
        pill_height = metrics.height() + 4
        line_step = pill_height + C_TAG_PILL_SPACING_PX
        max_lines = max(1, (option.rect.height() - 2) // line_step)
        painter.save()
        lines = self._wrap_tag_lines(metrics, option.rect, labels, max_lines)
        self._paint_tag_lines(painter, option, metrics, lines, pill_height)
        painter.restore()

    @staticmethod
    def _wrap_tag_lines(metrics: QFontMetrics, rect: QRect, labels: list[str], max_lines: int) -> list[list[str]]:
        """Group the pill labels into lines that fit the available width."""
        left = rect.x() + C_TAG_PILL_SPACING_PX
        right = rect.x() + rect.width() - C_TAG_PILL_SPACING_PX
        lines: list[list[str]] = [[]]
        x = left
        for label in labels:
            width = metrics.horizontalAdvance(label) + 2 * C_TAG_PILL_PADDING_PX
            if x > left and x + width > right:
                if len(lines) >= max_lines:
                    lines[-1].append(label)
                    x += width + C_TAG_PILL_SPACING_PX
                    continue
                lines.append([])
                x = left
            lines[-1].append(label)
            x += width + C_TAG_PILL_SPACING_PX
        return lines

    def _paint_tag_lines(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        metrics: QFontMetrics,
        lines: list[list[str]],
        pill_height: int,
    ) -> None:
        """Paint the pre-wrapped pill lines, the whole block centered vertically."""
        left = option.rect.x() + C_TAG_PILL_SPACING_PX
        content_height = len(lines) * pill_height + (len(lines) - 1) * C_TAG_PILL_SPACING_PX
        y = option.rect.y() + (option.rect.height() - content_height) // 2
        for line_labels in lines:
            x = left
            for label in line_labels:
                x += self._draw_pill(painter, metrics, x, y, pill_height, label) + C_TAG_PILL_SPACING_PX
            y += pill_height + C_TAG_PILL_SPACING_PX

    @staticmethod
    def _draw_pill(painter: QPainter, metrics: QFontMetrics, x: int, y: int, pill_height: int, label: str) -> int:
        """Draw one tag pill and return its width."""
        width = metrics.horizontalAdvance(label) + 2 * C_TAG_PILL_PADDING_PX
        color = C_TAG_COLORS.get(tag_from_label(label), C_COLOR_SELECTION)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(str(color)))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawRoundedRect(x, y, width, pill_height, C_TAG_PILL_RADIUS_PX, C_TAG_PILL_RADIUS_PX)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(QRect(x, y - 1, width, pill_height), Qt.AlignmentFlag.AlignCenter, label)
        return width

    def _paint_text(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        value: str,
        color: QColor,
        underline: bool,
        centered: bool = False,
    ) -> None:
        """Paint word-wrapped text, vertically centered and clipped to the cell."""
        rect = option.rect.adjusted(C_CELL_TEXT_PADDING_PX, 0, -C_CELL_TEXT_PADDING_PX, 0)
        painter.save()
        font = option.font
        font.setUnderline(underline)
        painter.setFont(font)
        painter.setPen(color)
        horizontal = Qt.AlignmentFlag.AlignHCenter if centered else Qt.AlignmentFlag.AlignLeft
        flags = int(horizontal | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap)
        painter.drawText(rect, flags, value)
        painter.restore()

    # -- interaction -------------------------------------------------------------------

    def editorEvent(  # noqa: N802 - Qt override
        self, event: QEvent, model: QAbstractItemModel, option: QStyleOptionViewItem, index: _ModelIndex
    ) -> bool:
        """Toggle the check column on click (whole cell is the hit zone)."""
        _ = option
        if event.type() != QEvent.Type.MouseButtonRelease:
            return False
        if index.column() == _CHECK_COLUMN:
            current = index.data(Qt.ItemDataRole.CheckStateRole)
            checked = current in {Qt.CheckState.Checked, Qt.CheckState.Checked.value}
            new_state = Qt.CheckState.Unchecked if checked else Qt.CheckState.Checked
            return model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
        if self._is_delete_column(index) and self._on_delete_clicked is not None:
            self._on_delete_clicked(index.row())
            return True
        return False


# EOF
