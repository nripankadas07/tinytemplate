"""Render tests — full end-to-end rendering."""
import pytest

from tinytemplate import (
    FilterError,
    MissingVariableError,
    Template,
    TemplateSyntaxError,
    find_variables,
    register_filter,
    render,
)


class TestRenderBasic:
    def test_render_empty_template_returns_empty_string(self):
        assert render("", {}) == ""

    def test_render_pure_literal_unchanged(self):
        assert render("hello world", {}) == "hello world"

    def test_render_single_variable_substituted(self):
        assert render("Hi ${name}!", {"name": "Ada"}) == "Hi Ada!"

    def test_render_multiple_variables(self):
        out = render("${a}-${b}-${c}", {"a": 1, "b": 2, "c": 3})
        assert out == "1-2-3"

    def test_render_dotted_path(self):
        ctx = {"user": {"name": "Ada"}}
        assert render("Hello ${user.name}", ctx) == "Hello Ada"

    def test_render_list_index(self):
        ctx = {"items": ["a", "b", "c"]}
        assert render("${items.1}", ctx) == "b"

    def test_render_integer_value_stringified(self):
        assert render("Port ${port}", {"port": 8080}) == "Port 8080"

    def test_render_float_value_stringified(self):
        assert render("Pi=${pi}", {"pi": 3.14}) == "Pi=3.14"

    def test_render_bool_true_renders_as_lowercase(self):
        assert render("${flag}", {"flag": True}) == "true"

    def test_render_bool_false_renders_as_lowercase(self):
        assert render("${flag}", {"flag": False}) == "false"

    def test_render_escape_dollar_with_backslash(self):
        assert render(r"price=\$${amount}", {"amount": 5}) == "price=$5"

    def test_render_escape_dollar_with_double_dollar(self):
        assert render("price=$$${amount}", {"amount": 5}) == "price=$5"


class TestRenderDefaults:
    def test_render_default_used_when_var_missing(self):
        assert render("Hello ${name:-stranger}", {}) == "Hello stranger"

    def test_render_default_ignored_when_var_present(self):
        assert render("Hello ${name:-stranger}", {"name": "Ada"}) == "Hello Ada"

    def test_render_default_used_when_var_is_none(self):
        assert render("Hello ${name:-anon}", {"name": None}) == "Hello anon"

    def test_render_default_can_be_empty_string(self):
        assert render("[${tag:-}]", {}) == "[]"

    def test_render_default_takes_precedence_over_strict(self):
        # default in the template trumps strict=True
        assert render("${x:-fallback}", {}, strict=True) == "fallback"


class TestRenderStrictMode:
    def test_render_strict_missing_variable_raises(self):
        with pytest.raises(MissingVariableError) as excinfo:
            render("${missing}", {}, strict=True)
        assert excinfo.value.path == "missing"

    def test_render_strict_missing_nested_path_raises(self):
        with pytest.raises(MissingVariableError) as excinfo:
            render("${user.email}", {"user": {}}, strict=True)
        assert excinfo.value.path == "user.email"

    def test_render_non_strict_missing_returns_empty(self):
        assert render("[${missing}]", {}, strict=False) == "[]"

    def test_render_non_strict_missing_uses_default_param(self):
        out = render("[${missing}]", {}, strict=False, default="N/A")
        assert out == "[N/A]"

    def test_render_non_strict_present_value_unaffected(self):
        out = render("[${name}]", {"name": "Ada"}, strict=False, default="N/A")
        assert out == "[Ada]"


