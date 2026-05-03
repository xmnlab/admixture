"""
title: High-level runner for invoking OpenADMIXTURE.jl from Python.
"""

from __future__ import annotations

import platform
import re
import subprocess
import sys

from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping

from ._version import __version__
from .exceptions import (
    OPENADMIXTURE_NOT_INSTALLED_MESSAGE,
    OpenAdmixtureNotInstalledError,
    OpenAdmixtureRunError,
)
from .julia_env import (
    JuliaInfo,
    bootstrap_julia_project,
    check_openadmixture_installed,
    find_julia,
    get_julia_version,
    get_openadmixture_version,
)
from .parsing import find_output_files, read_p, read_q
from .result import OpenAdmixtureResult
from .validation import (
    ensure_output_parent,
    validate_k,
    validate_plink_prefix,
    validate_seed,
    validate_threads,
)

_EXTRA_ARG_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


def _subprocess_output_to_text(output: str | bytes | None) -> str:
    """
    title: Normalize subprocess output to text.
    parameters:
      output:
        type: str | bytes | None
    returns:
      type: str
    """
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return output


class OpenAdmixtureRunner:
    """
    title: Run OpenADMIXTURE.jl on binary PLINK input data.
    attributes:
      julia:
        description: Julia executable name or path.
      project_dir:
        description: Optional Julia project directory.
      install_if_missing:
        description: Whether to bootstrap OpenADMIXTURE.jl when missing.
      timeout:
        description: Optional subprocess timeout in seconds.
      _resolved_julia:
        type: Path | None
    """

    def __init__(
        self,
        julia: str | Path = "julia",
        project_dir: str | Path | None = None,
        install_if_missing: bool = False,
        timeout: float | None = None,
    ) -> None:
        """
        title: Create a runner.
        parameters:
          julia:
            type: str | Path
          project_dir:
            type: str | Path | None
          install_if_missing:
            type: bool
          timeout:
            type: float | None
        """
        self.julia = julia
        self.project_dir = Path(project_dir).expanduser() if project_dir else None
        self.install_if_missing = install_if_missing
        self.timeout = timeout
        self._resolved_julia: Path | None = None

    def _julia_for_command(self) -> str:
        """
        title: Return the Julia executable string for a subprocess command.
        returns:
          type: str
        """
        if self._resolved_julia is not None:
            return str(self._resolved_julia)
        return str(self.julia)

    def check_julia(self) -> JuliaInfo:
        """
        title: Find Julia and return its executable path and version.
        returns:
          type: JuliaInfo
        """
        executable = find_julia(self.julia)
        self._resolved_julia = executable
        return JuliaInfo(executable=executable, version=get_julia_version(executable))

    def check_openadmixture(self) -> bool:
        """
        title: Return whether OpenADMIXTURE.jl imports successfully.
        returns:
          type: bool
        """
        julia = self._resolved_julia if self._resolved_julia else self.julia
        return check_openadmixture_installed(julia, self.project_dir)

    def version_info(self) -> dict[str, Any]:
        """
        title: Return Python, Julia and OpenADMIXTURE version metadata.
        returns:
          type: dict[str, Any]
        """
        julia_info = self.check_julia()
        openadmixture_installed = self.check_openadmixture()
        openadmixture_version = None
        if openadmixture_installed:
            openadmixture_version = get_openadmixture_version(
                julia_info.executable,
                self.project_dir,
            )
        return {
            "admixture_python_version": __version__,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "julia_executable": str(julia_info.executable),
            "julia_version": julia_info.version,
            "project_dir": str(self.project_dir) if self.project_dir else None,
            "openadmixture_installed": openadmixture_installed,
            "openadmixture_version": openadmixture_version,
        }

    def _build_command(
        self,
        *,
        bfile: Path,
        k: int,
        out_prefix: Path,
        seed: int | None,
        threads: int | None,
        extra_args: Mapping[str, str | int | float] | None = None,
    ) -> tuple[str, ...]:
        """
        title: Build the Julia subprocess command as a tuple of arguments.
        parameters:
          bfile:
            type: Path
          k:
            type: int
          out_prefix:
            type: Path
          seed:
            type: int | None
          threads:
            type: int | None
          extra_args:
            type: Mapping[str, str | int | float] | None
        returns:
          type: tuple[str, Ellipsis]
        """
        script = files("admixture").joinpath("julia/run_openadmixture.jl")
        command: list[str] = [self._julia_for_command()]
        if self.project_dir is not None:
            command.append(f"--project={self.project_dir}")
        if threads is not None:
            command.append(f"--threads={threads}")
        command.extend(
            [
                str(script),
                "--bfile",
                str(bfile),
                "--k",
                str(k),
                "--out",
                str(out_prefix),
            ]
        )
        if seed is not None:
            command.extend(["--seed", str(seed)])
        if threads is not None:
            command.extend(["--threads", str(threads)])
        if extra_args:
            for key, value in extra_args.items():
                flag = key.replace("_", "-")
                if not _EXTRA_ARG_RE.match(flag):
                    raise ValueError(
                        f"Invalid extra OpenADMIXTURE argument name: {key!r}"
                    )
                command.extend([f"--{flag}", str(value)])
        return tuple(command)

    def _ensure_openadmixture_available(self) -> None:
        """
        title: Ensure OpenADMIXTURE.jl can be imported before running.
        """
        if self.check_openadmixture():
            return
        if self.install_if_missing:
            if self.project_dir is None:
                raise OpenAdmixtureNotInstalledError(
                    f"{OPENADMIXTURE_NOT_INSTALLED_MESSAGE}\n"
                    "install_if_missing=True requires project_dir so that the "
                    "global Julia environment is not modified unexpectedly."
                )
            bootstrap_julia_project(self.project_dir, self._julia_for_command())
            if self.check_openadmixture():
                return
        raise OpenAdmixtureNotInstalledError(OPENADMIXTURE_NOT_INSTALLED_MESSAGE)

    def run(
        self,
        *,
        bfile: str | Path,
        k: int,
        out_prefix: str | Path,
        seed: int | None = None,
        threads: int | None = None,
        extra_args: Mapping[str, str | int | float] | None = None,
    ) -> OpenAdmixtureResult:
        """
        title: Run OpenADMIXTURE.jl and parse the output files.
        parameters:
          bfile:
            type: str | Path
          k:
            type: int
          out_prefix:
            type: str | Path
          seed:
            type: int | None
          threads:
            type: int | None
          extra_args:
            type: Mapping[str, str | int | float] | None
        returns:
          type: OpenAdmixtureResult
        """
        plink_files = validate_plink_prefix(bfile)
        validated_k = validate_k(k)
        validated_seed = validate_seed(seed)
        validated_threads = validate_threads(threads)
        output_prefix = ensure_output_parent(out_prefix)

        julia_info = self.check_julia()
        self._ensure_openadmixture_available()
        command = self._build_command(
            bfile=plink_files.prefix,
            k=validated_k,
            out_prefix=output_prefix,
            seed=validated_seed,
            threads=validated_threads,
            extra_args=extra_args,
        )

        try:
            completed = subprocess.run(
                command,
                shell=False,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = _subprocess_output_to_text(exc.stdout)
            stderr = _subprocess_output_to_text(exc.stderr)
            raise OpenAdmixtureRunError(
                "OpenADMIXTURE.jl timed out. Consider increasing timeout or "
                "checking the input size and Julia environment.\n\n"
                f"Command: {command}\nTimeout: {self.timeout} seconds\n"
                f"stdout:\n{stdout}\nstderr:\n{stderr}"
            ) from exc
        except OSError as exc:
            raise OpenAdmixtureRunError(
                "Failed to start the Julia OpenADMIXTURE backend.\n\n"
                f"Command: {command}\nError: {exc}"
            ) from exc

        if completed.returncode != 0:
            raise OpenAdmixtureRunError(
                "OpenADMIXTURE.jl exited with a nonzero status.\n\n"
                f"Exit status: {completed.returncode}\n"
                f"Command: {command}\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )

        output_files = find_output_files(output_prefix, validated_k)
        q = read_q(output_files.q, plink_files.fam)
        p = read_p(output_files.p) if output_files.p is not None else None
        metadata: dict[str, Any] = {
            "plink_prefix": str(plink_files.prefix),
            "bed_path": str(plink_files.bed),
            "bim_path": str(plink_files.bim),
            "fam_path": str(plink_files.fam),
            "julia_executable": str(julia_info.executable),
            "julia_version": julia_info.version,
            "project_dir": str(self.project_dir) if self.project_dir else None,
            "openadmixture_installed": True,
        }

        return OpenAdmixtureResult(
            q=q,
            p=p,
            q_path=output_files.q,
            p_path=output_files.p,
            log_path=output_files.log,
            out_prefix=output_prefix,
            k=validated_k,
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            metadata=metadata,
        )


def run_openadmixture(
    *,
    bfile: str | Path,
    k: int,
    out_prefix: str | Path,
    julia: str | Path = "julia",
    project_dir: str | Path | None = None,
    install_if_missing: bool = False,
    timeout: float | None = None,
    seed: int | None = None,
    threads: int | None = None,
    extra_args: Mapping[str, str | int | float] | None = None,
) -> OpenAdmixtureResult:
    """
    title: Run OpenADMIXTURE.jl once with a temporary runner.
    parameters:
      bfile:
        type: str | Path
      k:
        type: int
      out_prefix:
        type: str | Path
      julia:
        type: str | Path
      project_dir:
        type: str | Path | None
      install_if_missing:
        type: bool
      timeout:
        type: float | None
      seed:
        type: int | None
      threads:
        type: int | None
      extra_args:
        type: Mapping[str, str | int | float] | None
    returns:
      type: OpenAdmixtureResult
    """
    runner = OpenAdmixtureRunner(
        julia=julia,
        project_dir=project_dir,
        install_if_missing=install_if_missing,
        timeout=timeout,
    )
    return runner.run(
        bfile=bfile,
        k=k,
        out_prefix=out_prefix,
        seed=seed,
        threads=threads,
        extra_args=extra_args,
    )
