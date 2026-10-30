"""Read-only validator for a complete EXP03.1 real bundle and MLflow lineage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sat_dengue.experiments.exp03_1_reporting import (
    read_real_bundle,
    validate_real_mlflow,
)


def validate(path: Path, expected_bundle_id: str, tracking_root: str) -> dict[str, Any]:
    publication = read_real_bundle(path, expected_bundle_id)
    validate_real_mlflow(
        publication["bundle"], tracking_root, publication["manifest"]["bundle_id"]
    )
    return {
        "status": "verified",
        "bundle_id": publication["manifest"]["bundle_id"],
        "protocol_sha256": publication["bundle"]["protocol_sha256"],
        "cells": len(publication["bundle"]["cells"]),
        "parent_run_id": publication["bundle"]["mlflow_receipt"]["parent_run_id"],
        "child_runs": publication["bundle"]["mlflow_receipt"]["child_count"],
        "G5": publication["bundle"]["G5"],
        "champion": publication["bundle"]["champion"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--tracking-root", required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.bundle, args.bundle_id, args.tracking_root), sort_keys=True))


if __name__ == "__main__":
    main()
