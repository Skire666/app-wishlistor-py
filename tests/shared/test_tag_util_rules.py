# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from wishlistor.shared.enums.tag_enum import TagEnum
from wishlistor.shared.tag_util import apply_check, apply_uncheck, clean_tags, serialize_tags


def test_check_a_faire_unchecks_closed_tags_and_adds_favoris() -> None:
    tags = frozenset({TagEnum.E_TERMINE, TagEnum.E_ARCHIVE})
    result = apply_check(tags, TagEnum.E_A_FAIRE)
    assert result == frozenset({TagEnum.E_A_FAIRE, TagEnum.E_FAVORIS})


def test_check_termine_unchecks_active_and_abandonne() -> None:
    tags = frozenset({TagEnum.E_A_FAIRE, TagEnum.E_ABANDONNE, TagEnum.E_FAVORIS})
    result = apply_check(tags, TagEnum.E_TERMINE)
    assert result == frozenset({TagEnum.E_TERMINE, TagEnum.E_FAVORIS})


def test_check_ignore_unchecks_everything_except_favoris() -> None:
    tags = frozenset({TagEnum.E_FAVORIS, TagEnum.E_EN_COURS})
    result = apply_check(tags, TagEnum.E_IGNORE)
    assert result == frozenset({TagEnum.E_IGNORE, TagEnum.E_FAVORIS})


def test_check_archive_keeps_termine() -> None:
    tags = frozenset({TagEnum.E_TERMINE})
    result = apply_check(tags, TagEnum.E_ARCHIVE)
    assert result == frozenset({TagEnum.E_TERMINE, TagEnum.E_ARCHIVE})


def test_check_favoris_cascades_nothing() -> None:
    tags = frozenset({TagEnum.E_TERMINE})
    result = apply_check(tags, TagEnum.E_FAVORIS)
    assert result == frozenset({TagEnum.E_TERMINE, TagEnum.E_FAVORIS})


def test_uncheck_never_cascades() -> None:
    tags = frozenset({TagEnum.E_A_FAIRE, TagEnum.E_FAVORIS})
    result = apply_uncheck(tags, TagEnum.E_A_FAIRE)
    assert result == frozenset({TagEnum.E_FAVORIS})


def test_active_tag_auto_checks_favoris() -> None:
    result = apply_check(frozenset(), TagEnum.E_EN_COURS)
    assert TagEnum.E_FAVORIS in result


def test_clean_tags_drops_foreign_segments_and_reports_them() -> None:
    retained, dropped = clean_tags("Favoris||Bidule||Terminé")
    assert retained == frozenset({TagEnum.E_FAVORIS, TagEnum.E_TERMINE})
    assert dropped == ["Bidule"]


def test_clean_tags_first_read_wins_on_conflicts() -> None:
    retained, dropped = clean_tags("Ignoré||Favoris||A faire")
    assert retained == frozenset({TagEnum.E_IGNORE, TagEnum.E_FAVORIS})
    assert dropped == ["A faire"]


def test_clean_tags_termine_and_abandonne_never_coexist() -> None:
    retained, dropped = clean_tags("Terminé||Abandonné")
    assert retained == frozenset({TagEnum.E_TERMINE})
    assert dropped == ["Abandonné"]


def test_clean_tags_drops_duplicates_and_empty_segments_silently() -> None:
    retained, dropped = clean_tags("Favoris||||Favoris")
    assert retained == frozenset({TagEnum.E_FAVORIS})
    assert dropped == []


def test_clean_tags_adds_favoris_when_active_tag_present() -> None:
    retained, _dropped = clean_tags("A faire")
    assert retained == frozenset({TagEnum.E_A_FAIRE, TagEnum.E_FAVORIS})


def test_serialize_tags_uses_canonical_order_and_double_pipe() -> None:
    value = serialize_tags({TagEnum.E_TERMINE, TagEnum.E_FAVORIS})
    assert value == "Favoris||Terminé"


def test_serialize_empty_set_is_empty_string() -> None:
    assert serialize_tags(frozenset()) == ""


# EOF
