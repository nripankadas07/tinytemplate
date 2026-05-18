"""Resolve dotted-path lookups against a context."""

from __future__ import annotations

from typing import Any, Mapping, Tuple

# Sentinel to indicate a missing path. Public-only via _MISSING below.
_MISSING: Any = object()


def resolve(context: Mapping[str, Any], path: Tuple[str, ...]) -> Any:
    """Resolve a dotted path against a context.

    Returns the resolved value, or raises KeyError if the path cannot
    be walked.
    """
    result = walk(context, path)
    if result is _MISSING:
        raise KeyError(".".join(path))
    return result


def walk(context: Mapping[str, Any], path: Tuple[str, ...]) -> Any:
    """Walk path; return _MISSING on any failure (no raise).

    Numeric segments index lists/tuples (positive only). Mappings are
    keyed by segment name; otherwise getattr is used for objects.
    """
    current: Any = context
    for segment in path:
        nxt = _step(current, segment)
        if nxt is _MISSING:
            return _MISSING
        current = nxt
    return current


def _step(current: Any, segment: str) -> Any:
    """Take one step into the value for the given segment."""
    if isinstance(current, Mapping):
        if segment in current:
            return current[segment]
        return _MISSING
    if segment.isdigit() and isinstance(current, (list, tuple)):
        index = int(segment)
        if 0 <= index < len(current):
            return current[index]
        return _MISSING
    if isinstance(current, (str, bytes)):
        return _MISSING
    if hasattr(current, segment):
        return getattr(current, segment)
    return _MISSING


__all__ = ["resolve", "walk"]
