"""Error classes for tinytemplate."""

from __future__ import annotations


class TemplateError(Exception):
    """Base class for all tinytemplate errors."""


class TemplateSyntaxError(TemplateError):
    """Raised when a template cannot be parsed."""

    def __init__(self, message: str, position: int) -> None:
        super().__init__(f"{message} (at position {position})")
        self.position = position
        self.message = message


class MissingVariableError(TemplateError):
    """Raised in strict mode when a variable cannot be resolved."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Missing variable: {path!r}")
        self.path = path


class FilterError(TemplateError):
    """Raised when a filter is unknown or fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


__all__ = [
    "TemplateError",
    "TemplateSyntaxError",
    "MissingVariableError",
    "FilterError",
]
