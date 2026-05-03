"""Python wrapper around OpenADMIXTURE.jl."""

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
    "run_openadmixture",
]
