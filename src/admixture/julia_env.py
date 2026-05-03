"""Utilities for locating Julia and managing OpenADMIXTURE.jl."""

from __future__ import annotations

import os
import shutil
import subprocess

from dataclasses import dataclass
from pathlib import Path

from .exceptions import (
    JULIA_NOT_FOUND_MESSAGE,
    OPENADMIXTURE_NOT_INSTALLED_MESSAGE,
    JuliaNotFoundError,
    OpenAdmixtureNotInstalledError,
)

OPENADMIXTURE_URL = "https://github.com/OpenMendel/OpenADMIXTURE.jl"
SPARSE_KMEANS_URL = "https://github.com/kose-y/SparseKmeansFeatureRanking.jl"
OPENADMIXTURE_UUID = "425c031d-9e5b-441b-a07e-4acde9a966a3"


@dataclass(frozen=True)
class JuliaInfo:
    """Basic information about the Julia runtime."""

    executable: Path
    version: str


def _looks_like_path(value: str) -> bool:
    return (
        Path(value).is_absolute()
        or os.sep in value
        or (os.altsep is not None and os.altsep in value)
        or "\\" in value
    )


def find_julia(julia: str | Path = "julia") -> Path:
    """Find a Julia executable by explicit path or on ``PATH``."""
    julia_text = os.fspath(julia)
    if _looks_like_path(julia_text):
        candidate = Path(julia_text).expanduser()
        candidates = [candidate]
        if os.name == "nt" and candidate.suffix.lower() != ".exe":
            candidates.append(candidate.with_suffix(candidate.suffix + ".exe"))
        for path in candidates:
            if path.exists() and path.is_file():
                return path
        raise JuliaNotFoundError(
            f"{JULIA_NOT_FOUND_MESSAGE}\nChecked explicit path: {candidate}"
        )

    found = shutil.which(julia_text)
    if found is None:
        raise JuliaNotFoundError(
            f"{JULIA_NOT_FOUND_MESSAGE}\nChecked command on PATH: {julia_text}"
        )
    return Path(found)


def _project_arg(project_dir: str | Path | None) -> list[str]:
    if project_dir is None:
        return []
    return [f"--project={Path(project_dir).expanduser()}"]


def get_julia_version(julia: str | Path = "julia") -> str:
    """Return ``julia --version`` output for the selected executable."""
    julia_text = os.fspath(julia)
    if _looks_like_path(julia_text):
        executable = Path(julia_text).expanduser()
        if os.name == "nt" and executable.suffix.lower() != ".exe":
            exe_candidate = executable.with_suffix(executable.suffix + ".exe")
            if exe_candidate.exists():
                executable = exe_candidate
    else:
        executable = find_julia(julia_text)
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            shell=False,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise JuliaNotFoundError(
            f"{JULIA_NOT_FOUND_MESSAGE}\nCould not execute: {executable}"
        ) from exc

    output = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0:
        raise JuliaNotFoundError(
            "Julia was found, but `julia --version` failed.\n\n"
            f"Executable: {executable}\n"
            f"Exit status: {completed.returncode}\n"
            f"Output: {output}"
        )
    return output


def check_openadmixture_installed(
    julia: str | Path = "julia",
    project_dir: str | Path | None = None,
) -> bool:
    """Return whether OpenADMIXTURE.jl imports in the selected environment."""
    executable = find_julia(julia)
    command = [
        str(executable),
        *_project_arg(project_dir),
        "-e",
        'using OpenADMIXTURE; println("OK")',
    ]
    completed = subprocess.run(
        command,
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0


def get_openadmixture_version(
    julia: str | Path = "julia",
    project_dir: str | Path | None = None,
) -> str | None:
    """Return the installed OpenADMIXTURE.jl version, if discoverable."""
    executable = find_julia(julia)
    julia_code = f"""
using OpenADMIXTURE
using Pkg
uuid = Base.UUID(\"{OPENADMIXTURE_UUID}\")
deps = Pkg.dependencies()
if haskey(deps, uuid) && deps[uuid].version !== nothing
    println(deps[uuid].version)
else
    println(\"unknown\")
end
"""
    completed = subprocess.run(
        [str(executable), *_project_arg(project_dir), "-e", julia_code],
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    version = completed.stdout.strip().splitlines()[-1] if completed.stdout else ""
    if version == "unknown":
        return None
    return version or None


def bootstrap_julia_project(
    project_dir: str | Path,
    julia: str | Path = "julia",
) -> None:
    """Create a Julia project and install OpenADMIXTURE.jl into it."""
    executable = find_julia(julia)
    project_path = Path(project_dir).expanduser()
    project_path.mkdir(parents=True, exist_ok=True)
    julia_code = f"""
using Pkg
Pkg.add(url=\"{SPARSE_KMEANS_URL}\")
Pkg.add(url=\"{OPENADMIXTURE_URL}\")
"""
    completed = subprocess.run(
        [str(executable), f"--project={project_path}", "-e", julia_code],
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise OpenAdmixtureNotInstalledError(
            f"{OPENADMIXTURE_NOT_INSTALLED_MESSAGE}\n"
            "Automatic Julia project bootstrap failed.\n\n"
            f"Project directory: {project_path}\n"
            f"Exit status: {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
