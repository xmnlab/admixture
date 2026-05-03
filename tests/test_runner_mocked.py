"""Runner tests that mock Julia subprocess execution."""

from __future__ import annotations

import subprocess

from pathlib import Path

import pytest

from admixture import OpenAdmixtureRunner
from admixture.exceptions import (
    OpenAdmixtureNotInstalledError,
    OpenAdmixtureRunError,
    OutputParseError,
)
from admixture.julia_env import JuliaInfo

FAM_TEXT = """F1 S1 0 0 1 -9
F1 S2 0 0 2 -9
F1 S3 0 0 1 -9
"""

Q_TEXT = """0.8 0.2
0.5 0.5
0.1 0.9
"""

P_TEXT = """0.1 0.2 0.3
0.4 0.5 0.6
"""


def _write_plink(prefix: Path) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    (prefix.parent / f"{prefix.name}.bed").write_bytes(b"plink-bed")
    (prefix.parent / f"{prefix.name}.bim").write_text("1 rs1 0 1 A C\n")
    (prefix.parent / f"{prefix.name}.fam").write_text(FAM_TEXT)


def _patch_environment(
    monkeypatch: pytest.MonkeyPatch,
    runner: OpenAdmixtureRunner,
) -> None:
    monkeypatch.setattr(
        runner,
        "check_julia",
        lambda: JuliaInfo(executable=Path("/fake/julia"), version="julia version 1.11"),
    )
    monkeypatch.setattr(runner, "check_openadmixture", lambda: True)


def test_runner_success_with_mocked_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A successful mocked Julia run returns parsed DataFrames."""

    bfile = tmp_path / "input data" / "example"
    out_prefix = tmp_path / "outputs" / "example_k2"
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
        assert shell is False
        assert capture_output is True
        assert text is True
        assert check is False
        (tmp_path / "outputs").mkdir(exist_ok=True)
        Path(f"{out_prefix}.Q").write_text(Q_TEXT)
        Path(f"{out_prefix}.P").write_text(P_TEXT)
        Path(f"{out_prefix}.log").write_text("ok\n")
        return subprocess.CompletedProcess(command, 0, "stdout", "")

    monkeypatch.setattr("admixture.runner.subprocess.run", fake_run)

    result = runner.run(bfile=bfile, k=2, out_prefix=out_prefix, seed=1, threads=1)

    assert result.q.shape == (3, 2)
    assert result.p is not None
    assert result.p.shape == (2, 3)
    assert result.q.index.tolist() == ["S1", "S2", "S3"]
    assert result.returncode == 0
    assert result.stdout == "stdout"


def test_runner_failure_with_mocked_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A nonzero Julia exit status raises OpenAdmixtureRunError."""

    bfile = tmp_path / "example"
    out_prefix = tmp_path / "out"
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
        assert shell is False
        return subprocess.CompletedProcess(command, 1, "", "boom")

    monkeypatch.setattr("admixture.runner.subprocess.run", fake_run)

    with pytest.raises(OpenAdmixtureRunError, match="boom"):
        runner.run(bfile=bfile, k=2, out_prefix=out_prefix)


def test_runner_missing_output_with_mocked_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A zero exit status without Q output raises OutputParseError."""

    bfile = tmp_path / "example"
    out_prefix = tmp_path / "out"
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
        assert shell is False
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("admixture.runner.subprocess.run", fake_run)

    with pytest.raises(OutputParseError, match="Q output"):
        runner.run(bfile=bfile, k=2, out_prefix=out_prefix)


def test_runner_missing_openadmixture_raises_helpful_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing OpenADMIXTURE.jl raises install guidance before execution."""

    bfile = tmp_path / "example"
    _write_plink(bfile)
    runner = OpenAdmixtureRunner()
    monkeypatch.setattr(
        runner,
        "check_julia",
        lambda: JuliaInfo(Path("/fake/julia"), "julia version 1.11"),
    )
    monkeypatch.setattr(runner, "check_openadmixture", lambda: False)

    with pytest.raises(OpenAdmixtureNotInstalledError, match=r"Pkg\.add"):
        runner.run(bfile=bfile, k=2, out_prefix=tmp_path / "out")
