"""
title: Compatibility tests for malariagen-data as a development dependency.
"""

from __future__ import annotations

import sys

from typing import Any

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info >= (3, 13),
    reason="malariagen-data is not available for Python 3.13+",
)


def _import_malariagen_data() -> Any:
    """
    title: Import malariagen-data only on supported Python versions.
    returns:
      type: Any
    """
    import malariagen_data  # noqa: PLC0415 - avoid importing on Python 3.13+

    return malariagen_data


def test_malariagen_data_dev_dependency_imports() -> None:
    """
    title: malariagen-data imports as a test-only development dependency.
    """
    malariagen_data = _import_malariagen_data()

    assert hasattr(malariagen_data, "Ag3")
