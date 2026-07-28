"""Tag parsing, serialization and single-active-tag rules (spec B.4.3 / D.4).

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

# The six real tags, in canonical display and serialization order.
C_ALL_TAGS: Final[tuple[TagEnum, ...]] = (
    TagEnum.E_A_FAIRE,
    TagEnum.E_EN_COURS,
    TagEnum.E_TERMINE,
    TagEnum.E_ABANDONNE,
    TagEnum.E_ARCHIVE,
    TagEnum.E_IGNORE,
)

# Fixed pill background colors (white text on top), one distinct color per tag.
C_TAG_COLORS: Final[dict[TagEnum, str]] = {
    TagEnum.E_A_FAIRE: "#BA9310",
    TagEnum.E_EN_COURS: "#1D7CCE",
    TagEnum.E_TERMINE: "#439E46",
    TagEnum.E_ABANDONNE: "#BD3836",
    TagEnum.E_ARCHIVE: "#757575",
    TagEnum.E_IGNORE: "#602684",
}

_LABEL_TO_TAG: Final[dict[str, TagEnum]] = {tag.value: tag for tag in C_ALL_TAGS}

# Default tag weights, as fractions of N: +10% -> 0.10.
C_DEFAULT_TAG_WEIGHTS: Final[dict[str, float]] = {
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


def clean_tags(cell_value: str) -> tuple[frozenset[TagEnum], list[str]]:
    """Parse and strictly clean a raw `__custom_tags__` cell (spec D.4).

    Only one tag can be active on a row: the first recognized segment is
    retained, every other segment (foreign, or a second recognized tag) is
    dropped and reported. Duplicates and empty segments are dropped silently.

    Args:
        cell_value: Raw cell content, `||`-separated.

    Returns:
        A tuple ``(retained tag, dropped segment labels)`` where the first
        element holds at most one tag, and the second only contains segments
        worth a WARNING log.
    """
    retained: TagEnum | None = None
    dropped: list[str] = []
    for segment in cell_value.split(C_TAG_SEPARATOR):
        label = segment.strip()
        if not label:
            continue
        tag = tag_from_label(label)
        if tag is TagEnum.E_UNKNOWN:
            dropped.append(label)
        elif tag is retained:
            continue
        elif retained is None:
            retained = tag
        else:
            dropped.append(label)
    return (frozenset({retained}) if retained is not None else frozenset()), dropped


def apply_check(tags: frozenset[TagEnum], tag: TagEnum) -> frozenset[TagEnum]:
    """Check *tag*, replacing any tag already active (only one tag at a time).

    Args:
        tags: Current tag set (ignored: checking a tag always replaces it entirely).
        tag: Tag being checked by the user.

    Returns:
        A tag set containing only *tag*.
    """
    _ = tags
    return frozenset({tag})


def apply_uncheck(tags: frozenset[TagEnum], tag: TagEnum) -> frozenset[TagEnum]:
    """Uncheck *tag* on a tag set.

    Args:
        tags: Current tag set (holds at most one tag).
        tag: Tag being unchecked by the user.

    Returns:
        An empty set when *tag* was the active one, the input set unchanged otherwise.
    """
    return frozenset() if tag in tags else tags


# EOF
