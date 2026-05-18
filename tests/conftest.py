"""Pytest configuration: keep the default filter registry pristine per-test."""
import os
import sys

import pytest


# Ensure the in-tree src/ layout is importable without an editable install.
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, os.pardir, "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


@pytest.fixture(autouse=True)
def _reset_default_filters():
    from tinytemplate import reset_default_filters
    reset_default_filters()
    yield
    reset_default_filters()
