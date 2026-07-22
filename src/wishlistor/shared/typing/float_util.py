"""Parsing helpers shared across layers (pure Python, no UI dependency)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations


def safe_float_from_str(value: str | None, default: float) -> float:
    """Parse a numeric CSV cell, accepting '.' or ',' as decimal separator.

    Args:
        value: Raw cell content, possibly None or empty.
        default: Value returned when the input is non-numeric.

    Returns:
        The parsed float, or the default value when the value is missing or malformed.
    """
    if value is None:
        return default
    cleaned = value.strip()
    if not cleaned:
        return default
    try:
        # Replace the first comma with a dot to handle European decimal format
        return float(cleaned.replace(",", ".", 1))
    except ValueError:
        return default


# EOF
