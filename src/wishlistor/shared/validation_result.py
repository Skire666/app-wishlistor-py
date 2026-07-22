# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from wishlistor.shared.enums.process_result_enum import ProcessResultEnum
from wishlistor.shared.enums.severity_enum import SeverityEnum
from wishlistor.shared.errors.base_error_code import BaseErrorCode


@dataclass
class ValidationIssue:
    """Represents a validation issue with its code, severity, and context."""

    code: BaseErrorCode
    severity: SeverityEnum
    context: dict[str, Any] = field(default_factory=dict[str, Any])

    @property
    def message(self) -> str:
        """Formatted message for the validation issue."""
        try:
            return str(self.code.value).format(**self.context)
        except KeyError, IndexError:
            return str(self.code.value)  # fallback when the context is incomplete


@dataclass
class ValidationResult:
    """Accumulates validation issues with severity-keyed counters for efficient querying."""

    issues: list[ValidationIssue] = field(default_factory=list[ValidationIssue])
    count_warnings: int = 0
    count_errors: int = 0
    count_fatals: int = 0

    def append(self, code: BaseErrorCode, severity: SeverityEnum, context: dict[str, Any] | None = None) -> None:
        """Append a new ValidationIssue and increment the matching severity counter."""
        self.issues.append(ValidationIssue(code=code, severity=severity, context=context or {}))
        if severity == SeverityEnum.E_WARNING:
            self.count_warnings += 1
        elif severity == SeverityEnum.E_ERROR:
            self.count_errors += 1
        elif severity == SeverityEnum.E_FATAL:
            self.count_fatals += 1

    def extend(self, other: ValidationResult) -> None:
        """Merge another ValidationResult into this one."""
        self.issues.extend(other.issues)
        self.count_warnings += other.count_warnings
        self.count_errors += other.count_errors
        self.count_fatals += other.count_fatals

    def get_worst_result_enum(self) -> ProcessResultEnum:
        """Return the worst ProcessResultEnum based on the accumulated issues."""
        if self.count_fatals > 0:
            return ProcessResultEnum.E_FATAL
        if self.count_errors > 0:
            return ProcessResultEnum.E_ERROR
        if self.count_warnings > 0:
            return ProcessResultEnum.E_WARNING
        return ProcessResultEnum.E_SUCCESS

    def has_issues(self) -> bool:
        """Return True if there are any validation issues, False otherwise."""
        return bool(self.issues)

    def has_errors_or_fatals(self) -> bool:
        """Return True if there are any validation errors or fatals, False otherwise."""
        return self.count_errors > 0 or self.count_fatals > 0

    def has_errors(self) -> bool:
        """Return True if there are any validation errors, False otherwise."""
        return self.count_errors > 0

    def has_fatals(self) -> bool:
        """Return True if there are any validation fatals, False otherwise."""
        return self.count_fatals > 0

    def has_warnings(self) -> bool:
        """Return True if there are any validation warnings, False otherwise."""
        return self.count_warnings > 0

    def count_severities(self, severity: SeverityEnum) -> int:
        """Return the number of issues recorded for the given severity level."""
        if severity == SeverityEnum.E_WARNING:
            return self.count_warnings
        if severity == SeverityEnum.E_ERROR:
            return self.count_errors
        if severity == SeverityEnum.E_FATAL:
            return self.count_fatals
        return 0

    def count_severities_by_code(self, code: BaseErrorCode) -> int:
        """Count the number of issues with a specific error code."""
        return sum(1 for issue in self.issues if issue.code is code)

    def count_issues(self) -> int:
        """Return the total number of validation issues."""
        return len(self.issues)

    def _collect_issues(
        self, severity: SeverityEnum, nbr_max: int, concat: str, nbr_pushed: int
    ) -> tuple[str, int]:
        """Append formatted issues of one severity to concat, stopping at nbr_max total."""
        for issue in self.issues:
            if nbr_pushed >= nbr_max:
                break
            if issue.severity == severity:
                concat += f"{severity.value} : {issue.code} - {issue.message}\n"
                nbr_pushed += 1
        return concat, nbr_pushed

    def concat_issues_by_severity(self, nbr_max: int = 2) -> str:
        """Compute a displayable string of validation issues, worst severity first."""
        if not self.issues:
            return "--"
        concat = ""
        nbr_pushed = 0
        if self.count_fatals > 0:
            concat, nbr_pushed = self._collect_issues(SeverityEnum.E_FATAL, nbr_max, concat, nbr_pushed)
        if self.count_errors > 0 and nbr_pushed < nbr_max:
            concat, nbr_pushed = self._collect_issues(SeverityEnum.E_ERROR, nbr_max, concat, nbr_pushed)
        if self.count_warnings > 0 and nbr_pushed < nbr_max:
            concat, nbr_pushed = self._collect_issues(SeverityEnum.E_WARNING, nbr_max, concat, nbr_pushed)
        return concat.strip()

    def concat_issues_by_order(self, nbr_max: int = 5) -> str:
        """Compute a displayable string of validation issues, in insertion order."""
        if not self.issues:
            return "--"
        concat = ""
        for nbr_pushed, issue in enumerate(self.issues):
            concat += f"{issue.severity.value} : {issue.code} - {issue.message}\n"
            if nbr_pushed + 1 >= nbr_max:
                break
        return concat.strip()

    def clear(self) -> None:
        """Clear all validation issues and reset counts."""
        self.issues.clear()
        self.count_warnings = 0
        self.count_errors = 0
        self.count_fatals = 0


# EOF
