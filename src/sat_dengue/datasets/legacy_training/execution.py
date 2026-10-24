"""CLI entrypoint for Stage 4 reference execution and verification."""

from __future__ import annotations

import argparse
from pathlib import Path

from .contract import ModelTrainingConfig, resolve_root
from .persistence import json_bytes
from .pipeline import build_model_training, run_summary


def main() -> None:
    """Run Stage 4 references or verify an existing immutable bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    config = ModelTrainingConfig(resolve_root(args.root))
    result = build_model_training(config, verify_only=args.verify)
    print(json_bytes({"model_training_run": run_summary(result, config.root)}).decode())
