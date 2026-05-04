"""
title: Runtime tests using malariagen-data as a PLINK data source.
"""

from __future__ import annotations

import os
import sys

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from admixture import OpenAdmixtureRunner

pytestmark = pytest.mark.skipif(
    sys.version_info >= (3, 13),
    reason="malariagen-data is not available for Python 3.13+",
)


def _import_malariagen_data() -> Any:
    """
    title: Import malariagen-data only on supported Python versions.
    returns:
      type: Any
    """
    import malariagen_data  # noqa: PLC0415 - avoid importing on Python 3.13+

    return malariagen_data


def _openadmixture_runner() -> OpenAdmixtureRunner:
    """
    title: Create a runner backed by a real Julia/OpenADMIXTURE.jl environment.
    returns:
      type: OpenAdmixtureRunner
    """
    runner = OpenAdmixtureRunner()
    assert runner.check_openadmixture(), (
        "OpenADMIXTURE.jl is required for runtime tests. Install it in the "
        "packaged Julia project by running `admixture-setup`."
    )
    return runner


def _int_from_env(name: str, default: int) -> int:
    """
    title: Read an integer environment override.
    parameters:
      name:
        type: str
      default:
        type: int
    returns:
      type: int
    """
    raw = os.environ.get(name)
    return default if raw is None else int(raw)


def _fam_sample_count(prefix: Path) -> int:
    """
    title: Count samples in a PLINK FAM file.
    parameters:
      prefix:
        type: Path
    returns:
      type: int
    """
    return len(Path(f"{prefix}.fam").read_text().splitlines())


def _ag3_client(tmp_path: Path) -> Any:
    """
    title: Create an Ag3 API client for tests.
    parameters:
      tmp_path:
        type: Path
    returns:
      type: Any
    """
    malariagen_data = _import_malariagen_data()
    results_cache = os.environ.get("ADMIXTURE_TEST_MALARIAGEN_RESULTS_CACHE")
    if results_cache is None:
        results_cache = str(tmp_path / "malariagen-results-cache")
    return malariagen_data.Ag3(results_cache=results_cache)


def _malariagen_plink_prefix(tmp_path: Path) -> Path:
    """
    title: Export a small malariagen-data Ag3 SNP panel to PLINK files.
    parameters:
      tmp_path:
        type: Path
    returns:
      type: Path
    """
    ag3 = _ag3_client(tmp_path)
    output_dir = tmp_path / "malariagen-plink"
    output_dir.mkdir(parents=True, exist_ok=True)

    sample_query = os.environ.get("ADMIXTURE_TEST_MALARIAGEN_SAMPLE_QUERY")
    prefix = ag3.biallelic_snps_to_plink(
        output_dir=str(output_dir),
        region=os.environ.get(
            "ADMIXTURE_TEST_MALARIAGEN_REGION",
            "2L:2,400,000-2,500,000",
        ),
        n_snps=_int_from_env("ADMIXTURE_TEST_MALARIAGEN_N_SNPS", 50),
        overwrite=True,
        sample_sets=os.environ.get(
            "ADMIXTURE_TEST_MALARIAGEN_SAMPLE_SETS",
            "AG1000G-CI",
        ),
        sample_query=sample_query,
        min_minor_ac=_int_from_env("ADMIXTURE_TEST_MALARIAGEN_MIN_MINOR_AC", 2),
        max_missing_an=_int_from_env("ADMIXTURE_TEST_MALARIAGEN_MAX_MISSING_AN", 0),
        random_seed=42,
        out="ag3_openadmixture",
    )
    prefix_path = Path(prefix)
    for suffix in ("bed", "bim", "fam"):
        path = Path(f"{prefix_path}.{suffix}")
        assert path.is_file()
        assert path.stat().st_size > 0
    return prefix_path


def test_malariagen_data_exported_plink_runs_openadmixture(tmp_path: Path) -> None:
    """
    title: OpenADMIXTURE.jl runs on PLINK files exported by malariagen-data.
    parameters:
      tmp_path:
        type: Path
    """
    runner = _openadmixture_runner()
    plink_prefix = _malariagen_plink_prefix(tmp_path)
    out_prefix = tmp_path / "openadmixture" / "ag3_k2"

    result = runner.run(
        bfile=plink_prefix,
        k=2,
        out_prefix=out_prefix,
        seed=42,
        threads=1,
    )

    assert result.returncode == 0
    assert result.q_path.is_file()
    assert result.q.shape == (_fam_sample_count(plink_prefix), 2)
    assert result.p is not None
    assert result.p_path is not None
    assert result.p_path.is_file()
    assert result.p.shape[0] == 2
    assert result.metadata["plink_prefix"] == str(plink_prefix)
    np.testing.assert_allclose(result.q.sum(axis=1).to_numpy(), 1.0, atol=1e-3)
