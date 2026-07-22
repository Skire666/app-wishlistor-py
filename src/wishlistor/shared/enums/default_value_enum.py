# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class DefaultValueEnum(Enum):
    """Enumerates the fixed, extensible list of column default-value substitutions (spec §2)."""

    E_UNSET = "UNSET"
    E_DATE_1900 = "date_1900"
    E_DATE_TODAY = "date_today"
    E_COUNT_ZERO = "count_zero"
    E_TOTAL_ROW_COUNT = "total_row_count"
    E_EXTRACTOR_E0 = "extractor_e0"
    E_UNKNOWN = "UNKNOWN"


# EOF
