"""Bounded undo/redo history of write actions (spec E). Pure Python, no Qt."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import uuid

from wishlistor.models.undo_action_model import UndoActionModel
from wishlistor.shared.constants_util import C_UNDO_DEFAULT, C_UNDO_MAX, C_UNDO_MIN


class UndoService:
    """Keeps the last N write actions and tracks the clean (saved) position."""

    def __init__(self) -> None:
        """Initialize an empty history with the default depth."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._limit: int = C_UNDO_DEFAULT
        self._undo_stack: list[UndoActionModel] = []
        self._redo_stack: list[UndoActionModel] = []
        self._position: int = 0  # monotonic counter of applied actions
        self._clean_position: int = 0  # -1 when the saved state became unreachable

    @staticmethod
    def generate_id() -> str:
        """Return a new unique identifier for an undo transaction."""
        return str(uuid.uuid4())

    def set_limit(self, limit: int) -> None:
        """Set the maximum number of undoable actions (clamped to 1..30).

        Args:
            limit: Maximum history depth.
        """
        self._limit = max(C_UNDO_MIN, min(C_UNDO_MAX, limit))
        self._trim()

    def push(self, action: UndoActionModel) -> None:
        """Record a new write action (clears the redo branch).

        Args:
            action: The action just applied.
        """
        if self._redo_stack and self._clean_position > self._position:
            self._clean_position = -1  # the saved state was in the discarded future
        self._redo_stack.clear()
        self._undo_stack.append(action)
        self._position += 1
        self._trim()

    def _trim(self) -> None:
        """Drop the oldest actions when the stack exceeds the limit."""
        while len(self._undo_stack) > self._limit:
            self._undo_stack.pop(0)

    def can_undo(self) -> bool:
        """Return True when at least one action can be undone."""
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        """Return True when at least one action can be redone."""
        return bool(self._redo_stack)

    def undo(self) -> UndoActionModel | None:
        """Pop the latest action for undoing, or None."""
        if not self._undo_stack:
            return None
        action = self._undo_stack.pop()
        self._redo_stack.append(action)
        self._position -= 1
        return action

    def redo(self) -> UndoActionModel | None:
        """Pop the latest undone action for redoing, or None."""
        if not self._redo_stack:
            return None
        action = self._redo_stack.pop()
        self._undo_stack.append(action)
        self._position += 1
        return action

    def is_at_clean_state(self) -> bool:
        """Return True when the document matches the last saved position."""
        return self._position == self._clean_position

    def mark_clean(self) -> None:
        """Mark the current position as the clean (saved) state."""
        self._clean_position = self._position

    def clear(self) -> None:
        """Drop the whole history (project switch)."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._position = 0
        self._clean_position = 0


# EOF
