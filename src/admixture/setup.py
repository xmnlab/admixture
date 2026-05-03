"""
title: Explicit Julia/OpenADMIXTURE.jl setup helpers.
"""

from __future__ import annotations

from pathlib import Path

from .exceptions import (
    OPENADMIXTURE_NOT_INSTALLED_MESSAGE,
    OpenAdmixtureNotInstalledError,
)
from .julia_env import bootstrap_julia_project, check_openadmixture_installed


def setup(
    *,
    project_dir: str | Path,
    julia: str | Path = "julia",
) -> None:
    """
    title: Install OpenADMIXTURE.jl into an explicit Julia project.
    parameters:
      project_dir:
        type: str | Path
      julia:
        type: str | Path
    """
    bootstrap_julia_project(project_dir=project_dir, julia=julia)
    if not check_openadmixture_installed(julia=julia, project_dir=project_dir):
        raise OpenAdmixtureNotInstalledError(
            f"{OPENADMIXTURE_NOT_INSTALLED_MESSAGE}\n"
            "Julia project setup completed, but OpenADMIXTURE.jl could not be "
            "imported from the configured project."
        )
