"""
title: Python wrapper around OpenADMIXTURE.jl.
"""

from __future__ import annotations

from ._version import __version__
from .exceptions import (
    JuliaNotFoundError,
    OpenAdmixtureError,
    OpenAdmixtureNotInstalledError,
    OpenAdmixtureRunError,
    OutputParseError,
    PlinkInputError,
)
from .result import OpenAdmixtureResult
from .runner import OpenAdmixtureRunner, run_openadmixture
from .setup import default_julia_project_dir, setup

__all__ = [
    "JuliaNotFoundError",
    "OpenAdmixtureError",
    "OpenAdmixtureNotInstalledError",
    "OpenAdmixtureResult",
    "OpenAdmixtureRunError",
    "OpenAdmixtureRunner",
    "OutputParseError",
    "PlinkInputError",
    "__version__",
    "default_julia_project_dir",
    "run_openadmixture",
    "setup",
]
