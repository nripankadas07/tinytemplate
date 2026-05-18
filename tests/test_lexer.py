"""Lexer tests — parse() returns the right token stream."""
import pytest

from tinytemplate import (
    ExpressionToken,
    LiteralToken,
    TemplateSyntaxError,
    parse,
)


class TestParseBasic:
    def test_parse_empty_string_returns_no_tokens(self):
        assert parse("") == []

    def test_parse_pure_literal_returns_one_literal_token(self):
        tokens = parse("hello")
        assert tokens == [LiteralToken("hello", 0)]

    def test_parse_single_expression_returns_one_expression_token(self):
        tokens = parse("${name}")
        assert tokens == [ExpressionToken(("name",), None, (), 0)]

    def test_parse_literal_then_expression_then_literal(self):
        tokens = parse("Hi ${name}!")
        assert tokens == [
            LiteralToken("Hi ", 0),
            ExpressionToken(("name",), None, (), 3),
            LiteralToken("!", 10),
        ]

    def test_parse_multiple_expressions_in_sequence(self):
        tokens = parse("${a}${b}")
        assert [t for t in tokens if isinstance(t, ExpressionToken)] == [
            ExpressionToken(("a",), None, (), 0),
            ExpressionToken(("b",), None, (), 4),
        ]


class TestParsePaths:
    def test_parse_dotted_path_splits_segments(self):
        (token,) = parse("${a.b.c}")
        assert isinstance(token, ExpressionToken)
        assert token.path == ("a", "b", "c")

    def test_parse_numeric_path_segment_kept_as_string(self):
        (token,) = parse("${items.0.name}")
        assert isinstance(token, ExpressionToken)
        assert token.path == ("items", "0", "name")

    def test_parse_underscore_identifier_allowed(self):
        (token,) = parse("${_private.name_2}")
        assert isinstance(token, ExpressionToken)
        assert token.path == ("_private", "name_2")

    def test_parse_inner_whitespace_trimmed(self):
        (token,) = parse("${  name  }")
        assert isinstance(token, ExpressionToken)
        assert token.path == ("name",)


class TestParseDefaults:
    def test_parse_default_string_captured_verbatim(self):
        (token,) = parse("${name:-Anonymous}")
        assert isinstance(token, ExpressionToken)
        assert token.path == ("name",)
        assert token.default == "Anonymous"

    def test_parse_default_can_be_empty(self):
        (token,) = parse("${name:-}")
        assert isinstance(token, ExpressionToken)
        assert token.default == ""

    def test_parse_default_preserves_whitespace_after_marker(self):
        (token,) = parse("${name:-  spaced  }")
        assert isinstance(token, ExpressionToken)
        assert token.default == "  spaced  "


class TestParseFilters:
    def test_parse_single_filter_appended(self):
        (token,) = parse("${name|upper}")
        assert isinstance(token, ExpressionToken)
        assert token.filters == ("upper",)

    def test_parse_filter_chain_preserves_order(self):
        (token,) = parse("${name|upper|reverse}")
        assert isinstance(token, ExpressionToken)
        assert token.filters == ("upper", "reverse")

    def test_parse_filter_after_default(self):
        (token,) = parse("${name:-anon|upper}")
        assert isinstance(token, ExpressionToken)
        assert token.default == "anon"
        assert token.filters == ("upper",)

    def test_parse_filter_with_inner_whitespace(self):
        (token,) = parse("${ name | upper | reverse }")
        assert isinstance(token, ExpressionToken)
        assert token.filters == ("upper", "reverse")


class TestParseEscapes:
    def test_parse_backslash_dollar_is_literal_dollar(self):
        tokens = parse(r"price: \$5")
        assert tokens == [LiteralToken("price: $5", 0)]

    def test_parse_double_dollar_is_literal_dollar(self):
        tokens = parse("price: $$5")
        assert tokens == [LiteralToken("price: $5", 0)]

    def test_parse_trailing_dollar_is_literal(self):
        tokens = parse("cost$")
        assert tokens == [LiteralToken("cost$", 0)]

    def test_parse_dollar_followed_by_letter_is_literal(self):
        tokens = parse("$name")
        assert tokens == [LiteralToken("$name", 0)]


class TestParseErrors:
    def test_parse_unclosed_expression_raises(self):
        with pytest.raises(TemplateSyntaxError) as excinfo:
            parse("${name")
        assert excinfo.value.position == 0

    def test_parse_empty_expression_raises(self):
        with pytest.raises(TemplateSyntaxError):
            parse("${}")

    def test_parse_whitespace_only_expression_raises(self):
        with pytest.raises(TemplateSyntaxError):
            parse("${   }")

    def test_parse_invalid_first_segment_raises(self):
        with pytest.raises(TemplateSyntaxError):
            parse("${1bad}")

    def test_parse_empty_path_segment_raises(self):
        with pytest.raises(TemplateSyntaxError):
            parse("${a..b}")

    def test_parse_empty_filter_raises(self):
        with pytest.raises(TemplateSyntaxError):
            parse("${name|}")

    def test_parse_invalid_filter_name_raises(self):
        with pytest.raises(TemplateSyntaxError):
            parse("${name|1bad}")

    def test_parse_template_must_be_str(self):
        with pytest.raises(TypeError):
            parse(123)  # type: ignore[arg-type]


class TestParseEdgeCases:
    def test_parse_empty_path_with_default_raises(self):
        # Body is ':-foo'; path before ':-' is empty string.
        with pytest.raises(TemplateSyntaxError):
            parse("${:-foo}")

    def test_parse_filter_name_with_invalid_body_char_raises(self):
        # 'f-bad' starts with 'f' (valid first char) but has '-' in body.
        with pytest.raises(TemplateSyntaxError):
            parse("${name|f-bad}")

    def test_parse_filter_name_with_underscore_body_char_allowed(self):
        (token,) = parse("${name|my_filter}")
        assert isinstance(token, ExpressionToken)
        assert token.filters == ("my_filter",)
