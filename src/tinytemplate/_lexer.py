"""Lexer for tinytemplate.

Grammar (informal):
    template := segment*
    segment  := literal | escape | expression
    escape   := '\\$' | '$$'        (-> literal '$')
    expression := '${' WS? path (':-' default)? ('|' filter)* WS? '}'
    path       := identifier ('.' segment)*  (segments may be digits)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ._errors import TemplateSyntaxError
from ._tokens import ExpressionToken, LiteralToken, Token


@dataclass
class _LexerState:
    """Mutable accumulator passed through the lexer steps."""

    tokens: List[Token] = field(default_factory=list)
    buf: List[str] = field(default_factory=list)
    buf_start: int = 0


def parse(template: str) -> List[Token]:
    """Parse a template string into a list of tokens.

    Raises TemplateSyntaxError on malformed input.
    """
    if not isinstance(template, str):
        raise TypeError("template must be a str")
    state = _LexerState()
    index = 0
    while index < len(template):
        index = _consume_segment(template, index, state)
    if state.buf:
        state.tokens.append(LiteralToken("".join(state.buf), state.buf_start))
    return state.tokens


def _consume_segment(template: str, index: int, state: _LexerState) -> int:
    """Process a single segment starting at `index`, return new index."""
    char = template[index]
    if _is_escaped_dollar(template, index):
        state.buf.append("$")
        return index + 2
    if _is_expression_start(template, index):
        _flush_literal(state)
        token, after = _parse_expression(template, index)
        state.tokens.append(token)
        state.buf_start = after
        return after
    state.buf.append(char)
    return index + 1


def _flush_literal(state: _LexerState) -> None:
    """Drain the current literal buffer into a token."""
    if state.buf:
        state.tokens.append(LiteralToken("".join(state.buf), state.buf_start))
        state.buf = []


def _is_escaped_dollar(template: str, index: int) -> bool:
    """Return True if template[index:index+2] is '\\$' or '$$'."""
    if index + 1 >= len(template):
        return False
    pair = template[index : index + 2]
    return pair == "\\$" or pair == "$$"


def _is_expression_start(template: str, index: int) -> bool:
    """Return True if template[index:index+2] starts an expression."""
    return (
        index + 1 < len(template)
        and template[index] == "$"
        and template[index + 1] == "{"
    )


def _parse_expression(template: str, start: int) -> tuple[ExpressionToken, int]:
    """Parse a ${...} expression starting at template[start] (which is '$').

    Returns (token, index_after_closing_brace).
    """
    end = template.find("}", start + 2)
    if end == -1:
        raise TemplateSyntaxError("Unclosed expression", start)
    body = template[start + 2 : end]
    if not body.strip():
        raise TemplateSyntaxError("Empty expression", start)
    return _build_expression_token(body, start), end + 1


def _build_expression_token(body: str, position: int) -> ExpressionToken:
    """Decompose the inside of ${...} into path/default/filters.

    Filters are separated by '|' anywhere in the body. The default
    fallback (after ':-') runs from the marker up to the first '|'
    (or end of body) and preserves embedded whitespace.
    """
    head, filter_chain = _split_filters(body, position)
    path_text, default = _split_default(head)
    path = _split_path(path_text.strip(), position)
    return ExpressionToken(
        path=path, default=default, filters=tuple(filter_chain), position=position
    )


def _split_filters(body: str, position: int) -> tuple[str, list[str]]:
    """Pull the trailing |filter chain off the body, if any."""
    pipe_idx = body.find("|")
    if pipe_idx == -1:
        return body, []
    head = body[:pipe_idx]
    raw_filters = body[pipe_idx + 1 :].split("|")
    filters = [_validate_filter_name(raw, position) for raw in raw_filters]
    return head, filters


def _validate_filter_name(raw: str, position: int) -> str:
    """Validate one |filter name; return the trimmed name."""
    name = raw.strip()
    if not name:
        raise TemplateSyntaxError("Empty filter name", position)
    if not _is_identifier(name):
        raise TemplateSyntaxError(f"Invalid filter name: {name!r}", position)
    return name


def _split_default(head: str) -> tuple[str, str | None]:
    """Split `head` on the FIRST ':-' separator.

    The default value is preserved verbatim (no whitespace stripping)
    so callers may use leading/trailing spaces in their fallbacks.
    """
    marker = ":-"
    idx = head.find(marker)
    if idx == -1:
        return head, None
    return head[:idx], head[idx + len(marker) :]


def _split_path(body: str, position: int) -> tuple[str, ...]:
    """Split a dotted path into segments and validate each one."""
    if not body:
        raise TemplateSyntaxError("Empty variable name", position)
    segments = body.split(".")
    for segment in segments:
        _validate_path_segment(segment, position)
    return tuple(segments)


def _validate_path_segment(segment: str, position: int) -> None:
    """Validate that segment is a Python-style identifier or all digits."""
    if not segment:
        raise TemplateSyntaxError("Empty path segment", position)
    if not _is_identifier(segment) and not segment.isdigit():
        raise TemplateSyntaxError(f"Invalid path segment: {segment!r}", position)


def _is_identifier(token: str) -> bool:
    """Return True if `token` is a Python-style identifier.

    Callers must pre-validate that `token` is non-empty.
    """
    if not (token[0].isalpha() or token[0] == "_"):
        return False
    return all(char.isalnum() or char == "_" for char in token[1:])


__all__ = ["parse"]
