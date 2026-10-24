"""Fresh-kernel notebook06 execution and current candidate/receipt verification."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
from typing import Any

from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint

from .candidate_suite import build_candidate_suite
from .candidates import NOTEBOOK, candidate_code, candidate_summary
from .contract import ModelTrainingConfig, ModelTrainingError, read_json, resolve_root
from .notebook_execution import execute_notebook, extract_saved_summary
from .persistence import json_bytes, publish_artifacts, verify_artifacts


def verify_execution(
    config: ModelTrainingConfig, *, publish_receipt: bool = False
) -> dict[str, Any]:
    """Verify saved notebook output against current source, model inference and receipt.

    Args:
        config: Repository-scoped configuration.
        publish_receipt: Only true immediately following actual fresh-kernel execution.

    Returns:
        Reproducible receipt binding notebook bytes, models, runtime and displayed output.
    """
    result = build_candidate_suite(config, verify_only=True)
    nb = read_json(config.resolve(NOTEBOOK))
    summary = extract_saved_summary(nb)
    if summary != candidate_summary(result, config.root):
        raise ModelTrainingError("Saved notebook06 outputs are stale")
    receipt = dict(
        schema="notebook06-execution-v1",
        mode="fresh_kernel",
        notebook_bytes=fingerprint(config.resolve(NOTEBOOK)),
        manifest=fingerprint(result.bundle / "manifest.json"),
        summary=summary,
        executed_cells=len(nb["cells"]),
        kernel_packages={p: version(p) for p in ("nbclient", "nbformat", "ipykernel")},
    )
    data = json_bytes(receipt)
    identity = hashlib.sha256(data).hexdigest()
    base = config.resolve("artifacts/model_training/candidate_notebook_execution")
    if publish_receipt:
        publish_artifacts(base, identity, {"receipt.json": data})
    else:
        verify_artifacts(base / identity, {"receipt.json": data})
    return receipt


def main() -> None:
    """Execute code-only notebook06 or verify existing artifacts without model refitting."""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--execute", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    config = ModelTrainingConfig(resolve_root())
    if args.execute:
        execute_notebook(config.root, notebook_path=NOTEBOOK, fingerprints=candidate_code)
    receipt = verify_execution(config, publish_receipt=args.execute)
    print(json_bytes(dict(executed_cells=receipt["executed_cells"], **receipt["summary"])).decode())
