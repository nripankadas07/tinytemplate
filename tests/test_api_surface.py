"""Public-surface invariants."""
import tinytemplate as tt


def test_api_surface_exports_expected_names():
    expected = {
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
    }
    assert expected.issubset(set(dir(tt)))


def test_api_surface_version_is_a_string():
    assert isinstance(tt.__version__, str)
    assert tt.__version__


def test_api_surface_error_hierarchy():
    assert issubclass(tt.TemplateSyntaxError, tt.TemplateError)
    assert issubclass(tt.MissingVariableError, tt.TemplateError)
    assert issubclass(tt.FilterError, tt.TemplateError)


def test_api_surface_template_class_is_constructible():
    template = tt.Template("hello")
    assert isinstance(template, tt.Template)
    assert template.source == "hello"


def test_api_surface_register_filter_returns_none():
    result = tt.register_filter("noop", lambda v: v)
    assert result is None
