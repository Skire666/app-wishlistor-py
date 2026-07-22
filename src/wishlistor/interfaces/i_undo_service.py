# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol

from wishlistor.models.undo_action_model import UndoActionModel


class IUndoService(Protocol):
    """Bounded history of write actions (spec E). Pure Python, no Qt."""

    def set_limit(self, limit: int) -> None:
        """Set the maximum number of undoable actions.

        Args:
            limit: Maximum history depth (1..30).
        """
        ...

    def push(self, action: UndoActionModel) -> None:
        """Record a new write action (clears the redo branch).

        Args:
            action: The action just applied.
        """
        ...

    def can_undo(self) -> bool:
        """Return True when at least one action can be undone."""
        ...

    def can_redo(self) -> bool:
        """Return True when at least one action can be redone."""
        ...

    def undo(self) -> UndoActionModel | None:
        """Pop the latest action for undoing, or None."""
        ...

    def redo(self) -> UndoActionModel | None:
        """Pop the latest undone action for redoing, or None."""
        ...

    def is_at_clean_state(self) -> bool:
        """Return True when every applied action has been undone since the clean mark."""
        ...

    def mark_clean(self) -> None:
        """Mark the current position as the clean (saved) state."""
        ...

    def clear(self) -> None:
        """Drop the whole history (project switch)."""
        ...


# EOF
