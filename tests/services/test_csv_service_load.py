# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path

from tests.helpers_test import make_csv_service, make_project, write_csv
from wishlistor.shared.constants_util import (
    C_COL_CUSTOM_COMMENTS,
    C_COL_CUSTOM_TAGS,
    C_COL_RANK_1234_SUMMED,
    C_COL_RANK_RELEASED,
)
from wishlistor.shared.errors.csv_error import ErrorCodeCsv

_HEADER = "__primary_key__;rel;pop;score"


def test_load_adds_special_and_rank_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, "a;2024-01-01 00:00:00;10;5"])
    service = make_csv_service()
    document, result = service.load(make_project(csv_path))
    assert document is not None
    assert not result.has_errors_or_fatals()
    assert C_COL_CUSTOM_TAGS in document.header
    assert C_COL_CUSTOM_COMMENTS in document.header
    assert C_COL_RANK_RELEASED in document.header
    assert not document.is_dirty


def test_load_header_only_csv_is_valid(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER])
    document, result = make_csv_service().load(make_project(csv_path))
    assert document is not None
    assert len(document) == 0
    assert not result.has_errors_or_fatals()


def test_load_missing_file_reports_csv_1001(tmp_path: Path) -> None:
    document, result = make_csv_service().load(make_project(tmp_path / "absent.csv"))
    assert document is None
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1001) == 1


def test_load_empty_file_reports_csv_1002(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    csv_path.write_bytes(b"")
    document, result = make_csv_service().load(make_project(csv_path))
    assert document is None
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1002) == 1


def test_load_duplicate_column_names_abort(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, ["__primary_key__;rel;rel", "a;1;2"])
    document, result = make_csv_service().load(make_project(csv_path))
    assert document is None
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1003) == 1


def test_load_unknown_dunder_column_is_tolerated(tmp_path: Path) -> None:
    # Décision propriétaire (2026-07-13) : plus de contrôle de glossaire sur les colonnes __.
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, ["__primary_key__;__mystere__", "a;x"])
    document, result = make_csv_service().load(make_project(csv_path))
    assert document is not None
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1004) == 0
    assert "__mystere__" in document.header


def test_load_duplicate_reference_values_abort_with_line_numbers(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, "a;;;", "a;;;"])
    document, result = make_csv_service().load(make_project(csv_path))
    assert document is None
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1006) == 1


def test_load_empty_reference_values_abort(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, ";;;"])
    document, result = make_csv_service().load(make_project(csv_path))
    assert document is None
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1007) == 1


def test_load_pads_and_truncates_inconsistent_rows_with_warning(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, "a;1", "b;2024-01-01 00:00:00;3;4;extra"])
    document, result = make_csv_service().load(make_project(csv_path))
    assert document is not None
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1008) == 2
    expected = len(document.header)
    assert all(len(row) == expected for row in document.rows)


def test_load_cleans_foreign_tags_with_warning(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(
        csv_path,
        [f"__primary_key__;rel;pop;score;{C_COL_CUSTOM_TAGS}", "a;2024-01-01 00:00:00;1;1;Terminé||Bidule"],
    )
    document, result = make_csv_service().load(make_project(csv_path))
    assert document is not None
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1010) == 1
    tags_col = document.column_index(C_COL_CUSTOM_TAGS)
    assert document.rows[0][tags_col] == "Terminé"


def test_load_existing_rank_column_is_replaced_with_warning(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [f"__primary_key__;rel;pop;score;{C_COL_RANK_RELEASED}", "a;2024-01-01 00:00:00;1;1;999"])
    document, result = make_csv_service().load(make_project(csv_path))
    assert document is not None
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1015) == 1
    rank_col = document.column_index(C_COL_RANK_RELEASED)
    assert document.rows[0][rank_col] == "1"


def test_load_bom_is_tolerated(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    csv_path.write_bytes(b"\xef\xbb\xbf__primary_key__;rel;pop;score\r\na;2024-01-01 00:00:00;1;1\r\n")
    document, _result = make_csv_service().load(make_project(csv_path))
    assert document is not None
    assert document.header[0] == "__primary_key__"


def test_load_computes_summed_rank_for_every_row(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, "a;2024-01-01 00:00:00;10;5", "b;2025-01-01 00:00:00;5;1"])
    document, _result = make_csv_service().load(make_project(csv_path))
    assert document is not None
    summed_col = document.column_index(C_COL_RANK_1234_SUMMED)
    assert all(row[summed_col] for row in document.rows)


# EOF
