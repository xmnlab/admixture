"""Optional integration tests requiring Julia, OpenADMIXTURE.jl and PLINK data."""

from __future__ import annotations

import os
import shutil

import numpy as np
import pytest

from admixture import OpenAdmixtureRunner


@pytest.mark.integration
def test_openadmixture_integration(tmp_path) -> None:
    """Run OpenADMIXTURE.jl against a user-provided PLINK prefix."""

    prefix = os.environ.get("ADMIXTURE_TEST_PLINK_PREFIX")
    if not prefix:
        pytest.skip("Set ADMIXTURE_TEST_PLINK_PREFIX to run integration test")
    if shutil.which("julia") is None:
        pytest.skip("Julia executable is not available on PATH")

    project_dir = os.environ.get("ADMIXTURE_TEST_JULIA_PROJECT")
    runner = OpenAdmixtureRunner(project_dir=project_dir)
    if not runner.check_openadmixture():
        pytest.skip("OpenADMIXTURE.jl is not installed in the Julia environment")

    result = runner.run(
        bfile=prefix,
        k=2,
        out_prefix=tmp_path / "integration",
        seed=1,
        threads=1,
    )

    assert not result.q.empty
    assert result.q.shape[1] == 2
    np.testing.assert_allclose(result.q.sum(axis=1).to_numpy(), 1.0, atol=1e-3)
