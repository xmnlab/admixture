"""
title: Tests for PLINK and parameter validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from admixture.exceptions import PlinkInputError
from admixture.validation import (
    ensure_output_parent,
    validate_k,
    validate_plink_prefix,
    validate_seed,
    validate_threads,
)


def _write_plink_trio(prefix: Path, *, empty_suffix: str | None = None) -> None:
    """
    title: Write a complete PLINK trio for validation tests.
    parameters:
      prefix:
        type: Path
      empty_suffix:
        type: str | None
    """
    for suffix in ("bed", "bim", "fam"):
        content = b"" if suffix == empty_suffix else b"x"
        (prefix.parent / f"{prefix.name}.{suffix}").write_bytes(content)


def test_validate_plink_prefix_accepts_valid_trio(tmp_path: Path) -> None:
    """
    title: A complete non-empty .bed/.bim/.fam trio is accepted.
    parameters:
      tmp_path:
        type: Path
    """

    prefix = tmp_path / "example"
    _write_plink_trio(prefix)

    files = validate_plink_prefix(prefix)

    assert files.prefix == prefix
    assert files.bed == tmp_path / "example.bed"
    assert files.bim == tmp_path / "example.bim"
    assert files.fam == tmp_path / "example.fam"


def test_validate_plink_prefix_normalises_bed_suffix(tmp_path: Path) -> None:
    """
    title: Passing example.bed is safely normalized to example.
    parameters:
      tmp_path:
        type: Path
    """

    prefix = tmp_path / "example"
    _write_plink_trio(prefix)

    files = validate_plink_prefix(tmp_path / "example.bed")

    assert files.prefix == prefix


@pytest.mark.parametrize("missing_suffix", ["bed", "bim", "fam"])
def test_validate_plink_prefix_missing_file(
    tmp_path: Path,
    missing_suffix: str,
) -> None:
    """
    title: Each required PLINK file is reported when absent.
    parameters:
      tmp_path:
        type: Path
      missing_suffix:
        type: str
    """

    prefix = tmp_path / "example"
    for suffix in ("bed", "bim", "fam"):
        if suffix != missing_suffix:
            (tmp_path / f"example.{suffix}").write_bytes(b"x")

    with pytest.raises(PlinkInputError, match=f"example\\.{missing_suffix}"):
        validate_plink_prefix(prefix)


def test_validate_plink_prefix_empty_file(tmp_path: Path) -> None:
    """
    title: Empty PLINK files are rejected.
    parameters:
      tmp_path:
        type: Path
    """

    prefix = tmp_path / "example"
    _write_plink_trio(prefix, empty_suffix="bed")

    with pytest.raises(PlinkInputError, match="empty"):
        validate_plink_prefix(prefix)


def test_validate_k_accepts_two_or_more() -> None:
    """
    title: K must be at least two.
    """

    assert validate_k(2) == 2
    assert validate_k(3) == 3


@pytest.mark.parametrize("bad_k", [1, 0, -1, 2.5, True])
def test_validate_k_rejects_invalid_values(bad_k: object) -> None:
    """
    title: Invalid K values raise ValueError.
    parameters:
      bad_k:
        type: object
    """

    with pytest.raises(ValueError):
        validate_k(cast(int, bad_k))


def test_validate_threads() -> None:
    """
    title: Thread count accepts None or positive integers.
    """

    assert validate_threads(None) is None
    assert validate_threads(4) == 4
    with pytest.raises(ValueError):
        validate_threads(0)
    with pytest.raises(ValueError):
        validate_threads(True)


def test_validate_seed() -> None:
    """
    title: Seed accepts None or non-negative integers.
    """

    assert validate_seed(None) is None
    assert validate_seed(42) == 42
    with pytest.raises(ValueError):
        validate_seed(-1)
    with pytest.raises(ValueError):
        validate_seed(False)


def test_ensure_output_parent_creates_directory(tmp_path: Path) -> None:
    """
    title: The output prefix parent directory is created.
    parameters:
      tmp_path:
        type: Path
    """

    output = ensure_output_parent(tmp_path / "with spaces" / "example_k2")

    assert output == tmp_path / "with spaces" / "example_k2"
    assert output.parent.is_dir()
