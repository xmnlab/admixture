"""
title: Runtime tests using a tiny local PLINK data fixture.
"""

from __future__ import annotations

import shutil

from pathlib import Path

import numpy as np

from admixture import OpenAdmixtureRunner

N_SAMPLES = 8
N_SNPS = 24
DATA_DIR = Path(__file__).parent / "data" / "tiny-plink"


def _copy_tiny_plink(tmp_path: Path) -> Path:
    """
    title: Copy the tiny PLINK fixture into a writable temporary directory.
    parameters:
      tmp_path:
        type: Path
    returns:
      type: Path
    """
    prefix = tmp_path / "tiny-plink" / "tiny"
    prefix.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("bed", "bim", "fam"):
        shutil.copyfile(DATA_DIR / f"tiny.{suffix}", Path(f"{prefix}.{suffix}"))
    return prefix


def test_openadmixture_runs_on_tiny_local_plink(tmp_path: Path) -> None:
    """
    title: OpenADMIXTURE.jl runs on a tiny local PLINK data fixture.
    parameters:
      tmp_path:
        type: Path
    """
    plink_prefix = _copy_tiny_plink(tmp_path)
    out_prefix = tmp_path / "openadmixture" / "tiny_k2"

    runner = OpenAdmixtureRunner(timeout=120)
    assert runner.check_openadmixture(), (
        "OpenADMIXTURE.jl is required for runtime tests. Install it in the "
        "packaged Julia project by running `admixture-setup`."
    )

    result = runner.run(
        bfile=plink_prefix,
        k=2,
        out_prefix=out_prefix,
        seed=42,
        threads=1,
    )

    assert result.returncode == 0
    assert result.q_path.is_file()
    assert result.q.shape == (N_SAMPLES, 2)
    assert result.q.index.tolist() == [f"S{index + 1}" for index in range(N_SAMPLES)]
    assert result.p is not None
    assert result.p_path is not None
    assert result.p_path.is_file()
    assert result.p.shape == (2, N_SNPS)
    assert result.metadata["plink_prefix"] == str(plink_prefix)
    np.testing.assert_allclose(result.q.sum(axis=1).to_numpy(), 1.0, atol=1e-3)
