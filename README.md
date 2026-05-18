# tinytemplate

[![Tests](https://img.shields.io/badge/tests-121%20passing-brightgreen)](#running-tests)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](#running-tests)
[![Type](https://img.shields.io/badge/typed-mypy%20--strict-blue)](#running-tests)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Zero-dependency `${name}` template renderer with default fallbacks,
dotted-path access, and small filter chains. Pure Python, no parser
generator, single-file lexer.

```python
from tinytemplate import render

render("Hello, ${user.name}!", {"user": {"name": "Ada"}})
# -> "Hello, Ada!"

render("Port ${port:-8080}", {})
# -> "Port 8080"

render("${name|upper}", {"name": "alice"})
# -> "ALICE"
```

## Install

```bash
pip install tinytemplate
```

Requires Python 3.10+.

## Syntax

| Construct                | Meaning                                                            |
|--------------------------|--------------------------------------------------------------------|
| `${var}`                 | Substitute `var` from the context.                                 |
| `${a.b.c}`               | Dotted path through nested mappings, lists, or objects.            |
| `${items.0}`             | Numeric segments index lists/tuples.                               |
| `${var:-fallback}`       | POSIX-style default when `var` is missing or `None`.               |
| `${var\|upper}`           | Apply a filter to the resolved value.                              |
| `${var\|strip\|upper}`     | Filter chain (left-to-right).                                      |
| `${name:-anon\|upper}`    | Default value passed through filter chain.                         |
| `\$` or `$$`             | Literal `$`.                                                       |

## Public API

```python
render(template, context, *, default=None, strict=True, filters=None) -> str
Template(template, *, filters=None).render(context, *, default=None, strict=True) -> str
parse(template) -> list[Token]
find_variables(template) -> list[str]
register_filter(name, func) -> None
resolve(context, path) -> Any
```

### Strict mode

The default `strict=True` raises `MissingVariableError` when a path
cannot be resolved. With `strict=False`, missing values are replaced by
the per-call `default` (or `""` if not given). A template-level
fallback (`${var:-X}`) always wins over both modes.

```python
from tinytemplate import render, MissingVariableError

try:
    render("${missing}", {})
except MissingVariableError as exc:
    print(exc.path)            # 'missing'

render("${missing}", {}, strict=False)            # ""
render("${missing}", {}, strict=False, default="N/A")  # "N/A"
render("${missing:-anon}", {}, strict=True)        # "anon"
```

### Built-in filters

`upper`, `lower`, `title`, `strip` (alias `trim`), `len`, `reverse`.

### Custom filters

```python
from tinytemplate import register_filter, render

register_filter("shout", lambda v: f"{v}!!!")
render("${name|shout}", {"name": "ada"})
# -> "ada!!!"
```

Per-call `filters=` argument overrides the default registry without
mutating it:

```python
render("${n|sq}", {"n": 3}, filters={"sq": lambda v: int(v) ** 2})
# -> "9"
```

### Pre-compile a template

`Template` parses once and renders many times:

```python
from tinytemplate import Template

email = Template("Hi ${name}, your tier is ${tier:-free}.")
for user in users:
    print(email.render(user))
```

## Errors

```text
TemplateError
├── TemplateSyntaxError    # malformed template
├── MissingVariableError   # strict-mode resolution failure
└── FilterError            # unknown filter or filter-side failure
```

## Running tests

```bash
pip install -e .
pip install pytest pytest-cov mypy
pytest --cov=tinytemplate --cov-report=term-missing
mypy --strict src/tinytemplate
```

The full suite is 121 tests across 5 modules with **100% line / 100%
branch** coverage and a `mypy --strict` clean type check.

## Non-goals

- No conditionals (`{% if %}`) or loops (`{% for %}`). Use a real
  template engine if you need control flow.
- No HTML escaping. Caller's responsibility (`html.escape`).
- No filter arguments. Filter chains only — register a closure if you
  need parameterised behaviour.

## Licence

MIT.
