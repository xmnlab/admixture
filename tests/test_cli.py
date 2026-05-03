"""
title: Tests for command line entry points.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from admixture import cli
from admixture.exceptions import JuliaNotFoundError


def test_setup_main_calls_setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    title: The setup command delegates to the Python setup helper.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
      capsys:
        type: pytest.CaptureFixture[str]
    """
    calls: list[tuple[str | Path, str | Path]] = []

    def fake_setup(*, project_dir: str | Path, julia: str | Path) -> None:
        """
        title: Record setup arguments.
        parameters:
          project_dir:
            type: str | Path
          julia:
            type: str | Path
        """
        calls.append((project_dir, julia))

    project_dir = tmp_path / "julia env"
    monkeypatch.setattr(cli, "setup", fake_setup)

    returncode = cli.setup_main(
        [
            "--project-dir",
            str(project_dir),
            "--julia",
            "/opt/julia/bin/julia",
        ]
    )

    captured = capsys.readouterr()
    assert returncode == 0
    assert calls == [(str(project_dir), "/opt/julia/bin/julia")]
    assert "OpenADMIXTURE.jl installed" in captured.out
    assert str(project_dir) in captured.out
    assert captured.err == ""


def test_setup_main_reports_package_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    title: The setup command reports known package errors without a traceback.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
      capsys:
        type: pytest.CaptureFixture[str]
    """

    def fake_setup(*, project_dir: str | Path, julia: str | Path) -> None:
        """
        title: Raise a Julia lookup error.
        parameters:
          project_dir:
            type: str | Path
          julia:
            type: str | Path
        """
        raise JuliaNotFoundError("no julia")

    monkeypatch.setattr(cli, "setup", fake_setup)

    returncode = cli.setup_main(["--project-dir", str(tmp_path / "julia")])

    captured = capsys.readouterr()
    assert returncode == 1
    assert captured.out == ""
    assert "no julia" in captured.err