class TestRenderFilters:
    def test_render_filter_upper(self):
        assert render("${name|upper}", {"name": "ada"}) == "ADA"

    def test_render_filter_lower(self):
        assert render("${name|lower}", {"name": "ADA"}) == "ada"

    def test_render_filter_title(self):
        assert render("${name|title}", {"name": "ada lovelace"}) == "Ada Lovelace"

    def test_render_filter_strip(self):
        assert render("[${value|strip}]", {"value": "  ada  "}) == "[ada]"

    def test_render_filter_trim_alias_for_strip(self):
        assert render("[${value|trim}]", {"value": "  ada  "}) == "[ada]"

    def test_render_filter_len_on_string(self):
        assert render("${name|len}", {"name": "ada"}) == "3"

    def test_render_filter_len_on_list(self):
        assert render("${items|len}", {"items": [1, 2, 3, 4]}) == "4"

    def test_render_filter_reverse_on_string(self):
        assert render("${name|reverse}", {"name": "ada"}) == "ada"

    def test_render_filter_reverse_on_list_returns_list_repr(self):
        assert render("${items|reverse}", {"items": [1, 2, 3]}) == "[3, 2, 1]"

    def test_render_filter_chain_left_to_right(self):
        ctx = {"name": "  Ada  "}
        assert render("${name|strip|upper}", ctx) == "ADA"

    def test_render_filter_applied_to_default_value(self):
        assert render("${name:-anon|upper}", {}) == "ANON"

    def test_render_filter_unknown_raises(self):
        with pytest.raises(FilterError):
            render("${name|nope}", {"name": "x"})

    def test_render_filter_len_on_int_raises(self):
        with pytest.raises(FilterError):
            render("${n|len}", {"n": 42})

    def test_render_filter_reverse_on_int_raises(self):
        with pytest.raises(FilterError):
            render("${n|reverse}", {"n": 42})


class TestRenderCustomFilters:
    def test_render_register_filter_then_use_it(self):
        register_filter("shout", lambda value: f"{value}!!!")
        assert render("${name|shout}", {"name": "ada"}) == "ada!!!"

    def test_render_per_call_filters_override_default(self):
        out = render(
            "${name|squared}",
            {"name": 3},
            filters={"squared": lambda v: int(v) ** 2},
        )
        assert out == "9"

    def test_render_per_call_filters_isolated_from_default_registry(self):
        render("${n|sq}", {"n": 4}, filters={"sq": lambda v: int(v) ** 2})
        # default registry must not have learned 'sq'
        with pytest.raises(FilterError):
            render("${n|sq}", {"n": 4})

    def test_register_filter_rejects_empty_name(self):
        with pytest.raises(FilterError):
            register_filter("", lambda v: v)

    def test_register_filter_rejects_non_callable(self):
        with pytest.raises(FilterError):
            register_filter("x", "not-callable")  # type: ignore[arg-type]


class TestTemplateClass:
    def test_template_render_reuses_parsed_tokens(self):
        compiled = Template("Hi ${name}")
        assert compiled.render({"name": "Ada"}) == "Hi Ada"
        assert compiled.render({"name": "Bea"}) == "Hi Bea"

    def test_template_tokens_property_returns_tuple(self):
        compiled = Template("hi ${a}")
        assert isinstance(compiled.tokens, tuple)
        assert len(compiled.tokens) == 2

    def test_template_source_property(self):
        compiled = Template("hello")
        assert compiled.source == "hello"

    def test_template_rejects_non_str(self):
        with pytest.raises(TypeError):
            Template(b"bytes")  # type: ignore[arg-type]

    def test_template_render_rejects_non_mapping_context(self):
        compiled = Template("${name}")
        with pytest.raises(TypeError):
            compiled.render(["not", "a", "mapping"])  # type: ignore[arg-type]

    def test_template_uses_supplied_filter_table(self):
        compiled = Template(
            "${n|sq}", filters={"sq": lambda v: int(v) ** 2}
        )
        assert compiled.render({"n": 5}) == "25"

    def test_template_syntax_error_propagates_from_init(self):
        with pytest.raises(TemplateSyntaxError):
            Template("${")


class TestFindVariables:
    def test_find_variables_empty_template(self):
        assert find_variables("") == []

    def test_find_variables_returns_dotted_paths_in_order(self):
        out = find_variables("${a}-${user.name}-${items.0}")
        assert out == ["a", "user.name", "items.0"]

    def test_find_variables_does_not_dedupe(self):
        out = find_variables("${a}-${a}-${a}")
        assert out == ["a", "a", "a"]

    def test_find_variables_ignores_literals(self):
        assert find_variables("hello world") == []

    def test_find_variables_rejects_non_str(self):
        with pytest.raises(TypeError):
            find_variables(42)  # type: ignore[arg-type]


class TestRenderRejectsBadInputs:
    def test_render_rejects_non_str_template(self):
        with pytest.raises(TypeError):
            render(42, {})  # type: ignore[arg-type]

    def test_render_rejects_non_mapping_context(self):
        with pytest.raises(TypeError):
            render("hi", "not a mapping")  # type: ignore[arg-type]
