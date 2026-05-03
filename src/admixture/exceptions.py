"""
title: Custom exceptions raised by the :mod:`admixture` package.
"""

from __future__ import annotations


class OpenAdmixtureError(Exception):
    """
    title: Base exception for the admixture package.
    """


class JuliaNotFoundError(OpenAdmixtureError):
    """
    title: Raised when the Julia executable cannot be found.
    """


class OpenAdmixtureNotInstalledError(OpenAdmixtureError):
    """
    title: Raised when OpenADMIXTURE.jl is unavailable.
    """


class PlinkInputError(OpenAdmixtureError):
    """
    title: Raised when PLINK input files are missing or invalid.
    """


class OpenAdmixtureRunError(OpenAdmixtureError):
    """
    title: Raised when the Julia backend exits with a nonzero status.
    """


class OutputParseError(OpenAdmixtureError):
    """
    title: Raised when output files cannot be found or parsed.
    """


JULIA_NOT_FOUND_MESSAGE = """Julia executable was not found.

Install Julia from https://julialang.org/downloads/ or pass the executable path:

    OpenAdmixtureRunner(julia="/path/to/julia")

On Windows this may look like:

    OpenAdmixtureRunner(julia=r"C:\\Users\\you\\...\\julia.exe")
"""

OPENADMIXTURE_NOT_INSTALLED_MESSAGE = (
    "OpenADMIXTURE.jl does not appear to be installed in the selected Julia\n"
    "environment.\n\n"
    "Install it with Julia's package manager:\n\n"
    "    julia -e 'using Pkg; "
    'Pkg.add(url="https://github.com/kose-y/SparseKmeansFeatureRanking.jl"); '
    'Pkg.add(url="https://github.com/OpenMendel/OpenADMIXTURE.jl")\'\n\n'
    "or create a project-local Julia environment and pass project_dir=... to\n"
    "OpenAdmixtureRunner.\n"
)
