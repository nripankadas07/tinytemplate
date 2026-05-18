"""Integration tests across the full pipeline."""
import pytest

from tinytemplate import (
    Template,
    builtin_filters,
    default_registry,
    find_variables,
    register_filter,
    render,
    reset_default_filters,
)


def test_email_template_round_trip():
    template = (
        "Subject: Welcome ${user.first|title}!\n"
        "\n"
        "Hi ${user.first|title} ${user.last|title},\n"
        "Your tier is ${tier:-free|upper}."
    )
    ctx = {
        "user": {"first": "ada", "last": "lovelace"},
        "tier": "premium",
    }
    out = render(template, ctx)
    assert out == (
        "Subject: Welcome Ada!\n"
        "\n"
        "Hi Ada Lovelace,\n"
        "Your tier is PREMIUM."
    )


def test_email_template_uses_default_when_tier_missing():
    template = "Tier: ${tier:-free|upper}"
    assert render(template, {}) == "Tier: FREE"


def test_compiled_template_handles_thousands_of_renders():
    compiled = Template("Hi ${name}")
    for i in range(1000):
        assert compiled.render({"name": f"user{i}"}) == f"Hi user{i}"


def test_builtin_filters_exposed_as_dict_copy():
    table = builtin_filters()
    table["new_filter"] = lambda v: v
    # mutating the returned copy must not leak into the registry
    assert "new_filter" not in default_registry()


def test_register_filter_appears_in_default_registry():
    register_filter("noop", lambda v: v)
    assert "noop" in default_registry()


def test_reset_default_filters_clears_user_added_filters():
    register_filter("noop", lambda v: v)
    assert "noop" in default_registry()
    reset_default_filters()
    assert "noop" not in default_registry()
    # built-ins survive the reset
    assert "upper" in default_registry()


def test_find_variables_consistent_with_parse_tokens():
    template = "${a.b}-${c.0}-${d:-X}-${e|upper}"
    found = find_variables(template)
    assert found == ["a.b", "c.0", "d", "e"]


def test_render_handles_unicode_in_values():
    out = render("${name|upper}", {"name": "ælfric"})
    assert out == "ÆLFRIC"


def test_render_handles_unicode_in_template():
    out = render("こんにちは ${name}!", {"name": "Ada"})
    assert out == "こんにちは Ada!"


def test_complex_nested_data_rendering():
    template = "${rows.0.cells.0|upper}.${rows.1.cells.1|lower}"
    ctx = {"rows": [{"cells": ["abc", "DEF"]}, {"cells": ["GHI", "JKL"]}]}
    assert render(template, ctx) == "ABC.jkl"


def test_pathological_braces_in_literal_text_pass_through():
    out = render("config { x: ${val} }", {"val": 42})
    assert out == "config { x: 42 }"


def test_dollar_at_end_of_string_is_literal():
    assert render("cost: $", {}) == "cost: $"


def test_multiline_template_works_end_to_end():
    template = (
        "line1: ${a}\n"
        "line2: ${b.c}\n"
        "line3: ${missing:-fallback}\n"
    )
    out = render(template, {"a": 1, "b": {"c": 2}})
    assert out == "line1: 1\nline2: 2\nline3: fallback\n"


def test_filter_chain_applied_to_default_value():
    register_filter("exclaim", lambda v: f"{v}!")
    out = render("${x:-anon|upper|exclaim}", {})
    assert out == "ANON!"


def test_pipe_inside_default_is_treated_as_filter_separator():
    # By design: filter chain separators are parsed before default fallback,
    # so "${x:-a|upper}" splits as default='a' followed by upper filter.
    assert render("${x:-ada|upper}", {}) == "ADA"
