# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from enum import Enum


class ProcessResultEnum(Enum):
    """Enumerates the possible outcomes of a processing step.

    SUCCESS and WARNING are both treated as success for statistics purposes;
    ERROR and FATAL are both failures, but only FATAL stops the workflow.
    """

    E_UNSET = "UNSET"  # default value; should be overridden
    E_SKIPPED = "SKIPPED"  # step was not executed
    E_SUCCESS = "SUCCESS"  # step completed fully
    E_WARNING = "WARNING"  # completed with a non-critical anomaly
    E_ERROR = "ERROR"  # step failed; workflow continues
    E_FATAL = "FATAL"  # step failed; workflow stops immediately
    E_UNKNOWN = "UNKNOWN"


# EOF
