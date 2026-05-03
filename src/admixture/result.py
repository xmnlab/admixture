"""
title: Result containers returned by :class:`admixture.OpenAdmixtureRunner`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class OpenAdmixtureResult:
    """
    title: Parsed result and execution metadata from an OpenADMIXTURE run.
    attributes:
      q:
        type: pd.DataFrame
      p:
        type: pd.DataFrame | None
      q_path:
        type: Path
      p_path:
        type: Path | None
      log_path:
        type: Path | None
      out_prefix:
        type: Path
      k:
        type: int
      command:
        type: tuple[str, Ellipsis]
      returncode:
        type: int
      stdout:
        type: str
      stderr:
        type: str
      metadata:
        type: dict[str, Any]
    """

    q: pd.DataFrame
    p: pd.DataFrame | None
    q_path: Path
    p_path: Path | None
    log_path: Path | None
    out_prefix: Path
    k: int
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    metadata: dict[str, Any]

    def to_csv(self, prefix: str | Path) -> None:
        """
        title: Write parsed Q and P tables to CSV files using ``prefix``.
        parameters:
          prefix:
            type: str | Path
        """
        output_prefix = Path(prefix)
        output_prefix.parent.mkdir(parents=True, exist_ok=True)
        self.q.to_csv(Path(f"{output_prefix}.Q.csv"))
        if self.p is not None:
            self.p.to_csv(Path(f"{output_prefix}.P.csv"), index=False)

    def summary(self) -> dict[str, Any]:
        """
        title: Return a compact summary of the result.
        returns:
          type: dict[str, Any]
        """
        return {
            "k": self.k,
            "n_individuals": int(self.q.shape[0]),
            "n_ancestries": int(self.q.shape[1]),
            "has_p": self.p is not None,
            "q_path": str(self.q_path),
            "p_path": str(self.p_path) if self.p_path is not None else None,
            "log_path": str(self.log_path) if self.log_path is not None else None,
            "returncode": self.returncode,
        }
