"""Resolver tests — dotted-path traversal."""
import pytest

from tinytemplate import resolve


class _Box:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestResolveBasic:
    def test_resolve_single_key_returns_value(self):
        assert resolve({"name": "Ada"}, ("name",)) == "Ada"

    def test_resolve_nested_dict_walks_path(self):
        ctx = {"user": {"profile": {"email": "a@b.c"}}}
        assert resolve(ctx, ("user", "profile", "email")) == "a@b.c"

    def test_resolve_list_index_with_digit_segment(self):
        ctx = {"items": ["alpha", "beta", "gamma"]}
        assert resolve(ctx, ("items", "1")) == "beta"

    def test_resolve_tuple_index_works_like_list(self):
        ctx = {"point": (10, 20, 30)}
        assert resolve(ctx, ("point", "2")) == 30

    def test_resolve_list_inside_dict_inside_list(self):
        ctx = {"rows": [{"cells": ["a", "b"]}]}
        assert resolve(ctx, ("rows", "0", "cells", "1")) == "b"


class TestResolveAttributeAccess:
    def test_resolve_object_attribute(self):
        ctx = {"obj": _Box(name="Ada")}
        assert resolve(ctx, ("obj", "name")) == "Ada"

    def test_resolve_chained_attributes(self):
        inner = _Box(value=42)
        outer = _Box(inner=inner)
        ctx = {"outer": outer}
        assert resolve(ctx, ("outer", "inner", "value")) == 42


class TestResolveErrors:
    def test_resolve_missing_key_raises_keyerror(self):
        with pytest.raises(KeyError):
            resolve({}, ("missing",))

    def test_resolve_missing_nested_key_raises_keyerror(self):
        with pytest.raises(KeyError):
            resolve({"user": {}}, ("user", "name"))

    def test_resolve_index_out_of_range_raises_keyerror(self):
        with pytest.raises(KeyError):
            resolve({"items": [1, 2]}, ("items", "5"))

    def test_resolve_string_segment_on_list_raises_keyerror(self):
        with pytest.raises(KeyError):
            resolve({"items": [1, 2]}, ("items", "name"))

    def test_resolve_step_into_string_treats_as_atom(self):
        with pytest.raises(KeyError):
            resolve({"name": "Ada"}, ("name", "0"))


class TestResolveEdgeCases:
    def test_resolve_step_into_bytes_returns_keyerror(self):
        with pytest.raises(KeyError):
            resolve({"data": b"abc"}, ("data", "0"))

    def test_resolve_unknown_attribute_raises_keyerror(self):
        ctx = {"obj": _Box(name="Ada")}
        with pytest.raises(KeyError):
            resolve({"obj": ctx["obj"]}, ("obj", "missing"))

    def test_walk_returns_missing_sentinel_for_unknown_path(self):
        from tinytemplate._resolver import _MISSING, walk
        assert walk({"a": 1}, ("missing",)) is _MISSING
