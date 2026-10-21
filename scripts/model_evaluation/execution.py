"""CLI entrypoint for Stage 5 calibration and threshold execution/verification."""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts.model_training.persistence import json_bytes

from .contract import CONTRACT_PATH, ModelEvaluationConfig, resolve_root
from .pipeline import build_model_evaluation, run_summary


def main() -> None:
    """Execute or verify Stage 5 artifacts with immutable identities."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    root = resolve_root(args.root)
    config = ModelEvaluationConfig(root=root, contract_path=args.contract)
    result = build_model_evaluation(config, verify_only=args.verify)
    print(json_bytes({"model_evaluation_run": run_summary(result, root)}).decode())


if __name__ == "__main__":
    main()
