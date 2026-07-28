# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from wishlistor.models.csv_document_model import CsvDocumentModel
from wishlistor.shared.constants_util import C_COL_CUSTOM_TAGS
from wishlistor.shared.enums.tag_enum import TagEnum


def _document() -> CsvDocumentModel:
    document = CsvDocumentModel()
    document.csv_path = "test.csv"
    document.header = ["__primary_key__", "titre", C_COL_CUSTOM_TAGS]
    document.rows.extend(
        [["a", "Bonjour Monde", "A faire"], ["b", "Autre chose", ""], ["c", "bonjour encore", ""]]
    )
    document.set_search_columns(["titre"])
    return document


def test_search_is_case_insensitive_over_indexed_columns() -> None:
    assert _document().search("bonjour") == [0, 2]


def test_search_ignores_non_indexed_columns() -> None:
    assert _document().search("a") != [0]  # 'a' only exists in the non-indexed key column
    assert _document().search("chose") == [1]


def test_set_cell_refreshes_the_search_index_and_tags() -> None:
    document = _document()
    document.set_cell(1, 1, "Bonjour aussi")
    assert document.search("bonjour") == [0, 1, 2]
    document.set_cell(1, 2, "Archivé")
    assert document.tag_sets[1] == frozenset({TagEnum.E_ARCHIVE})
    assert document.is_dirty


def test_insert_and_remove_row_keep_caches_aligned() -> None:
    document = _document()
    document.insert_row(1, ["d", "bonjour inséré", "Terminé"])
    assert document.search("inséré") == [1]
    assert document.tag_sets[1] == frozenset({TagEnum.E_TERMINE})
    removed = document.remove_row(1)
    assert removed[0] == "d"
    assert len(document.tag_sets) == 3


def test_find_in_column_is_strict() -> None:
    document = _document()
    assert document.find_in_column(0, "a") == 0
    assert document.find_in_column(0, "A") == -1


# EOF
