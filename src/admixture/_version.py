"""Version helpers for :mod:`admixture`."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("admixture")
except PackageNotFoundError:  # pragma: no cover - only used from source trees.
    __version__ = "0.0.0"
