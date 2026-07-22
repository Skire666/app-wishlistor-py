# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations


class UnsupportedOperatingSystemError(Exception):
    """Raised when an OS interaction is requested on an unsupported platform."""

    def __init__(self, os_name: str) -> None:
        """Initialize the error with the detected platform name.

        Args:
            os_name: The detected operating system label.
        """
        super().__init__(f"Système d'exploitation non pris en charge : {os_name}")
        self.os_name = os_name


# EOF
