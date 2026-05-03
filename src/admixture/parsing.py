"""Parsers for PLINK metadata and OpenADMIXTURE output files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .exceptions import OutputParseError

FAM_COLUMNS = [
    "family_id",
    "individual_id",
    "paternal_id",
    "maternal_id",
    "sex",
    "phenotype",
]


@dataclass(frozen=True)
class OutputFiles:
    """OpenADMIXTURE output files discovered for a run."""

    q: Path
    p: Path | None
    log: Path | None


def read_fam(path: str | Path) -> pd.DataFrame:
    """Read a standard six-column PLINK ``.fam`` file."""
    fam_path = Path(path)
    try:
        fam = pd.read_csv(fam_path, sep=r"\s+", header=None, dtype=str)
    except FileNotFoundError as exc:
        raise OutputParseError(f"Could not find .fam file: {fam_path}") from exc
    except pd.errors.EmptyDataError as exc:
        raise OutputParseError(f"The .fam file is empty: {fam_path}") from exc
    except Exception as exc:  # pragma: no cover - pandas exception details vary.
        raise OutputParseError(f"Could not parse .fam file {fam_path}: {exc}") from exc

    if fam.shape[1] != len(FAM_COLUMNS):
        raise OutputParseError(
            f"Expected {len(FAM_COLUMNS)} columns in .fam file {fam_path}, "
            f"found {fam.shape[1]}."
        )
    fam.columns = FAM_COLUMNS
    return fam


def _read_numeric_matrix(path: str | Path, *, label: str) -> pd.DataFrame:
    matrix_path = Path(path)
    try:
        data = pd.read_csv(
            matrix_path,
            sep=r"\s+",
            header=None,
            dtype=float,
        )
    except FileNotFoundError as exc:
        raise OutputParseError(f"Could not find {label} file: {matrix_path}") from exc
    except pd.errors.EmptyDataError as exc:
        raise OutputParseError(f"The {label} file is empty: {matrix_path}") from exc
    except Exception as exc:
        raise OutputParseError(
            f"Could not parse {label} file {matrix_path} as a numeric matrix: {exc}"
        ) from exc

    values = data.to_numpy(dtype=float)
    if values.size == 0 or data.shape[0] == 0 or data.shape[1] == 0:
        raise OutputParseError(
            f"The {label} file contains no numeric values: {matrix_path}"
        )
    if not np.isfinite(values).all():
        raise OutputParseError(
            f"The {label} file contains NaN or infinite values: {matrix_path}"
        )
    return data


def read_q(
    path: str | Path,
    fam_path: str | Path | None = None,
    *,
    row_sum_tolerance: float = 1e-3,
) -> pd.DataFrame:
    """Read an ancestry-proportion ``.Q`` matrix.

    Rows are individuals and columns are named ``ancestry_1``,
    ``ancestry_2``, ... . When ``fam_path`` is provided, the index is set to
    the PLINK individual IDs from the matching ``.fam`` file.
    """
    q = _read_numeric_matrix(path, label="Q")
    q.columns = [f"ancestry_{index}" for index in range(1, q.shape[1] + 1)]

    if fam_path is not None:
        fam = read_fam(fam_path)
        if len(fam) != len(q):
            raise OutputParseError(
                "The Q file row count does not match the .fam file. "
                f"Q rows: {len(q)}; .fam rows: {len(fam)}."
            )
        q.index = fam["individual_id"].astype(str)
        q.index.name = "individual_id"
        q.attrs["family_id"] = fam["family_id"].astype(str).tolist()

    row_sums = q.to_numpy(dtype=float).sum(axis=1)
    if not np.allclose(row_sums, 1.0, atol=row_sum_tolerance, rtol=0.0):
        max_deviation = float(np.max(np.abs(row_sums - 1.0)))
        raise OutputParseError(
            "Rows in the Q matrix should sum approximately to 1. "
            f"Maximum deviation was {max_deviation:.6g}; tolerance is "
            f"{row_sum_tolerance:.6g}."
        )

    return q


def read_p(path: str | Path) -> pd.DataFrame:
    """Read an allele-frequency ``.P`` matrix."""
    p = _read_numeric_matrix(path, label="P")
    p.columns = [f"snp_{index}" for index in range(1, p.shape[1] + 1)]
    return p


def _candidate_paths(out_prefix: Path, k: int, extension: str) -> list[Path]:
    prefix = str(out_prefix)
    return [
        Path(f"{prefix}.{extension}"),
        Path(f"{prefix}.{extension.lower()}"),
        Path(f"{prefix}.{k}.{extension}"),
        Path(f"{prefix}.{k}.{extension.lower()}"),
        Path(f"{prefix}_K{k}.{extension}"),
        Path(f"{prefix}_K{k}.{extension.lower()}"),
    ]


def _existing_unique(candidates: Iterable[Path], *, label: str) -> list[Path]:
    seen: set[Path] = set()
    existing: list[Path] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            existing.append(candidate)
    if len(existing) > 1:
        files = "\n".join(f"  - {path}" for path in existing)
        raise OutputParseError(
            f"Found multiple candidate {label} output files and cannot choose "
            f"safely. Remove stale outputs or use a unique out_prefix.\n{files}"
        )
    return existing


def find_output_files(out_prefix: str | Path, k: int) -> OutputFiles:
    """Find Q, P and log outputs for an OpenADMIXTURE run."""
    prefix = Path(out_prefix)
    q_candidates = _candidate_paths(prefix, k, "Q")
    p_candidates = _candidate_paths(prefix, k, "P")
    log_candidates = _candidate_paths(prefix, k, "log")

    q_existing = _existing_unique(q_candidates, label="Q")
    if not q_existing:
        tried = "\n".join(f"  - {path}" for path in q_candidates)
        raise OutputParseError(
            "Could not find an OpenADMIXTURE Q output file. Tried:\n" f"{tried}"
        )

    p_existing = _existing_unique(p_candidates, label="P")
    log_existing = _existing_unique(log_candidates, label="log")

    return OutputFiles(
        q=q_existing[0],
        p=p_existing[0] if p_existing else None,
        log=log_existing[0] if log_existing else None,
    )
