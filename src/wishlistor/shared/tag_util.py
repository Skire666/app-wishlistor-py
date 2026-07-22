"""Tag parsing, serialization, cascade and invariant rules (spec B.4.3 / D.4).

The tag list is hardcoded and frozen. These helpers are pure functions shared
by services (cleanup, mass edits) and views (rendering, tag selector).
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Final

from wishlistor.shared.constants_util import C_TAG_SEPARATOR
from wishlistor.shared.enums.tag_enum import TagEnum

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# The seven real tags, in canonical display and serialization order.
C_ALL_TAGS: Final[tuple[TagEnum, ...]] = (
    TagEnum.E_FAVORIS,
    TagEnum.E_A_FAIRE,
    TagEnum.E_EN_COURS,
    TagEnum.E_TERMINE,
    TagEnum.E_ABANDONNE,
    TagEnum.E_ARCHIVE,
    TagEnum.E_IGNORE,
)

# Active group vs closed group (spec B.4.3 invariants).
C_ACTIVE_TAGS: Final[frozenset[TagEnum]] = frozenset({TagEnum.E_A_FAIRE, TagEnum.E_EN_COURS})
C_CLOSED_TAGS: Final[frozenset[TagEnum]] = frozenset(
    {TagEnum.E_TERMINE, TagEnum.E_ABANDONNE, TagEnum.E_ARCHIVE, TagEnum.E_IGNORE}
)

# Tags automatically unchecked when the key tag gets checked (spec B.4.3).
C_CHECK_CASCADE: Final[dict[TagEnum, frozenset[TagEnum]]] = {
    TagEnum.E_FAVORIS: frozenset(),
    TagEnum.E_A_FAIRE: C_CLOSED_TAGS,
    TagEnum.E_EN_COURS: C_CLOSED_TAGS,
    TagEnum.E_TERMINE: frozenset({TagEnum.E_A_FAIRE, TagEnum.E_EN_COURS, TagEnum.E_ABANDONNE}),
    TagEnum.E_ABANDONNE: frozenset({TagEnum.E_A_FAIRE, TagEnum.E_EN_COURS, TagEnum.E_TERMINE, TagEnum.E_IGNORE}),
    TagEnum.E_ARCHIVE: frozenset({TagEnum.E_A_FAIRE, TagEnum.E_EN_COURS, TagEnum.E_IGNORE}),
    TagEnum.E_IGNORE: frozenset(set(C_ALL_TAGS) - {TagEnum.E_FAVORIS, TagEnum.E_IGNORE}),
}

# Fixed pill background colors (white text on top), one distinct color per tag.
C_TAG_COLORS: Final[dict[TagEnum, str]] = {
    TagEnum.E_FAVORIS: "#C69C11",
    TagEnum.E_A_FAIRE: "#1F81D7",
    TagEnum.E_EN_COURS: "#007380",
    TagEnum.E_TERMINE: "#4CAF50",
    TagEnum.E_ABANDONNE: "#E53935",
    TagEnum.E_ARCHIVE: "#757575",
    TagEnum.E_IGNORE: "#6A1B9A",
}

_LABEL_TO_TAG: Final[dict[str, TagEnum]] = {tag.value: tag for tag in C_ALL_TAGS}

# Default tag weights, as fractions of N: +10% -> 0.10.
C_DEFAULT_TAG_WEIGHTS: Final[dict[str, float]] = {
    TagEnum.E_FAVORIS.value: 0.20,
    TagEnum.E_A_FAIRE.value: 0.40,
    TagEnum.E_EN_COURS.value: 0.80,
    TagEnum.E_TERMINE.value: -0.50,
    TagEnum.E_ABANDONNE.value: -0.75,
    TagEnum.E_ARCHIVE.value: -1.00,
    TagEnum.E_IGNORE.value: -1.00,
}

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def tag_from_label(label: str) -> TagEnum:
    """Resolve a serialized segment into a tag.

    Args:
        label: Raw segment read from a `__custom_tags__` cell.

    Returns:
        The matching tag, or ``TagEnum.E_UNKNOWN`` for foreign data.
    """
    return _LABEL_TO_TAG.get(label.strip(), TagEnum.E_UNKNOWN)


def serialize_tags(tags: frozenset[TagEnum] | set[TagEnum]) -> str:
    """Serialize a tag set into its canonical `||`-joined cell value.

    Args:
        tags: Tags to serialize.

    Returns:
        The joined string, empty when no tag is present.
    """
    return C_TAG_SEPARATOR.join(tag.value for tag in C_ALL_TAGS if tag in tags)


def is_tag_compatible(retained: frozenset[TagEnum], tag: TagEnum) -> bool:
    """Return True when *tag* can join *retained* without violating an invariant.

    Args:
        retained: Tags already retained (earlier segments win).
        tag: Candidate tag.

    Returns:
        False when the candidate breaks the active/closed exclusion or the
        Terminé/Abandonné exclusion.
    """
    if tag in C_ACTIVE_TAGS and retained & C_CLOSED_TAGS:
        return False
    if tag in C_CLOSED_TAGS and retained & C_ACTIVE_TAGS:
        return False
    if tag is TagEnum.E_TERMINE and TagEnum.E_ABANDONNE in retained:
        return False
    return not (tag is TagEnum.E_ABANDONNE and TagEnum.E_TERMINE in retained)


def _apply_favoris_invariant(tags: set[TagEnum]) -> frozenset[TagEnum]:
    """Auto-check Favoris when an active-group tag is present."""
    if tags & C_ACTIVE_TAGS:
        tags.add(TagEnum.E_FAVORIS)
    return frozenset(tags)


def clean_tags(cell_value: str) -> tuple[frozenset[TagEnum], list[str]]:
    """Parse and strictly clean a raw `__custom_tags__` cell (spec D.4).

    Duplicates and empty segments are dropped silently. Foreign segments and
    invariant conflicts (first tag read wins) are dropped and reported.

    Args:
        cell_value: Raw cell content, `||`-separated.

    Returns:
        A tuple ``(retained tags, dropped segment labels)`` where the second
        element only contains segments worth a WARNING log.
    """
    retained: set[TagEnum] = set()
    dropped: list[str] = []
    for segment in cell_value.split(C_TAG_SEPARATOR):
        label = segment.strip()
        if not label:
            continue
        tag = tag_from_label(label)
        if tag is TagEnum.E_UNKNOWN:
            dropped.append(label)
        elif tag not in retained:
            if is_tag_compatible(frozenset(retained), tag):
                retained.add(tag)
            else:
                dropped.append(label)
    return _apply_favoris_invariant(retained), dropped


def apply_check(tags: frozenset[TagEnum], tag: TagEnum) -> frozenset[TagEnum]:
    """Check *tag* on a tag set, applying the cascade and invariants.

    Args:
        tags: Current tag set.
        tag: Tag being checked by the user.

    Returns:
        The resulting tag set.
    """
    result = set(tags) - C_CHECK_CASCADE.get(tag, frozenset())
    result.add(tag)
    return _apply_favoris_invariant(result)


def apply_uncheck(tags: frozenset[TagEnum], tag: TagEnum) -> frozenset[TagEnum]:
    """Uncheck *tag* on a tag set. Unchecking never cascades (spec B.4.3).

    Args:
        tags: Current tag set.
        tag: Tag being unchecked by the user.

    Returns:
        The resulting tag set.
    """
    return frozenset(set(tags) - {tag})


# EOF
