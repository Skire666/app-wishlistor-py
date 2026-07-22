# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from wishlistor.models.undo_action_model import UndoActionModel
from wishlistor.services.undo_service import UndoService
from wishlistor.shared.enums.undo_action_enum import UndoActionEnum


def _action() -> UndoActionModel:
    return UndoActionModel(kind=UndoActionEnum.E_CELL_EDIT)


def test_undo_redo_round_trip() -> None:
    service = UndoService()
    action = _action()
    service.push(action)
    assert service.can_undo()
    assert service.undo() is action
    assert service.can_redo()
    assert service.redo() is action


def test_push_clears_the_redo_branch() -> None:
    service = UndoService()
    service.push(_action())
    service.undo()
    service.push(_action())
    assert not service.can_redo()


def test_limit_drops_the_oldest_actions() -> None:
    service = UndoService()
    service.set_limit(2)
    first = _action()
    service.push(first)
    service.push(_action())
    service.push(_action())
    assert service.undo() is not None
    assert service.undo() is not None
    assert service.undo() is None  # `first` was trimmed


def test_limit_is_clamped_to_bounds() -> None:
    service = UndoService()
    service.set_limit(999)
    for _index in range(31):
        service.push(_action())
    undone = 0
    while service.undo() is not None:
        undone += 1
    assert undone == 30


def test_clean_state_tracking_through_undo_and_redo() -> None:
    service = UndoService()
    assert service.is_at_clean_state()
    service.push(_action())
    assert not service.is_at_clean_state()
    service.undo()
    assert service.is_at_clean_state()
    service.redo()
    service.mark_clean()
    assert service.is_at_clean_state()
    service.undo()
    assert not service.is_at_clean_state()


def test_clean_state_becomes_unreachable_when_future_is_discarded() -> None:
    service = UndoService()
    service.push(_action())
    service.mark_clean()
    service.undo()
    service.push(_action())  # discards the redo branch holding the clean state
    service.undo()
    assert not service.is_at_clean_state()


def test_clear_resets_everything() -> None:
    service = UndoService()
    service.push(_action())
    service.clear()
    assert not service.can_undo()
    assert not service.can_redo()
    assert service.is_at_clean_state()


# EOF
