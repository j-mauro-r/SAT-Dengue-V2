"""Compatibility CLI for the read-only migrated frozen assessment."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    """Map retained execution/verification entrypoints onto guarded Kedro replay."""
    parser = argparse.ArgumentParser(description="Replay consumed frozen evidence without fitting")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--scientific", action="store_true")
    args = parser.parse_args()
    if args.scientific:
        raise PermissionError("2025 is consumed; scientific fitting/tuning/selection is forbidden")
    from kedro.framework.cli import main as kedro_main

    previous = sys.argv
    try:
        sys.argv = [
            "kedro",
            "run",
            "--pipeline=evaluation_replay",
            "--params=profile=evaluation_replay",
        ]
        kedro_main()
    finally:
        sys.argv = previous
