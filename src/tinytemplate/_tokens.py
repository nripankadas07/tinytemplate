"""Token types produced by the lexer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class LiteralToken:
    """A literal text segment between expressions."""

    text: str
    position: int


@dataclass(frozen=True)
class ExpressionToken:
    """A parsed ${...} expression.

    - path is a tuple of segment strings (already split on '.')
    - default is the literal default text following ':-' (or None)
    - filters is the ordered tuple of filter names (may be empty)
    """

    path: Tuple[str, ...]
    default: str | None = None
    filters: Tuple[str, ...] = field(default_factory=tuple)
    position: int = 0


Token = LiteralToken | ExpressionToken


__all__ = ["LiteralToken", "ExpressionToken", "Token"]
