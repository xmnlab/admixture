"""
title: Command line entry points for admixture.
"""

from __future__ import annotations

import argparse
import sys

from collections.abc import Sequence

from .exceptions import OpenAdmixtureError
from .setup import setup


def _build_setup_parser() -> argparse.ArgumentParser:
    """
    title: Build the OpenADMIXTURE.jl setup command parser.
    returns:
      type: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="admixture-setup",
        description="Instantiate the packaged OpenADMIXTURE.jl Julia project.",
    )
    parser.add_argument(
        "--julia",
        default="julia",
        help="Julia executable name or path.",
    )
    return parser


def setup_main(argv: Sequence[str] | None = None) -> int:
    """
    title: Run the OpenADMIXTURE.jl setup command.
    parameters:
      argv:
        type: Sequence[str] | None
    returns:
      type: int
    """
    parser = _build_setup_parser()
    args = parser.parse_args(argv)
    try:
        project_dir = setup(julia=args.julia)
    except OpenAdmixtureError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(f"Packaged OpenADMIXTURE.jl Julia project instantiated: {project_dir}")
    return 0


def main() -> None:
    """
    title: Execute the setup command as a Python module.
    """
    raise SystemExit(setup_main())


if __name__ == "__main__":
    main()
