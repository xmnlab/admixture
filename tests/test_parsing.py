"""Tests for .fam, .Q, .P and output-discovery parsers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from admixture.exceptions import OutputParseError
from admixture.parsing import find_output_files, read_fam, read_p, read_q

FAM_TEXT = """F1 S1 0 0 1 -9
F1 S2 0 0 2 -9
F1 S3 0 0 1 -9
"""

Q_TEXT = """0.8 0.2
0.5 0.5
0.1 0.9
"""


def test_read_fam(tmp_path: Path) -> None:
    """FAM files are parsed as six whitespace-delimited columns."""

    fam_path = tmp_path / "example.fam"
    fam_path.write_text(FAM_TEXT)

    fam = read_fam(fam_path)

    assert list(fam.columns) == [
        "family_id",
        "individual_id",
        "paternal_id",
        "maternal_id",
        "sex",
        "phenotype",
    ]
    assert fam["individual_id"].tolist() == ["S1", "S2", "S3"]


def test_read_q_with_fam_index(tmp_path: Path) -> None:
    """Q files are parsed with ancestry columns and individual IDs."""

    fam_path = tmp_path / "example.fam"
    q_path = tmp_path / "example.Q"
    fam_path.write_text(FAM_TEXT)
    q_path.write_text(Q_TEXT)

    q = read_q(q_path, fam_path)

    assert list(q.columns) == ["ancestry_1", "ancestry_2"]
    assert q.index.tolist() == ["S1", "S2", "S3"]
    np.testing.assert_allclose(q.sum(axis=1).to_numpy(), 1.0)


def test_read_q_row_count_mismatch(tmp_path: Path) -> None:
    """A Q/.fam row mismatch raises a parsing error."""

    fam_path = tmp_path / "example.fam"
    q_path = tmp_path / "example.Q"
    fam_path.write_text(FAM_TEXT)
    q_path.write_text("0.8 0.2\n")

    with pytest.raises(OutputParseError, match="row count"):
        read_q(q_path, fam_path)


def test_read_q_invalid_numeric(tmp_path: Path) -> None:
    """Non-numeric Q files raise a parsing error."""

    q_path = tmp_path / "example.Q"
    q_path.write_text("0.8 nope\n")

    with pytest.raises(OutputParseError, match="numeric"):
        read_q(q_path)


def test_read_q_bad_row_sums(tmp_path: Path) -> None:
    """Q rows must sum approximately to one."""

    q_path = tmp_path / "example.Q"
    q_path.write_text("0.8 0.8\n")

    with pytest.raises(OutputParseError, match="sum"):
        read_q(q_path)


def test_read_p(tmp_path: Path) -> None:
    """P files are parsed as numeric matrices with generic SNP columns."""

    p_path = tmp_path / "example.P"
    p_path.write_text("0.1 0.2 0.3\n0.4 0.5 0.6\n")

    p = read_p(p_path)

    assert list(p.columns) == ["snp_1", "snp_2", "snp_3"]
    assert p.shape == (2, 3)


def test_find_output_files_common_patterns(tmp_path: Path) -> None:
    """Output discovery supports the wrapper's default file names."""

    prefix = tmp_path / "example"
    (tmp_path / "example.Q").write_text(Q_TEXT)
    (tmp_path / "example.P").write_text("0.1 0.2\n")
    (tmp_path / "example.log").write_text("ok\n")

    outputs = find_output_files(prefix, 2)

    assert outputs.q == tmp_path / "example.Q"
    assert outputs.p == tmp_path / "example.P"
    assert outputs.log == tmp_path / "example.log"


def test_find_output_files_ambiguous_q(tmp_path: Path) -> None:
    """Ambiguous Q candidates are rejected."""

    prefix = tmp_path / "example"
    (tmp_path / "example.Q").write_text(Q_TEXT)
    (tmp_path / "example.2.Q").write_text(Q_TEXT)

    with pytest.raises(OutputParseError, match="multiple"):
        find_output_files(prefix, 2)
