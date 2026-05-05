"""
title: Command line entry points for admixture.
"""

from __future__ import annotations

import argparse
import sys

from collections.abc import Callable, Sequence
from typing import cast

from .exceptions import OpenAdmixtureError
from .setup import setup

Command = Callable[[argparse.Namespace], int]


def _add_setup_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """
    title: Add the OpenADMIXTURE.jl setup subcommand parser.
    parameters:
      subparsers:
        type: argparse._SubParsersAction[argparse.ArgumentParser]
    """
    parser = subparsers.add_parser(
        "setup",
        help="instantiate the packaged OpenADMIXTURE.jl Julia project",
        description="Instantiate the packaged OpenADMIXTURE.jl Julia project.",
    )
    parser.add_argument(
        "--julia",
        default="julia",
        help="Julia executable name or path.",
    )
    parser.set_defaults(command=_run_setup_command)


def _build_parser() -> argparse.ArgumentParser:
    """
    title: Build the top-level admixture command parser.
    returns:
      type: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="admixture",
        description="Command line helpers for the Python OpenADMIXTURE.jl wrapper.",
    )
    subparsers = parser.add_subparsers(dest="subcommand")
    _add_setup_parser(subparsers)
    return parser


def _run_setup_command(args: argparse.Namespace) -> int:
    """
    title: Run the OpenADMIXTURE.jl setup command.
    parameters:
      args:
        type: argparse.Namespace
    returns:
      type: int
    """
    try:
        project_dir = setup(julia=args.julia)
    except OpenAdmixtureError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(f"Packaged OpenADMIXTURE.jl Julia project instantiated: {project_dir}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """
    title: Execute the top-level admixture command.
    parameters:
      argv:
        type: Sequence[str] | None
    returns:
      type: int
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    command = getattr(args, "command", None)
    if command is None:
        parser.print_help()
        return 2
    return cast(Command, command)(args)


if __name__ == "__main__":
    raise SystemExit(main())
