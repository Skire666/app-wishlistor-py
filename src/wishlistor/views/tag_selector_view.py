"""Tag selector: the modeless tag composer, used for both single-row and mass edits.

Checkboxes render white text on the fixed tag color. Only one tag can be
active at a time (spec B.4.3): checking one live-unchecks every other.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QPoint, QSize, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from wishlistor.shared.constants_util import C_TAG_PILL_SPACING_PX
from wishlistor.shared.enums.tag_enum import TagEnum
from wishlistor.shared.i18n_fra import CSV_EDIT_TAGS_BUTTON
from wishlistor.shared.tag_util import C_ALL_TAGS, C_TAG_COLORS, apply_check, apply_uncheck
from wishlistor.views.tag_pill_view import TagPillView


class TagChecklistView(QWidget):
    """Colored tag-pill checkboxes enforcing a single active tag live."""

    def __init__(self, parent: QWidget | None = None, horizontal: bool = False) -> None:
        """Initialize the checklist.

        Args:
            parent: The owning widget.
            horizontal: True lays the tags left to right instead of top-down.
        """
        super().__init__(parent)
        self.setObjectName("tag_checklist")
        self._horizontal = horizontal
        self._tags: frozenset[TagEnum] = frozenset()
        self._boxes: dict[TagEnum, QCheckBox] = {}
        self._on_changed: Callable[[], None] | None = None
        layout = QHBoxLayout(self) if horizontal else QVBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(C_TAG_PILL_SPACING_PX)
        for tag in C_ALL_TAGS:
            layout.addWidget(self._build_row(tag))
        if horizontal:
            layout.addStretch(1)

    def _build_row(self, tag: TagEnum) -> QCheckBox:
        """Build one colored pill checkbox for the tag (spec A.4: whole pill toggles it)."""
        box = TagPillView(tag.value, C_TAG_COLORS[tag], self)
        box.setObjectName(f"tag_row_{tag.name.lower()}")
        if not self._horizontal:
            box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        box.toggled.connect(lambda checked, t=tag: self._handle_toggle(t, checked))
        self._boxes[tag] = box
        return box

    def bind_changed(self, callback: Callable[[], None]) -> None:
        """Register the change callback (fired after every toggle).

        Args:
            callback: Called after any user toggle.
        """
        self._on_changed = callback

    def set_tags(self, tags: frozenset[TagEnum]) -> None:
        """Install the current tag set.

        Args:
            tags: Tags to check initially.
        """
        self._tags = tags
        self._sync_boxes()

    def tags(self) -> frozenset[TagEnum]:
        """Return the current tag set."""
        return self._tags

    def tag_labels(self) -> frozenset[str]:
        """Return the current tag labels."""
        return frozenset(tag.value for tag in self._tags)

    def _handle_toggle(self, tag: TagEnum, checked: bool) -> None:
        """Enforce the single-active-tag rule after a user toggle."""
        self._tags = apply_check(self._tags, tag) if checked else apply_uncheck(self._tags, tag)
        self._sync_boxes()
        if self._on_changed is not None:
            self._on_changed()

    def _sync_boxes(self) -> None:
        """Reflect the tag set in the checkboxes without re-triggering toggles."""
        for tag, box in self._boxes.items():
            box.blockSignals(True)
            box.setChecked(tag in self._tags)
            box.blockSignals(False)


def _clamp_to_screen(pos: QPoint, size: QSize) -> QPoint:
    """Keep a top-left position inside the screen the click happened on."""
    screen = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
    bounds = screen.availableGeometry()
    x = min(max(pos.x(), bounds.left()), max(bounds.left(), bounds.right() - size.width()))
    y = min(max(pos.y(), bounds.top()), max(bounds.top(), bounds.bottom() - size.height()))
    return QPoint(x, y)


class _TagsDialog(QDialog):
    """Modeless tag dialog that dismisses itself when it loses window focus."""

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802 - Qt override
        """Close the dialog (as a cancel) once an outside click deactivates it."""
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow():
            self.reject()
        super().changeEvent(event)


def _open_tags(
    parent: QWidget,
    initial_tags: frozenset[TagEnum],
    anchor_pos: QPoint | None,
    on_done: Callable[[frozenset[str] | None], None],
) -> None:
    """Open the modeless tag composer, pre-checked with the given tags.

    Args:
        parent: The owning widget.
        initial_tags: Tags checked when the dialog opens.
        anchor_pos: Global position to open next to (the clicked cell or button), or None to center.
        on_done: Called with the composed tag labels, or None on cancel.
    """
    dialog = _TagsDialog(parent)
    dialog.setObjectName("tags_dialog")
    dialog.setWindowTitle(CSV_EDIT_TAGS_BUTTON)
    dialog.setModal(False)
    dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    checklist = TagChecklistView(dialog)
    checklist.set_tags(initial_tags)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout = QVBoxLayout(dialog)
    layout.addWidget(checklist)
    layout.addWidget(buttons)
    if anchor_pos is not None:
        dialog.adjustSize()
        dialog.move(_clamp_to_screen(anchor_pos, dialog.size()))
    dialog.finished.connect(
        lambda result: on_done(checklist.tag_labels() if result == QDialog.DialogCode.Accepted else None)
    )
    dialog.show()


def open_mass_tags(
    parent: QWidget, on_done: Callable[[frozenset[str] | None], None], anchor_pos: QPoint | None = None
) -> None:
    """Open the modeless tag composer used by the mass edit action.

    Args:
        parent: The owning widget.
        on_done: Called with the composed tag labels, or None on cancel.
        anchor_pos: Global position to open next to (the button), or None to center.
    """
    _open_tags(parent, frozenset(), anchor_pos, on_done)


def open_row_tags(
    parent: QWidget,
    tags: frozenset[TagEnum],
    on_done: Callable[[frozenset[str] | None], None],
    anchor_pos: QPoint | None = None,
) -> None:
    """Open the modeless tag composer used to edit a single row's tags.

    Args:
        parent: The owning widget.
        tags: The row's current tag set.
        on_done: Called with the composed tag labels, or None on cancel.
        anchor_pos: Global position to open next to (the clicked cell), or None to center.
    """
    _open_tags(parent, tags, anchor_pos, on_done)


# EOF
