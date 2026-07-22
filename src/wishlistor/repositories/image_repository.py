"""Raw image file access for CSV cells referencing images by relative path."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from pathlib import Path

from wishlistor.shared.constants_util import C_IMAGE_FILE_CACHE_MAX_BYTES


class ImageRepository:
    """Reads image files from disk, cached and invalidated on mtime change."""

    def __init__(self) -> None:
        """Initialize the repository."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._entries: dict[str, tuple[float, bytes | None]] = {}
        self._bytes: int = 0

    def read_image_bytes(self, absolute_path: str) -> bytes | None:
        """Return the raw bytes of the image at *absolute_path*.

        Args:
            absolute_path: Absolute filesystem path to the image.

        Returns:
            The file bytes, or None when the file is missing or unreadable.
        """
        try:
            mtime = Path(absolute_path).stat().st_mtime
        except OSError:
            self._logger.debug("Image introuvable : %s", absolute_path)
            self._drop(absolute_path)
            return None
        cached = self._entries.get(absolute_path)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        self._drop(absolute_path)
        try:
            data = Path(absolute_path).read_bytes()
        except OSError as excp:
            self._logger.debug("Lecture d'image impossible : %s (%s)", absolute_path, excp)
            data = None
        self._entries[absolute_path] = (mtime, data)
        if data is not None:
            self._bytes += len(data)
            self._evict()
        return data

    def invalidate_cache(self) -> None:
        """Drop every cached image entry."""
        self._logger.debug("Invalidation du cache d'images")
        self._entries.clear()
        self._bytes = 0

    def _drop(self, absolute_path: str) -> None:
        """Remove one cached entry and reclaim its byte budget."""
        previous = self._entries.pop(absolute_path, None)
        if previous is not None and previous[1] is not None:
            self._bytes -= len(previous[1])

    def _evict(self) -> None:
        """Drop the oldest entries until the byte budget is respected."""
        while self._bytes > C_IMAGE_FILE_CACHE_MAX_BYTES and self._entries:
            self._drop(next(iter(self._entries)))


# EOF
