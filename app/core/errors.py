"""Stable application error taxonomy."""

from dataclasses import dataclass


@dataclass
class AppError(Exception):
    """Base application domain exception with machine-readable code."""

    code: str
    message: str
    status_code: int = 400


class ValidationAppError(AppError):
    """Exception raised when user input fails business validation checks."""

    def __init__(self, message: str) -> None:
        """Initialize validation error with standard code and HTTP 422 status."""
        super().__init__("VALIDATION_ERROR", message, 422)
