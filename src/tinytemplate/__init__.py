"""tinytemplate — zero-dep ${name} template renderer.

Public API:

    >>> from tinytemplate import render
    >>> render("Hello, ${user.name}!", {"user": {"name": "Ada"}})
    'Hello, Ada!'

    >>> render("Port ${port:-8080}", {})
    'Port 8080'

    >>> render("${name|upper}", {"name": "alice"})
    'ALICE'
"""

from __future__ import annotations

from ._errors import (
    FilterError,
    MissingVariableError,
    TemplateError,
    TemplateSyntaxError,
)
from ._filters import (
    builtin_filters,
    default_registry,
    register_filter,
    reset_default_filters,
)
from ._lexer import parse
from ._render import Template, find_variables, render
from ._resolver import resolve
from ._tokens import ExpressionToken, LiteralToken, Token


__version__ = "0.1.0"

__all__ = [
    "ExpressionToken",
    "FilterError",
    "LiteralToken",
    "MissingVariableError",
    "Template",
    "TemplateError",
    "TemplateSyntaxError",
    "Token",
    "__version__",
    "builtin_filters",
    "default_registry",
    "find_variables",
    "parse",
    "register_filter",
    "render",
    "reset_default_filters",
    "resolve",
]
