# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path

from tests.helpers_test import make_csv_service, make_project, write_csv
from wishlistor.shared.constants_util import (
    C_COL_CUSTOM_TAGS,
    C_COL_RANK_1234_SUMMED,
    C_COL_RANK_CUSTOM_TAGS,
    C_COL_RANK_NOTATION,
    C_COL_RANK_POPULARITY,
    C_COL_RANK_RELEASED,
    C_DEFAULT_DATETIME_STR_CSV,
)
from wishlistor.shared.errors.csv_error import ErrorCodeCsv

_HEADER = f"__primary_key__;rel;pop;score;{C_COL_CUSTOM_TAGS}"


def _load(tmp_path: Path, lines: list[str], with_mapping: bool = True) -> tuple[object, object, object]:
    """Load a document and return (document, project, result)."""
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, lines)
    project = make_project(csv_path)
    if not with_mapping:
        project.released_column = ""
        project.popularity_column = ""
        project.scoring_column = ""
    document, result = make_csv_service().load(project)
    return document, project, result


def _column(document: object, name: str) -> list[str]:
    """Return every cell of a column, in file order."""
    col = document.column_index(name)  # type: ignore[attr-defined]
    return [row[col] for row in document.rows]  # type: ignore[attr-defined]


def test_rank_released_is_one_for_most_recent(tmp_path: Path) -> None:
    lines = [_HEADER, "a;2024-01-01 00:00:00;0;0;", "b;2025-06-01 00:00:00;0;0;", "c;2020-01-01 00:00:00;0;0;"]
    document, _project, _result = _load(tmp_path, lines)
    assert _column(document, C_COL_RANK_RELEASED) == ["2", "1", "3"]


def test_rank_popularity_is_one_for_lowest_value(tmp_path: Path) -> None:
    lines = [_HEADER, "a;2024-01-01 00:00:00;10;0;", "b;2024-01-01 00:00:00;5;0;", "c;2024-01-01 00:00:00;99;0;"]
    document, _project, _result = _load(tmp_path, lines)
    assert _column(document, C_COL_RANK_POPULARITY) == ["2", "1", "3"]


def test_rank_notation_is_one_for_worst_score(tmp_path: Path) -> None:
    lines = [_HEADER, "a;2024-01-01 00:00:00;0;50;", "b;2024-01-01 00:00:00;0;10;", "c;2024-01-01 00:00:00;0;80;"]
    document, _project, _result = _load(tmp_path, lines)
    assert _column(document, C_COL_RANK_NOTATION) == ["2", "1", "3"]


def test_missing_source_values_are_substituted_and_reported(tmp_path: Path) -> None:
    lines = [_HEADER, "a;;;;", "b;2024-01-01 00:00:00;5;3;"]
    document, _project, result = _load(tmp_path, lines)
    rel_col = document.column_index("rel")  # type: ignore[attr-defined]
    pop_col = document.column_index("pop")  # type: ignore[attr-defined]
    assert document.rows[0][rel_col] == C_DEFAULT_DATETIME_STR_CSV  # type: ignore[attr-defined]
    assert document.rows[0][pop_col] == "0"  # type: ignore[attr-defined]
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1011) >= 2  # type: ignore[attr-defined]


def test_unmapped_columns_yield_sequential_ranks_and_warning(tmp_path: Path) -> None:
    lines = [_HEADER, "a;;;;", "b;;;;", "c;;;;"]
    document, _project, result = _load(tmp_path, lines, with_mapping=False)
    assert _column(document, C_COL_RANK_RELEASED) == ["1", "2", "3"]
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1017) == 3  # type: ignore[attr-defined]


def test_rank_custom_tags_uses_project_weights_times_row_count(tmp_path: Path) -> None:
    lines = [_HEADER, "a;;0;0;A faire", "b;;0;0;", "c;;0;0;Archivé", "d;;0;0;"]
    document, _project, _result = _load(tmp_path, lines)
    # N = 4 : pas de tag -> 0 ; Archivé (-100%) -> -4.
    values = _column(document, C_COL_RANK_CUSTOM_TAGS)
    assert values[1] == "0"
    assert values[2] == "-4"


def test_summed_rank_is_the_sum_of_the_four_ranks(tmp_path: Path) -> None:
    lines = [_HEADER, "a;2024-01-01 00:00:00;10;5;", "b;2025-01-01 00:00:00;5;1;"]
    document, _project, _result = _load(tmp_path, lines)
    for row_index in range(2):
        expected = sum(
            int(_column(document, name)[row_index])
            for name in (C_COL_RANK_RELEASED, C_COL_RANK_POPULARITY, C_COL_RANK_NOTATION, C_COL_RANK_CUSTOM_TAGS)
        )
        assert int(_column(document, C_COL_RANK_1234_SUMMED)[row_index]) == expected


def test_recompute_after_tag_edit_updates_rank_custom_tags(tmp_path: Path) -> None:
    lines = [_HEADER, "a;2024-01-01 00:00:00;0;0;", "b;2024-01-01 00:00:00;0;0;"]
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, lines)
    project = make_project(csv_path)
    service = make_csv_service()
    document, _result = service.load(project)
    assert document is not None
    service.edit_cell(document, project, 0, C_COL_CUSTOM_TAGS, "Archivé")
    values = _column(document, C_COL_RANK_CUSTOM_TAGS)
    assert values[0] == "-2"  # -100% de N=2


# EOF
