"""Parsing helpers shared across layers (pure Python, no UI dependency)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations


def safe_int_from_str(value: str | None, default: int) -> int:
    """Convert a value to an integer, falling back to *default* on failure.

    Args:
        value: The value to convert.
        default: Value returned when the input is non-numeric.

    Returns:
        Integer value or ``default``.
    """
    if value is None:
        return default
    cleaned = value.strip()
    if not cleaned:
        return default
    try:
        return int(cleaned)
    except ValueError, TypeError:
        return default


# EOF
