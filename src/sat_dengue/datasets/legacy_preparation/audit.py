"""Read-only milestone evidence: validate products and compare scientific hashes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contract import PreparationConfig, PreparationError, read_json
from .pipeline import fingerprint, prepare_inputs


def main() -> None:
    """Validate notebook 03 products and an optional pre-task preservation baseline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    result = prepare_inputs(PreparationConfig(args.root))
    if args.baseline:
        baseline = read_json(args.baseline)
        for relative, expected in baseline.items():
            path = PreparationConfig(args.root).resolve(relative)
            if fingerprint(path) != expected:
                raise PreparationError(f"Scientific input changed: {relative}")
        result.report["preservation_files_verified"] = len(baseline)
    print(json.dumps(result.report, indent=2))
