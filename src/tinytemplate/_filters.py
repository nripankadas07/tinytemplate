"""Built-in filters and the default filter registry."""

from __future__ import annotations

from typing import Any, Callable, Dict

from ._errors import FilterError


Filter = Callable[[Any], Any]


def _filter_upper(value: Any) -> str:
    return str(value).upper()


def _filter_lower(value: Any) -> str:
    return str(value).lower()


def _filter_title(value: Any) -> str:
    return str(value).title()


def _filter_strip(value: Any) -> str:
    return str(value).strip()


def _filter_len(value: Any) -> int:
    """Length of value; works on collections or strings."""
    try:
        return len(value)
    except TypeError as exc:
        raise FilterError(
            f"len: object of type {type(value).__name__} has no len()"
        ) from exc


def _filter_reverse(value: Any) -> Any:
    """Reverse a string, list, or tuple. Raises FilterError otherwise."""
    if isinstance(value, str):
        return value[::-1]
    if isinstance(value, (list, tuple)):
        return type(value)(reversed(value))
    raise FilterError(
        f"reverse: cannot reverse object of type {type(value).__name__}"
    )


_BUILTIN_FILTERS: Dict[str, Filter] = {
    "upper": _filter_upper,
    "lower": _filter_lower,
    "title": _filter_title,
    "strip": _filter_strip,
    "trim": _filter_strip,
    "len": _filter_len,
    "reverse": _filter_reverse,
}


_DEFAULT_REGISTRY: Dict[str, Filter] = dict(_BUILTIN_FILTERS)


def builtin_filters() -> Dict[str, Filter]:
    """Return a fresh copy of the built-in filter table."""
    return dict(_BUILTIN_FILTERS)


def register_filter(name: str, func: Filter) -> None:
    """Register a filter in the default (module-level) registry."""
    if not isinstance(name, str) or not name:
        raise FilterError("filter name must be a non-empty string")
    if not callable(func):
        raise FilterError("filter func must be callable")
    _DEFAULT_REGISTRY[name] = func


def reset_default_filters() -> None:
    """Reset the default registry to only the built-ins (test-only helper)."""
    _DEFAULT_REGISTRY.clear()
    _DEFAULT_REGISTRY.update(_BUILTIN_FILTERS)


def default_registry() -> Dict[str, Filter]:
    """Return the live module-level registry (NOT a copy)."""
    return _DEFAULT_REGISTRY


def apply_chain(value: Any, names: tuple[str, ...], registry: Dict[str, Filter]) -> Any:
    """Apply a chain of filters by name; raises FilterError on unknown filter."""
    current = value
    for name in names:
        if name not in registry:
            raise FilterError(f"Unknown filter: {name!r}")
        current = registry[name](current)
    return current


__all__ = [
    "Filter",
    "apply_chain",
    "builtin_filters",
    "default_registry",
    "register_filter",
    "reset_default_filters",
]
