# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from wishlistor.shared.enums.tag_enum import TagEnum
from wishlistor.shared.tag_util import apply_check, apply_uncheck, clean_tags, serialize_tags


def test_apply_check_replaces_any_previously_active_tag() -> None:
    tags = frozenset({TagEnum.E_TERMINE})
    result = apply_check(tags, TagEnum.E_A_FAIRE)
    assert result == frozenset({TagEnum.E_A_FAIRE})


def test_apply_check_on_empty_set_just_adds_the_tag() -> None:
    result = apply_check(frozenset(), TagEnum.E_EN_COURS)
    assert result == frozenset({TagEnum.E_EN_COURS})


def test_apply_check_same_tag_is_idempotent() -> None:
    tags = frozenset({TagEnum.E_IGNORE})
    result = apply_check(tags, TagEnum.E_IGNORE)
    assert result == frozenset({TagEnum.E_IGNORE})


def test_apply_uncheck_clears_the_active_tag() -> None:
    tags = frozenset({TagEnum.E_A_FAIRE})
    result = apply_uncheck(tags, TagEnum.E_A_FAIRE)
    assert result == frozenset()


def test_apply_uncheck_ignores_a_tag_that_is_not_active() -> None:
    tags = frozenset({TagEnum.E_A_FAIRE})
    result = apply_uncheck(tags, TagEnum.E_TERMINE)
    assert result == frozenset({TagEnum.E_A_FAIRE})


def test_clean_tags_drops_foreign_segments_and_reports_them() -> None:
    retained, dropped = clean_tags("Terminé||Bidule")
    assert retained == frozenset({TagEnum.E_TERMINE})
    assert dropped == ["Bidule"]


def test_clean_tags_keeps_only_the_first_recognized_tag() -> None:
    retained, dropped = clean_tags("Ignoré||A faire")
    assert retained == frozenset({TagEnum.E_IGNORE})
    assert dropped == ["A faire"]


def test_clean_tags_drops_duplicates_and_empty_segments_silently() -> None:
    retained, dropped = clean_tags("Terminé||||Terminé")
    assert retained == frozenset({TagEnum.E_TERMINE})
    assert dropped == []


def test_clean_tags_empty_cell_yields_no_tag() -> None:
    retained, dropped = clean_tags("")
    assert retained == frozenset()
    assert dropped == []


def test_serialize_tags_uses_canonical_order_and_double_pipe() -> None:
    value = serialize_tags({TagEnum.E_ARCHIVE, TagEnum.E_A_FAIRE})
    assert value == "A faire||Archivé"


def test_serialize_empty_set_is_empty_string() -> None:
    assert serialize_tags(frozenset()) == ""


# EOF
