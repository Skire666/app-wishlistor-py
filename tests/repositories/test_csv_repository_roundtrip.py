# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path

import pytest

from wishlistor.repositories.csv_repository import CsvRepository
from wishlistor.shared.exceptions.csv_structure_error import CsvStructureError


def test_write_atomic_then_read_all_round_trip(tmp_path: Path) -> None:
    repository = CsvRepository()
    path = tmp_path / "data.csv"
    header = ["a", "b"]
    rows = [["1", "avec;point-virgule"], ["2", 'avec "guillemets"']]
    repository.write_atomic(str(path), header, rows)
    read_header, read_rows = repository.read_all(str(path))
    assert read_header == header
    assert read_rows == rows


def test_write_atomic_returns_fresh_stats(tmp_path: Path) -> None:
    repository = CsvRepository()
    path = tmp_path / "data.csv"
    mtime, size = repository.write_atomic(str(path), ["a"], [["x"]])
    stats = repository.file_stats(str(path))
    assert stats is not None
    assert stats == (mtime, size)


def test_write_never_adds_a_bom(tmp_path: Path) -> None:
    repository = CsvRepository()
    path = tmp_path / "data.csv"
    repository.write_atomic(str(path), ["a"], [["é"]])
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")


def test_read_all_rejects_an_empty_file(tmp_path: Path) -> None:
    repository = CsvRepository()
    path = tmp_path / "vide.csv"
    path.write_bytes(b"")
    with pytest.raises(CsvStructureError):
        repository.read_all(str(path))


def test_file_stats_returns_none_for_missing_file(tmp_path: Path) -> None:
    assert CsvRepository().file_stats(str(tmp_path / "absent.csv")) is None


# EOF
