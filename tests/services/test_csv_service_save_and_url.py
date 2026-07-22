# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path

from wishlistor.shared.constants_util import C_COL_CUSTOM_COMMENTS, C_COL_RANK_RELEASED
from wishlistor.shared.errors.csv_error import ErrorCodeCsv
from tests.helpers_test import make_csv_service, make_project, write_csv

_HEADER = "__primary_key__;rel;pop;score"


def test_save_preserves_row_order_and_normalizes_values(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, "b;2025-01-01 00:00:00;;3", "a;2024-01-01 00:00:00;7;1"])
    service = make_csv_service()
    project = make_project(csv_path)
    document, _result = service.load(project)
    assert document is not None
    saved, result = service.save(document, False)
    assert saved
    assert not result.has_errors_or_fatals()
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert lines[1].startswith("b;")  # original order preserved
    assert lines[2].startswith("a;")
    assert ";0;" in lines[1]  # empty popularity normalized to the default


def test_save_detects_external_modification(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, "a;2024-01-01 00:00:00;1;1"])
    service = make_csv_service()
    document, _result = service.load(make_project(csv_path))
    assert document is not None
    write_csv(csv_path, [_HEADER, "a;2024-01-01 00:00:00;1;1", "z;2024-01-01 00:00:00;2;2"])
    saved, result = service.save(document, False)
    assert not saved
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1012) == 1
    saved_forced, _result = service.save(document, True)
    assert saved_forced


def test_save_as_updates_document_path(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, "a;2024-01-01 00:00:00;1;1"])
    service = make_csv_service()
    document, _result = service.load(make_project(csv_path))
    assert document is not None
    new_path = tmp_path / "copy.csv"
    result = service.save_as(document, str(new_path))
    assert not result.has_errors_or_fatals()
    assert document.csv_path == str(new_path)
    assert new_path.is_file()


def test_add_url_appends_row_at_the_end_with_defaults(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, "a;2024-01-01 00:00:00;1;1"])
    service = make_csv_service()
    project = make_project(csv_path)
    document, _result = service.load(project)
    assert document is not None
    row_index, result = service.add_url(document, project, "https://exemple.org/page")
    assert row_index == 1
    assert not result.has_errors_or_fatals()
    primary_col = document.column_index("__primary_key__")
    assert document.rows[1][primary_col] == "https://exemple.org/page"
    rank_col = document.column_index(C_COL_RANK_RELEASED)
    assert document.rows[1][rank_col] != ""  # ranks recomputed, no empty rank cell
    assert document.is_dirty


def test_add_url_strict_duplicate_is_rejected(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, "https://exemple.org;2024-01-01 00:00:00;1;1"])
    service = make_csv_service()
    project = make_project(csv_path)
    document, _result = service.load(project)
    assert document is not None
    row_index, result = service.add_url(document, project, "https://exemple.org")
    assert row_index == 0  # existing row returned for focusing
    assert result.count_severities_by_code(ErrorCodeCsv.CSV_1016) == 1
    assert len(document) == 1
    # strict comparison: a case variant is a different value
    row_index_2, result_2 = service.add_url(document, project, "https://EXEMPLE.org")
    assert row_index_2 == 1
    assert result_2.count_severities_by_code(ErrorCodeCsv.CSV_1016) == 0


def test_save_marks_history_clean_and_resets_dirty(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    write_csv(csv_path, [_HEADER, "a;2024-01-01 00:00:00;1;1"])
    service = make_csv_service()
    project = make_project(csv_path)
    document, _result = service.load(project)
    assert document is not None
    service.edit_cell(document, project, 0, C_COL_CUSTOM_COMMENTS, "note")
    assert document.is_dirty
    saved, _result = service.save(document, False)
    assert saved
    assert not document.is_dirty
    assert service.is_clean()


# EOF
