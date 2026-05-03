"""
title: Tests for OpenADMIXTURE result containers.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from admixture.result import OpenAdmixtureResult


def _make_result(tmp_path: Path, p: pd.DataFrame | None) -> OpenAdmixtureResult:
    """
    title: Build a small result object for tests.
    parameters:
      tmp_path:
        type: Path
      p:
        type: pd.DataFrame | None
    returns:
      type: OpenAdmixtureResult
    """
    return OpenAdmixtureResult(
        q=pd.DataFrame({"ancestry_1": [0.7], "ancestry_2": [0.3]}, index=["S1"]),
        p=p,
        q_path=tmp_path / "example.Q",
        p_path=tmp_path / "example.P" if p is not None else None,
        log_path=tmp_path / "example.log",
        out_prefix=tmp_path / "example",
        k=2,
        command=("julia", "run_openadmixture.jl"),
        returncode=0,
        stdout="stdout",
        stderr="stderr",
        metadata={"julia_version": "julia version 1.11.0"},
    )


def test_result_to_csv_writes_q_and_p(tmp_path: Path) -> None:
    """
    title: Result CSV export writes Q and P files.
    parameters:
      tmp_path:
        type: Path
    """
    p = pd.DataFrame({"snp_1": [0.1, 0.2]})
    result = _make_result(tmp_path, p)

    result.to_csv(tmp_path / "exports" / "example")

    assert (tmp_path / "exports" / "example.Q.csv").is_file()
    assert (tmp_path / "exports" / "example.P.csv").is_file()


def test_result_to_csv_skips_missing_p(tmp_path: Path) -> None:
    """
    title: Result CSV export skips absent P files.
    parameters:
      tmp_path:
        type: Path
    """
    result = _make_result(tmp_path, None)

    result.to_csv(tmp_path / "exports" / "example")

    assert (tmp_path / "exports" / "example.Q.csv").is_file()
    assert not (tmp_path / "exports" / "example.P.csv").exists()


def test_result_summary(tmp_path: Path) -> None:
    """
    title: Result summaries include dimensions and output paths.
    parameters:
      tmp_path:
        type: Path
    """
    result = _make_result(tmp_path, pd.DataFrame({"snp_1": [0.1]}))

    assert result.summary() == {
        "k": 2,
        "n_individuals": 1,
        "n_ancestries": 2,
        "has_p": True,
        "q_path": str(tmp_path / "example.Q"),
        "p_path": str(tmp_path / "example.P"),
        "log_path": str(tmp_path / "example.log"),
        "returncode": 0,
    }
