"""
title: Tests for OpenAdmixtureRunner command construction.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from admixture import OpenAdmixtureRunner


def test_build_command_uses_packaged_project_and_preserves_spaces(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    title: Paths with spaces remain single subprocess arguments.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
    """

    project_dir = tmp_path / "Julia Project"
    bfile = tmp_path / "plink data" / "example"
    out_prefix = tmp_path / "results dir" / "example_k2"
    monkeypatch.setattr(
        "admixture.runner.default_julia_project_dir", lambda: project_dir
    )
    runner = OpenAdmixtureRunner(julia="julia")

    command = runner._build_command(
        bfile=bfile,
        k=2,
        out_prefix=out_prefix,
        seed=42,
        threads=4,
    )

    assert isinstance(command, tuple)
    assert f"--project={project_dir}" in command
    assert "--threads=4" in command
    assert "--seed" in command
    assert "--threads" in command
    assert command[command.index("--bfile") + 1] == str(bfile)
    assert command[command.index("--out") + 1] == str(out_prefix)


def test_build_command_omits_optional_args_when_absent(tmp_path: Path) -> None:
    """
    title: Seed and thread args are emitted only when requested.
    parameters:
      tmp_path:
        type: Path
    """

    runner = OpenAdmixtureRunner(julia=Path("julia"))
    command = runner._build_command(
        bfile=tmp_path / "example",
        k=3,
        out_prefix=tmp_path / "out",
        seed=None,
        threads=None,
    )

    assert any(arg.startswith("--project=") for arg in command)
    assert not any(arg.startswith("--threads") for arg in command)
    assert "--seed" not in command


def test_build_command_accepts_extra_args(tmp_path: Path) -> None:
    """
    title: Extra algorithm parameters are converted to CLI flags.
    parameters:
      tmp_path:
        type: Path
    """

    runner = OpenAdmixtureRunner()
    command = runner._build_command(
        bfile=tmp_path / "example",
        k=2,
        out_prefix=tmp_path / "out",
        seed=None,
        threads=None,
        extra_args={"max_iter": 10, "tol": 1e-5},
    )

    assert "--max-iter" in command
    assert command[command.index("--max-iter") + 1] == "10"
    assert "--tol" in command
    assert command[command.index("--tol") + 1] == "1e-05"


def test_runner_uses_packaged_julia_project(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    title: Runner defaults to the packaged Julia project directory.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
    """
    project_dir = tmp_path / "packaged-julia"
    monkeypatch.setattr(
        "admixture.runner.default_julia_project_dir", lambda: project_dir
    )

    runner = OpenAdmixtureRunner()

    assert runner.project_dir == project_dir
