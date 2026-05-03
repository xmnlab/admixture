"""
title: Tests for Julia environment helpers.
"""

from __future__ import annotations

import subprocess

from pathlib import Path

import pytest

from admixture.exceptions import JuliaNotFoundError, OpenAdmixtureNotInstalledError
from admixture.julia_env import (
    _looks_like_path,
    _project_arg,
    bootstrap_julia_project,
    check_openadmixture_installed,
    find_julia,
    get_julia_version,
    get_openadmixture_version,
)


def test_looks_like_path_detects_paths() -> None:
    """
    title: Path-like Julia arguments are detected.
    """
    assert _looks_like_path("/usr/bin/julia")
    assert _looks_like_path("bin/julia")
    assert _looks_like_path(r"C:\Julia\bin\julia.exe")
    assert not _looks_like_path("julia")


def test_find_julia_accepts_explicit_path(tmp_path: Path) -> None:
    """
    title: Explicit Julia executable paths are accepted.
    parameters:
      tmp_path:
        type: Path
    """
    executable = tmp_path / "julia"
    executable.write_text("#!/bin/sh\n")

    assert find_julia(executable) == executable


def test_find_julia_uses_path_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    title: Julia command names are resolved from PATH.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
    """
    monkeypatch.setattr("admixture.julia_env.shutil.which", lambda _: "/bin/julia")

    assert find_julia("julia") == Path("/bin/julia")


def test_find_julia_missing_command_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    title: Missing Julia commands raise a helpful error.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
    """
    monkeypatch.setattr("admixture.julia_env.shutil.which", lambda _: None)

    with pytest.raises(JuliaNotFoundError, match="Checked command on PATH"):
        find_julia("julia")


def test_get_julia_version_from_stdout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    title: Julia version output is read from stdout.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
    """
    executable = tmp_path / "julia"

    def fake_run(
        command: list[str],
        *,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        """
        title: Return successful Julia version output.
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
        assert command == [str(executable), "--version"]
        assert shell is False
        assert capture_output is True
        assert text is True
        assert check is False
        return subprocess.CompletedProcess(command, 0, "julia version 1.11.0\n", "")

    monkeypatch.setattr("admixture.julia_env.subprocess.run", fake_run)

    assert get_julia_version(executable) == "julia version 1.11.0"


def test_get_julia_version_failure_raises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    title: Failed Julia version commands raise a helpful error.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
    """
    executable = tmp_path / "julia"

    def fake_run(
        command: list[str],
        *,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        """
        title: Return a failed Julia version command.
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
        return subprocess.CompletedProcess(command, 1, "", "boom\n")

    monkeypatch.setattr("admixture.julia_env.subprocess.run", fake_run)

    with pytest.raises(JuliaNotFoundError, match="julia --version"):
        get_julia_version(executable)


def test_get_julia_version_os_error_raises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    title: OS errors while running Julia are wrapped.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
    """
    executable = tmp_path / "julia"

    def fake_run(
        command: list[str],
        *,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        """
        title: Raise an OS error for Julia execution.
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
        raise OSError("not executable")

    monkeypatch.setattr("admixture.julia_env.subprocess.run", fake_run)

    with pytest.raises(JuliaNotFoundError, match="Could not execute"):
        get_julia_version(executable)


def test_project_arg() -> None:
    """
    title: Julia project arguments are built only when requested.
    """
    assert _project_arg(None) == []
    assert _project_arg("julia-env") == [f"--project={Path('julia-env')}"]


def test_check_openadmixture_installed_runs_import_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    title: OpenADMIXTURE installation checks run Julia import code.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
    """
    monkeypatch.setattr(
        "admixture.julia_env.find_julia",
        lambda _: Path("/fake/julia"),
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
        title: Return a successful OpenADMIXTURE import check.
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
        assert command[:2] == ["/fake/julia", "--project=julia-env"]
        assert command[-2:] == ["-e", 'using OpenADMIXTURE; println("OK")']
        return subprocess.CompletedProcess(command, 0, "OK\n", "")

    monkeypatch.setattr("admixture.julia_env.subprocess.run", fake_run)

    assert check_openadmixture_installed("julia", "julia-env")


@pytest.mark.parametrize(
    ("returncode", "stdout", "expected"),
    [
        (0, "0.7.1\n", "0.7.1"),
        (0, "unknown\n", None),
        (0, "", None),
        (1, "boom\n", None),
    ],
)
def test_get_openadmixture_version(
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    stdout: str,
    expected: str | None,
) -> None:
    """
    title: OpenADMIXTURE version discovery handles common outcomes.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      returncode:
        type: int
      stdout:
        type: str
      expected:
        type: str | None
    """
    monkeypatch.setattr(
        "admixture.julia_env.find_julia",
        lambda _: Path("/fake/julia"),
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
        title: Return a mocked OpenADMIXTURE version lookup.
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
        assert command[1] == "-e"
        return subprocess.CompletedProcess(command, returncode, stdout, "")

    monkeypatch.setattr("admixture.julia_env.subprocess.run", fake_run)

    assert get_openadmixture_version("julia") == expected


def test_bootstrap_julia_project_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    title: Julia project bootstrap creates the project directory.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
    """
    monkeypatch.setattr(
        "admixture.julia_env.find_julia",
        lambda _: Path("/fake/julia"),
    )
    project_dir = tmp_path / "julia-env"

    def fake_run(
        command: list[str],
        *,
        shell: bool,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        """
        title: Return a successful Julia bootstrap.
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
        assert command[1] == f"--project={project_dir}"
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("admixture.julia_env.subprocess.run", fake_run)

    bootstrap_julia_project(project_dir)

    assert project_dir.is_dir()


def test_bootstrap_julia_project_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    title: Julia project bootstrap failures are reported.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
    """
    monkeypatch.setattr(
        "admixture.julia_env.find_julia",
        lambda _: Path("/fake/julia"),
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
        title: Return a failed Julia bootstrap.
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
        return subprocess.CompletedProcess(command, 1, "stdout", "stderr")

    monkeypatch.setattr("admixture.julia_env.subprocess.run", fake_run)

    with pytest.raises(OpenAdmixtureNotInstalledError, match="bootstrap failed"):
        bootstrap_julia_project(tmp_path / "julia-env")
