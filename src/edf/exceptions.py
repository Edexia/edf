"""Custom exceptions for EDF operations."""


class EDFError(Exception):
    """Base exception for all EDF-related errors."""

    pass


class EDFValidationError(EDFError):
    """Raised when EDF content fails validation checks."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class EDFStructureError(EDFError):
    """Raised when required files are missing or the archive structure is invalid."""

    pass


class EDFConsistencyError(EDFError):
    """Raised when cross-file consistency checks fail."""

    pass
