"""Render templates into strings."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from ._errors import MissingVariableError
from ._filters import Filter, apply_chain, default_registry
from ._lexer import parse
from ._resolver import _MISSING, walk
from ._tokens import ExpressionToken, LiteralToken, Token


class Template:
    """A pre-parsed template that can be rendered repeatedly."""

    __slots__ = ("_source", "_tokens", "_filters")

    def __init__(
        self, template: str, *, filters: Mapping[str, Filter] | None = None
    ) -> None:
        if not isinstance(template, str):
            raise TypeError("template must be a str")
        self._source = template
        self._tokens: List[Token] = parse(template)
        self._filters: Dict[str, Filter] = (
            dict(filters) if filters is not None else dict(default_registry())
        )

    @property
    def source(self) -> str:
        return self._source

    @property
    def tokens(self) -> tuple[Token, ...]:
        return tuple(self._tokens)

    def render(
        self,
        context: Mapping[str, Any],
        *,
        default: str | None = None,
        strict: bool = True,
    ) -> str:
        if not isinstance(context, Mapping):
            raise TypeError("context must be a Mapping")
        parts: List[str] = []
        for token in self._tokens:
            if isinstance(token, LiteralToken):
                parts.append(token.text)
            else:
                parts.append(self._render_expression(token, context, default, strict))
        return "".join(parts)

    def _render_expression(
        self,
        token: ExpressionToken,
        context: Mapping[str, Any],
        default: str | None,
        strict: bool,
    ) -> str:
        value = walk(context, token.path)
        if value is _MISSING or value is None:
            value = _fallback(token, default, strict)
        if token.filters:
            value = apply_chain(value, token.filters, self._filters)
        return _stringify(value)


def render(
    template: str,
    context: Mapping[str, Any],
    *,
    default: str | None = None,
    strict: bool = True,
    filters: Mapping[str, Filter] | None = None,
) -> str:
    """Render a template string against a context."""
    compiled = Template(template, filters=filters)
    return compiled.render(context, default=default, strict=strict)


def find_variables(template: str) -> List[str]:
    """Return the dotted-path of every expression in the template, in order."""
    if not isinstance(template, str):
        raise TypeError("template must be a str")
    out: List[str] = []
    for token in parse(template):
        if isinstance(token, ExpressionToken):
            out.append(".".join(token.path))
    return out


def _fallback(token: ExpressionToken, default: str | None, strict: bool) -> Any:
    """Return the appropriate fallback for a missing/None expression value."""
    if token.default is not None:
        return token.default
    if strict:
        raise MissingVariableError(".".join(token.path))
    return default if default is not None else ""


def _stringify(value: Any) -> str:
    """Convert a value to its rendered string form."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


__all__ = ["Template", "render", "find_variables"]
