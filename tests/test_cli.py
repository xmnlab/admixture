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
    calls: list[str | Path] = []

    def fake_setup(*, julia: str | Path) -> Path:
        """
        title: Record setup arguments.
        parameters:
          julia:
            type: str | Path
        returns:
          type: Path
        """
        calls.append(julia)
        return tmp_path / "packaged-julia"

    monkeypatch.setattr(cli, "setup", fake_setup)

    returncode = cli.setup_main(
        [
            "--julia",
            "/opt/julia/bin/julia",
        ]
    )

    captured = capsys.readouterr()
    assert returncode == 0
    assert calls == ["/opt/julia/bin/julia"]
    assert "Julia project instantiated" in captured.out
    assert str(tmp_path / "packaged-julia") in captured.out
    assert captured.err == ""


def test_setup_main_uses_default_julia(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """
    title: The setup command can use the default Julia executable.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
      capsys:
        type: pytest.CaptureFixture[str]
    """
    calls: list[str | Path] = []
    project_dir = tmp_path / "packaged-julia"

    def fake_setup(*, julia: str | Path) -> Path:
        """
        title: Record setup arguments and return the packaged path.
        parameters:
          julia:
            type: str | Path
        returns:
          type: Path
        """
        calls.append(julia)
        return project_dir

    monkeypatch.setattr(cli, "setup", fake_setup)

    returncode = cli.setup_main([])

    captured = capsys.readouterr()
    assert returncode == 0
    assert calls == ["julia"]
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

    def fake_setup(*, julia: str | Path) -> Path:
        """
        title: Raise a Julia lookup error.
        parameters:
          julia:
            type: str | Path
        returns:
          type: Path
        """
        raise JuliaNotFoundError("no julia")

    monkeypatch.setattr(cli, "setup", fake_setup)

    returncode = cli.setup_main([])

    captured = capsys.readouterr()
    assert returncode == 1
    assert captured.out == ""
    assert "no julia" in captured.err
