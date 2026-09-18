"""Shared fixtures."""

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load custom_components/ in tests."""
    yield


def load_fixture(name: str):
    """Return a parsed JSON fixture."""
    return json.loads((FIXTURES / name).read_text())
