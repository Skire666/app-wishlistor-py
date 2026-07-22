"""Immutable value objects describing one undoable write action (spec E)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass, field

from wishlistor.shared.enums.undo_action_enum import UndoActionEnum


@dataclass(frozen=True)
class CellChange:
    """One cell mutation, kept with both values so it can be undone exactly."""

    row_index: int
    column_index: int
    old_value: str
    new_value: str


@dataclass(frozen=True)
class RowSnapshot:
    """A full row captured before insertion or deletion, with its file position."""

    row_index: int
    values: tuple[str, ...]


@dataclass(frozen=True)
class UndoActionModel:
    """One atomic user write action (a mass edit counts as a single action)."""

    kind: UndoActionEnum = UndoActionEnum.E_UNSET
    changes: tuple[CellChange, ...] = field(default_factory=tuple)
    rows: tuple[RowSnapshot, ...] = field(default_factory=tuple)


# EOF
