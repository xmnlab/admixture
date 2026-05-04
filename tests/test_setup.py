"""
title: Tests for packaged Julia setup helpers.
"""

from __future__ import annotations

import importlib
import subprocess

from pathlib import Path

import pytest

admixture_setup_module = importlib.import_module("admixture.setup")


def test_default_julia_project_dir_points_to_packaged_project() -> None:
    """
    title: The default Julia project lives inside the Python package.
    """
    project_dir = admixture_setup_module.default_julia_project_dir()

    assert project_dir.name == "julia-env"
    assert project_dir.parent.name == "admixture"
    assert (project_dir / "Project.toml").is_file()
    assert (project_dir / "Manifest.toml").is_file()


def test_instantiate_julia_project_uses_packaged_project(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    title: Julia project instantiation targets the packaged project.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
    """
    project_dir = tmp_path / "packaged-julia"
    monkeypatch.setattr(
        admixture_setup_module, "default_julia_project_dir", lambda: project_dir
    )
    monkeypatch.setattr(
        admixture_setup_module,
        "find_julia",
        lambda julia: Path("/fake/julia"),
    )

    def fake_run(
        command: list[str],
        *,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        """
        title: Return a successful Julia project instantiation.
        parameters:
          command:
            type: list[str]
          shell:
            type: bool
          capture_output:
            type: bool
          text:
            type: bool
          check:
            type: bool
        returns:
          type: subprocess.CompletedProcess[str]
        """
        assert command[0] == "/fake/julia"
        assert command[1] == f"--project={project_dir}"
        assert "Pkg.instantiate()" in command[-1]
        assert shell is False
        assert capture_output is True
        assert text is True
        assert check is False
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(admixture_setup_module.subprocess, "run", fake_run)

    assert (
        admixture_setup_module.instantiate_julia_project(julia="julia-bin")
        == project_dir
    )


def test_setup_instantiates_and_checks_packaged_project(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    title: Setup instantiates and checks the packaged Julia project.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
    """
    project_dir = tmp_path / "packaged-julia"
    calls: list[tuple[str | Path, Path]] = []
    monkeypatch.setattr(
        admixture_setup_module,
        "instantiate_julia_project",
        lambda julia: project_dir,
    )

    def fake_check(julia: str | Path, project_dir: str | Path | None) -> bool:
        """
        title: Record OpenADMIXTURE import checks.
        parameters:
          julia:
            type: str | Path
          project_dir:
            type: str | Path | None
        returns:
          type: bool
        """
        assert project_dir is not None
        calls.append((julia, Path(project_dir)))
        return True

    monkeypatch.setattr(
        admixture_setup_module,
        "check_openadmixture_installed",
        fake_check,
    )

    assert admixture_setup_module.setup(julia="julia-bin") == project_dir
    assert calls == [("julia-bin", project_dir)]
