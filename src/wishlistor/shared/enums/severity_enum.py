# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class SeverityEnum(Enum):
    """Enumerates the severity levels for error messages.

    These levels are used to categorize and prioritize error handling.
    """

    E_UNSET = "UNSET"
    E_INFO = "INFO"  # Informational message; no action required
    E_WARNING = "WARNING"  # Non-critical issue; workflow can continue
    E_ERROR = "ERROR"  # Critical issue; workflow may be affected
    E_FATAL = "FATAL"  # Severe issue; workflow must stop immediately
    E_UNKNOWN = "UNKNOWN"  # Unknown severity level


# EOF
