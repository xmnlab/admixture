"""Validation helpers for PLINK input and runner parameters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .exceptions import PlinkInputError


@dataclass(frozen=True)
class PlinkFiles:
    """Paths belonging to a binary PLINK dataset prefix."""

    prefix: Path
    bed: Path
    bim: Path
    fam: Path


def _normalise_plink_prefix(prefix: str | Path) -> Path:
    path = Path(prefix).expanduser()
    if path.suffix.lower() in {".bed", ".bim", ".fam"}:
        return path.with_suffix("")
    return path


def validate_plink_prefix(prefix: str | Path) -> PlinkFiles:
    """Validate a binary PLINK prefix and return its component files.

    Parameters
    ----------
    prefix
        PLINK file prefix, not normally including ``.bed``. Passing a path that
        ends in ``.bed``, ``.bim`` or ``.fam`` is normalized to the prefix.

    Raises
    ------
    PlinkInputError
        If any of the ``.bed``, ``.bim`` or ``.fam`` files are missing or empty.
    """
    normalised = _normalise_plink_prefix(prefix)
    files = PlinkFiles(
        prefix=normalised,
        bed=Path(f"{normalised}.bed"),
        bim=Path(f"{normalised}.bim"),
        fam=Path(f"{normalised}.fam"),
    )

    missing = [path for path in (files.bed, files.bim, files.fam) if not path.exists()]
    if missing:
        expected = "\n".join(
            f"  - {path}" for path in (files.bed, files.bim, files.fam)
        )
        missing_text = "\n".join(f"  - {path}" for path in missing)
        raise PlinkInputError(
            "Missing binary PLINK input file(s).\n\n"
            "Pass the PLINK prefix, for example bfile='data/example' for:\n"
            f"{expected}\n\n"
            f"Missing file(s):\n{missing_text}"
        )

    empty = [
        path for path in (files.bed, files.bim, files.fam) if path.stat().st_size == 0
    ]
    if empty:
        empty_text = "\n".join(f"  - {path}" for path in empty)
        raise PlinkInputError(
            "Binary PLINK input file(s) are empty. OpenADMIXTURE.jl needs a "
            "valid .bed/.bim/.fam trio.\n\n"
            f"Empty file(s):\n{empty_text}"
        )

    return files


def validate_k(k: int) -> int:
    """Validate the number of ancestral populations."""
    if isinstance(k, bool) or not isinstance(k, int):
        raise ValueError("k must be an integer greater than or equal to 2.")
    if k < 2:
        raise ValueError("k must be greater than or equal to 2.")
    return k


def validate_threads(threads: int | None) -> int | None:
    """Validate the requested Julia thread count."""
    if threads is None:
        return None
    if isinstance(threads, bool) or not isinstance(threads, int):
        raise ValueError(
            "threads must be None or an integer greater than or equal to 1."
        )
    if threads < 1:
        raise ValueError("threads must be greater than or equal to 1.")
    return threads


def validate_seed(seed: int | None) -> int | None:
    """Validate a random seed."""
    if seed is None:
        return None
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be None or an integer greater than or equal to 0.")
    if seed < 0:
        raise ValueError("seed must be greater than or equal to 0.")
    return seed


def ensure_output_parent(path: str | Path) -> Path:
    """Ensure the parent directory for an output prefix exists."""
    output_prefix = Path(path).expanduser()
    parent = output_prefix.parent
    if parent != Path(""):
        parent.mkdir(parents=True, exist_ok=True)
    return output_prefix
