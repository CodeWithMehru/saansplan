"""Stable application error taxonomy."""

from dataclasses import dataclass


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400


class ValidationAppError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("VALIDATION_ERROR", message, 422)
