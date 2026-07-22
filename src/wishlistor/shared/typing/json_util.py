"""Typed helpers to walk raw JSON payloads without unknown-type leaks."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast


def as_str_object_dict(value: object) -> dict[str, object] | None:
    """Return *value* as a ``dict[str, object]``, or None when not a dict.

    Args:
        value: Any JSON-decoded object.

    Returns:
        A dictionary with stringified keys, or None.
    """
    if not isinstance(value, dict):
        return None
    typed = cast("dict[object, object]", value)
    return {str(key): item for key, item in typed.items()}


def as_object_list(value: object) -> list[object] | None:
    """Return *value* as a ``list[object]``, or None when not a list.

    Args:
        value: Any JSON-decoded object.

    Returns:
        A shallow copy of the list, or None.
    """
    if not isinstance(value, list):
        return None
    return list(cast("list[object]", value))


def as_str_list(value: object) -> list[str]:
    """Return the string items of *value* (empty when not a list).

    Args:
        value: Any JSON-decoded object.

    Returns:
        The string items, in order.
    """
    items = as_object_list(value)
    if items is None:
        return []
    return [item for item in items if isinstance(item, str)]


# EOF
