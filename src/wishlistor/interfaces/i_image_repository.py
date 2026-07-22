# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol


class IImageRepository(Protocol):
    """Raw image file access, cached and keyed by absolute path."""

    def read_image_bytes(self, absolute_path: str) -> bytes | None:
        """Return the raw bytes of the image at *absolute_path*.

        Args:
            absolute_path: Absolute filesystem path to the image.

        Returns:
            The file bytes, or None when the file is missing or unreadable.
        """
        ...

    def invalidate_cache(self) -> None:
        """Drop every cached image entry."""
        ...


# EOF
