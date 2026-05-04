"""
title: Tests for runner edge cases.
"""

from __future__ import annotations

import subprocess

from pathlib import Path

import pandas as pd
import pytest

from admixture import OpenAdmixtureResult, OpenAdmixtureRunner, run_openadmixture
from admixture.exceptions import OpenAdmixtureRunError
from admixture.julia_env import JuliaInfo

FAM_TEXT = """F1 S1 0 0 1 -9
"""


def _write_plink(prefix: Path) -> None:
    """
    title: Write a minimal PLINK trio.
    parameters:
      prefix:
        type: Path
    """
    prefix.parent.mkdir(parents=True, exist_ok=True)
    (prefix.parent / f"{prefix.name}.bed").write_bytes(b"bed")
    (prefix.parent / f"{prefix.name}.bim").write_text("1 rs1 0 1 A C\n")
    (prefix.parent / f"{prefix.name}.fam").write_text(FAM_TEXT)


def _patch_environment(
    monkeypatch: pytest.MonkeyPatch,
    runner: OpenAdmixtureRunner,
) -> None:
    """
    title: Patch Julia and OpenADMIXTURE availability checks.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      runner:
        type: OpenAdmixtureRunner
    """
    monkeypatch.setattr(
        runner,
        "check_julia",
        lambda: JuliaInfo(Path("/fake/julia"), "julia version 1.11"),
    )
    monkeypatch.setattr(runner, "check_openadmixture", lambda: True)


def test_build_command_rejects_invalid_extra_arg(tmp_path: Path) -> None:
    """
    title: Extra argument names must be safe CLI flag names.
    parameters:
      tmp_path:
        type: Path
    """
    runner = OpenAdmixtureRunner()

    with pytest.raises(ValueError, match="Invalid extra"):
        runner._build_command(
            bfile=tmp_path / "example",
            k=2,
            out_prefix=tmp_path / "out",
            seed=None,
            threads=None,
            extra_args={"bad flag": 1},
        )


def test_runner_timeout_is_wrapped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    title: Subprocess timeouts are wrapped with captured output.
    parameters:
      tmp_path:
        type: Path
      monkeypatch:
        type: pytest.MonkeyPatch
    """
    bfile = tmp_path / "example"
    _write_plink(bfile)
    runner = OpenAdmixtureRunner(timeout=1)
    _patch_environment(monkeypatch, runner)

    def fake_run(
        command: tuple[str, ...],
        *,
        shell: bool,
        capture_output: bool,
        text: bool,
        timeout: float | None,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        """
        title: Raise a timeout for the runner subprocess.
        parameters:
          command:
            type: tuple[str, Ellipsis]
          shell:
            type: bool
          capture_output:
            type: bool
          text:
            type: bool
          timeout:
            type: float | None
          check:
            type: bool
        returns:
          type: subprocess.CompletedProcess[str]
        """
        raise subprocess.TimeoutExpired(command, 1.0, output=b"out", stderr=b"err")

    monkeypatch.setattr("admixture.runner.subprocess.run", fake_run)

    with pytest.raises(OpenAdmixtureRunError, match="timed out") as exc_info:
        runner.run(bfile=bfile, k=2, out_prefix=tmp_path / "out")

    assert "out" in str(exc_info.value)
    assert "err" in str(exc_info.value)


def test_runner_os_error_is_wrapped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    title: OS errors starting Julia are wrapped.
    parameters:
      tmp_path:
        type: Path
      monkeypatch:
        type: pytest.MonkeyPatch
    """
    bfile = tmp_path / "example"
    _write_plink(bfile)
    runner = OpenAdmixtureRunner()
    _patch_environment(monkeypatch, runner)

    def fake_run(
        command: tuple[str, ...],
        *,
        shell: bool,
        capture_output: bool,
        text: bool,
        timeout: float | None,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        """
        title: Raise an OS error for the runner subprocess.
        parameters:
          command:
            type: tuple[str, Ellipsis]
          shell:
            type: bool
          capture_output:
            type: bool
          text:
            type: bool
          timeout:
            type: float | None
          check:
            type: bool
        returns:
          type: subprocess.CompletedProcess[str]
        """
        raise OSError("cannot start")

    monkeypatch.setattr("admixture.runner.subprocess.run", fake_run)

    with pytest.raises(OpenAdmixtureRunError, match="Failed to start"):
        runner.run(bfile=bfile, k=2, out_prefix=tmp_path / "out")


def test_ensure_openadmixture_bootstrap_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    title: Automatic OpenADMIXTURE bootstrap succeeds when import checks pass.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
    """
    runner = OpenAdmixtureRunner(install_if_missing=True)
    checks = iter([False, True])
    monkeypatch.setattr(runner, "check_openadmixture", lambda: next(checks))
    monkeypatch.setattr("admixture.runner.setup", lambda julia: runner.project_dir)

    runner._ensure_openadmixture_available()


def test_run_openadmixture_uses_temporary_runner(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    title: Convenience function delegates to a temporary runner.
    parameters:
      monkeypatch:
        type: pytest.MonkeyPatch
      tmp_path:
        type: Path
    """

    monkeypatch.setattr(
        "admixture.runner.default_julia_project_dir",
        lambda: tmp_path / "packaged-julia",
    )

    def fake_run(
        self: OpenAdmixtureRunner,
        *,
        bfile: str | Path,
        k: int,
        out_prefix: str | Path,
        seed: int | None,
        threads: int | None,
        extra_args: dict[str, int] | None,
    ) -> OpenAdmixtureResult:
        """
        title: Return a result from the temporary runner.
        parameters:
          self:
            type: OpenAdmixtureRunner
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
            type: dict[str, int] | None
        returns:
          type: OpenAdmixtureResult
        """
        assert self.project_dir == tmp_path / "packaged-julia"
        assert self.install_if_missing is True
        assert self.timeout == 10
        assert bfile == tmp_path / "example"
        assert k == 2
        assert out_prefix == tmp_path / "out"
        assert seed == 1
        assert threads == 2
        assert extra_args == {"max_iter": 10}
        return OpenAdmixtureResult(
            q=pd.DataFrame({"ancestry_1": [1.0]}),
            p=None,
            q_path=tmp_path / "out.Q",
            p_path=None,
            log_path=None,
            out_prefix=tmp_path / "out",
            k=2,
            command=("julia",),
            returncode=0,
            stdout="",
            stderr="",
            metadata={},
        )

    monkeypatch.setattr(OpenAdmixtureRunner, "run", fake_run)

    result = run_openadmixture(
        bfile=tmp_path / "example",
        k=2,
        out_prefix=tmp_path / "out",
        install_if_missing=True,
        timeout=10,
        seed=1,
        threads=2,
        extra_args={"max_iter": 10},
    )

    assert result.k == 2
