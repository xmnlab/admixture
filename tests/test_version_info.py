"""Tests for Julia/OpenADMIXTURE environment metadata."""

from __future__ import annotations

from pathlib import Path

import pytest

from admixture import OpenAdmixtureRunner
from admixture.exceptions import JuliaNotFoundError
from admixture.julia_env import JuliaInfo, find_julia


def test_version_info(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Version metadata includes Python, Julia and backend fields."""

    runner = OpenAdmixtureRunner(project_dir=tmp_path / "julia_env")
    monkeypatch.setattr(
        runner,
        "check_julia",
        lambda: JuliaInfo(Path("/fake/julia"), "julia version 1.11.0"),
    )
    monkeypatch.setattr(runner, "check_openadmixture", lambda: True)
    monkeypatch.setattr(
        "admixture.runner.get_openadmixture_version",
        lambda julia, project_dir: "0.1.0",
    )

    info = runner.version_info()

    assert info["admixture_python_version"]
    assert info["python_version"]
    assert info["platform"]
    assert info["julia_executable"] == "/fake/julia"
    assert info["julia_version"] == "julia version 1.11.0"
    assert info["openadmixture_installed"] is True
    assert info["openadmixture_version"] == "0.1.0"


def test_find_julia_missing_raises_helpful_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing Julia raises the package-specific helpful exception."""

    monkeypatch.setattr("admixture.julia_env.shutil.which", lambda _: None)

    with pytest.raises(JuliaNotFoundError, match="Install Julia"):
        find_julia("definitely-not-julia")
