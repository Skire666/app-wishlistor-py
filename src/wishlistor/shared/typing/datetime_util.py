# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from datetime import datetime

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_TIME_FORMAT_HH_MM_SS = "%H:%M:%S"
C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS = "%Y-%m-%d %H:%M:%S"
C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM = "%Y-%m-%d %H:%M"
C_DATE_FORMAT_DD_MM_YYYY = "%d/%m/%Y"

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def get_datetime_now() -> datetime:
    """Return the current date and time as a datetime object.

    Returns:
        The current datetime.
    """
    return datetime.now()


def get_datetime_now_yyyy_mm_dd_hh_mm() -> str:
    """Return the current date and time formatted as '2024-06-01 14:30'.

    Returns:
        A string representing the current date and time.
    """
    return datetime.now().strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM)


def get_datetime_now_yyyy_mm_dd_hh_mm_ss() -> str:
    """Return the current date and time formatted as '2024-06-01 14:30:45'.

    Returns:
        A string representing the current date and time.
    """
    return datetime.now().strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS)


# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def format_datetime_to_yyyy_mm_dd_hh_mm(value: datetime) -> str:
    """Format *value* as '2024-06-01 14:30'.

    Args:
        value: The datetime to format.

    Returns:
        The formatted string.
    """
    return value.strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM)


def safe_datetime_from_str(value: str | None, default: datetime) -> datetime:
    """Parse an ISO 8601 string into a datetime, returning the default on failure.

    Args:
        value: Any object; only str values can be parsed.
        default: The datetime to return if parsing fails.

    Returns:
        The parsed datetime, or the default.
    """
    if value is None:
        return default
    cleaned = value.strip()
    if not cleaned:
        return default
    try:
        return datetime.fromisoformat(value)
    except ValueError, TypeError:
        return default


# EOF
