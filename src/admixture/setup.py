"""
title: Explicit Julia/OpenADMIXTURE.jl setup helpers.
"""

from __future__ import annotations

import subprocess

from importlib.resources import files
from pathlib import Path

from .exceptions import (
    OPENADMIXTURE_NOT_INSTALLED_MESSAGE,
    OpenAdmixtureNotInstalledError,
)
from .julia_env import check_openadmixture_installed, find_julia


def default_julia_project_dir() -> Path:
    """
    title: Return the packaged Julia project directory.
    returns:
      type: Path
    """
    return Path(str(files("admixture").joinpath("julia-env")))


def instantiate_julia_project(
    *,
    julia: str | Path = "julia",
) -> Path:
    """
    title: Instantiate the packaged Julia project.
    parameters:
      julia:
        type: str | Path
    returns:
      type: Path
    """
    executable = find_julia(julia)
    project_dir = default_julia_project_dir()
    completed = subprocess.run(
        [
            str(executable),
            f"--project={project_dir}",
            "-e",
            "using Pkg; Pkg.instantiate(); Pkg.precompile()",
        ],
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise OpenAdmixtureNotInstalledError(
            f"{OPENADMIXTURE_NOT_INSTALLED_MESSAGE}\n"
            "Packaged Julia project instantiation failed.\n\n"
            f"Project directory: {project_dir}\n"
            f"Exit status: {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return project_dir


def setup(
    *,
    julia: str | Path = "julia",
) -> Path:
    """
    title: >-
      Install OpenADMIXTURE.jl dependencies for the packaged Julia project.
    parameters:
      julia:
        type: str | Path
    returns:
      type: Path
    """
    project_dir = instantiate_julia_project(julia=julia)
    if not check_openadmixture_installed(
        julia=julia,
        project_dir=project_dir,
    ):
        raise OpenAdmixtureNotInstalledError(
            f"{OPENADMIXTURE_NOT_INSTALLED_MESSAGE}\n"
            "Julia project setup completed, but OpenADMIXTURE.jl could not be "
            "imported from the packaged project."
        )
    return project_dir
