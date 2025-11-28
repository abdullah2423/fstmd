"""
Pytest configuration and fixtures for FSTMD tests.
"""

from __future__ import annotations

import pytest
from fstmd import Markdown


@pytest.fixture
def md_safe() -> Markdown:
    """Provide a safe-mode Markdown instance."""
    return Markdown(mode="safe")


@pytest.fixture
def md_raw() -> Markdown:
    """Provide a raw-mode Markdown instance."""
    return Markdown(mode="raw")


@pytest.fixture
def md_strict() -> Markdown:
    """Provide a strict-mode Markdown instance."""
    return Markdown(mode="safe", strict=True)
