"""Tests for PLINK and parameter validation."""

from __future__ import annotations

import pytest

from admixture.exceptions import PlinkInputError
from admixture.validation import (
    ensure_output_parent,
    validate_k,
    validate_plink_prefix,
    validate_seed,
    validate_threads,
)


def _write_plink_trio(prefix, *, empty_suffix: str | None = None) -> None:
    for suffix in ("bed", "bim", "fam"):
        content = b"" if suffix == empty_suffix else b"x"
        (prefix.parent / f"{prefix.name}.{suffix}").write_bytes(content)


def test_validate_plink_prefix_accepts_valid_trio(tmp_path) -> None:
    """A complete non-empty .bed/.bim/.fam trio is accepted."""

    prefix = tmp_path / "example"
    _write_plink_trio(prefix)

    files = validate_plink_prefix(prefix)

    assert files.prefix == prefix
    assert files.bed == tmp_path / "example.bed"
    assert files.bim == tmp_path / "example.bim"
    assert files.fam == tmp_path / "example.fam"


def test_validate_plink_prefix_normalises_bed_suffix(tmp_path) -> None:
    """Passing example.bed is safely normalized to example."""

    prefix = tmp_path / "example"
    _write_plink_trio(prefix)

    files = validate_plink_prefix(tmp_path / "example.bed")

    assert files.prefix == prefix


@pytest.mark.parametrize("missing_suffix", ["bed", "bim", "fam"])
def test_validate_plink_prefix_missing_file(tmp_path, missing_suffix) -> None:
    """Each required PLINK file is reported when absent."""

    prefix = tmp_path / "example"
    for suffix in ("bed", "bim", "fam"):
        if suffix != missing_suffix:
            (tmp_path / f"example.{suffix}").write_bytes(b"x")

    with pytest.raises(PlinkInputError, match=f"example\\.{missing_suffix}"):
        validate_plink_prefix(prefix)


def test_validate_plink_prefix_empty_file(tmp_path) -> None:
    """Empty PLINK files are rejected."""

    prefix = tmp_path / "example"
    _write_plink_trio(prefix, empty_suffix="bed")

    with pytest.raises(PlinkInputError, match="empty"):
        validate_plink_prefix(prefix)


def test_validate_k_accepts_two_or_more() -> None:
    """K must be at least two."""

    assert validate_k(2) == 2
    assert validate_k(3) == 3


@pytest.mark.parametrize("bad_k", [1, 0, -1, 2.5, True])
def test_validate_k_rejects_invalid_values(bad_k) -> None:
    """Invalid K values raise ValueError."""

    with pytest.raises(ValueError):
        validate_k(bad_k)  # type: ignore[arg-type]


def test_validate_threads() -> None:
    """Thread count accepts None or positive integers."""

    assert validate_threads(None) is None
    assert validate_threads(4) == 4
    with pytest.raises(ValueError):
        validate_threads(0)
    with pytest.raises(ValueError):
        validate_threads(True)  # type: ignore[arg-type]


def test_validate_seed() -> None:
    """Seed accepts None or non-negative integers."""

    assert validate_seed(None) is None
    assert validate_seed(42) == 42
    with pytest.raises(ValueError):
        validate_seed(-1)
    with pytest.raises(ValueError):
        validate_seed(False)  # type: ignore[arg-type]


def test_ensure_output_parent_creates_directory(tmp_path) -> None:
    """The output prefix parent directory is created."""

    output = ensure_output_parent(tmp_path / "with spaces" / "example_k2")

    assert output == tmp_path / "with spaces" / "example_k2"
    assert output.parent.is_dir()
