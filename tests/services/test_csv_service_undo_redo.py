# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path

from wishlistor.shared.constants_util import C_COL_CUSTOM_COMMENTS, C_COL_RANK_RELEASED
from tests.helpers_test import make_csv_service, make_project, write_csv

_HEADER = "__primary_key__;rel;pop;score"


def _setup(tmp_path: Path, lines: list[str]) -> tuple[object, object, object]:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, lines)
    service = make_csv_service()
    project = make_project(csv_path)
    document, _result = service.load(project)
    assert document is not None
    return service, project, document


def test_undo_restores_the_exact_previous_cell_value(tmp_path: Path) -> None:
    service, project, document = _setup(tmp_path, [_HEADER, "a;2024-01-01 00:00:00;1;1"])
    comments_col = document.column_index(C_COL_CUSTOM_COMMENTS)  # type: ignore[attr-defined]
    service.edit_cell(document, project, 0, C_COL_CUSTOM_COMMENTS, "note")  # type: ignore[attr-defined]
    assert service.undo(document, project)  # type: ignore[attr-defined]
    assert document.rows[0][comments_col] == ""  # type: ignore[attr-defined]
    assert not document.is_dirty  # type: ignore[attr-defined]
    assert service.redo(document, project)  # type: ignore[attr-defined]
    assert document.rows[0][comments_col] == "note"  # type: ignore[attr-defined]
    assert document.is_dirty  # type: ignore[attr-defined]


def test_undo_of_add_url_removes_the_row_and_recomputes_ranks(tmp_path: Path) -> None:
    service, project, document = _setup(tmp_path, [_HEADER, "a;2024-01-01 00:00:00;1;1"])
    service.add_url(document, project, "https://exemple.org")  # type: ignore[attr-defined]
    assert len(document) == 2  # type: ignore[arg-type]
    assert service.undo(document, project)  # type: ignore[attr-defined]
    assert len(document) == 1  # type: ignore[arg-type]
    rank_col = document.column_index(C_COL_RANK_RELEASED)  # type: ignore[attr-defined]
    assert document.rows[0][rank_col] == "1"  # type: ignore[attr-defined]
    assert service.redo(document, project)  # type: ignore[attr-defined]
    assert len(document) == 2  # type: ignore[arg-type]


def test_delete_rows_can_be_undone_at_their_original_positions(tmp_path: Path) -> None:
    lines = [_HEADER, "a;2024-01-01 00:00:00;1;1", "b;2024-01-01 00:00:00;2;2", "c;2024-01-01 00:00:00;3;3"]
    service, project, document = _setup(tmp_path, lines)
    primary_col = document.column_index("__primary_key__")  # type: ignore[attr-defined]
    service.delete_rows(document, project, [0, 2])  # type: ignore[attr-defined]
    assert [row[primary_col] for row in document.rows] == ["b"]  # type: ignore[attr-defined]
    assert service.undo(document, project)  # type: ignore[attr-defined]
    assert [row[primary_col] for row in document.rows] == ["a", "b", "c"]  # type: ignore[attr-defined]


# EOF
