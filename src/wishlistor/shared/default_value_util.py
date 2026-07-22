"""Ordered list and key resolution for the column default-value picker (spec §2)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Final

from wishlistor.shared.enums.default_value_enum import DefaultValueEnum

# The five default-value choices, in canonical display order. Extensible without
# changing the widget logic (spec §2).
C_ALL_DEFAULT_VALUES: Final[tuple[DefaultValueEnum, ...]] = (
    DefaultValueEnum.E_DATE_1900,
    DefaultValueEnum.E_DATE_TODAY,
    DefaultValueEnum.E_COUNT_ZERO,
    DefaultValueEnum.E_TOTAL_ROW_COUNT,
    DefaultValueEnum.E_EXTRACTOR_E0,
)

_KEY_TO_DEFAULT_VALUE: Final[dict[str, DefaultValueEnum]] = {item.value: item for item in C_ALL_DEFAULT_VALUES}


def default_value_from_key(key: str) -> DefaultValueEnum:
    """Resolve a serialized key into a default-value choice.

    Args:
        key: Raw key read from the project configuration.

    Returns:
        The matching choice, or ``DefaultValueEnum.E_UNKNOWN`` for foreign data.
    """
    return _KEY_TO_DEFAULT_VALUE.get(key.strip(), DefaultValueEnum.E_UNKNOWN)


# EOF
