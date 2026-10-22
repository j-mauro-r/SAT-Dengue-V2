"""Execute notebook07 in a fresh kernel and verify saved Stage 5 outputs."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import version
from pathlib import Path
from typing import Any

from scripts.model_training.notebook_execution import execute_notebook
from scripts.model_training.persistence import json_bytes, publish_artifacts, verify_artifacts
from scripts.training_preparation.pipeline import fingerprint

from .contract import (
    CONTRACT_PATH,
    ModelEvaluationConfig,
    ModelEvaluationError,
    read_json,
    resolve_root,
)
from .pipeline import NOTEBOOK_PATH, build_model_evaluation, code_fingerprints, run_summary


def _json_load_summary(text: str) -> dict[str, Any]:
    """Parse the notebook machine-readable summary payload."""
    import json

    return json.loads(text)["model_evaluation_run"]


def extract_saved_summary(notebook: dict[str, Any]) -> dict[str, Any]:
    """Require successful sequential code execution and extract Stage 5 summary."""
    cells = notebook["cells"]
    if (
        not cells
        or any(cell["cell_type"] != "code" for cell in cells)
        or [cell.get("execution_count") for cell in cells] != list(range(1, len(cells) + 1))
        or any(
            output.get("output_type") == "error"
            for cell in cells
            for output in cell.get("outputs", [])
        )
    ):
        raise ModelEvaluationError("Notebook is not a successful sequential code-only execution")

    summary_cells = [
        cell for cell in cells if "model_evaluation_run" in "".join(cell.get("source", []))
    ]
    if len(summary_cells) != 1:
        summary_cells = [
            cell
            for cell in cells
            if any(
                output.get("output_type") == "stream"
                and "model_evaluation_run" in "".join(output.get("text", []))
                for output in cell.get("outputs", [])
            )
        ]
    if len(summary_cells) != 1:
        raise ModelEvaluationError("Expected one summary cell containing model_evaluation_run")

    text = "".join(
        "".join(output["text"])
        for output in summary_cells[0].get("outputs", [])
        if output.get("output_type") == "stream" and output.get("name") == "stdout"
    )
    try:
        return _json_load_summary(text)
    except (KeyError, ValueError) as exc:
        raise ModelEvaluationError(
            "Notebook has no valid saved model_evaluation_run summary"
        ) from exc


def verify_execution(
    config: ModelEvaluationConfig,
    *,
    publish_receipt: bool = False,
) -> dict[str, Any]:
    """Verify saved notebook07 output identity against current Stage 5 artifacts."""
    result = build_model_evaluation(config, verify_only=True)
    notebook = read_json(config.resolve(NOTEBOOK_PATH))
    displayed = extract_saved_summary(notebook)
    expected = run_summary(result, config.root)
    if displayed != expected:
        raise ModelEvaluationError("Saved notebook outputs do not describe current artifacts")

    contract = read_json(config.resolve(config.contract_path))
    receipt = {
        "schema": "notebook07-execution-v1",
        "mode": "fresh_kernel",
        "notebook_bytes": fingerprint(config.resolve(NOTEBOOK_PATH)),
        "notebook_code": code_fingerprints(config.root)[str(NOTEBOOK_PATH)],
        "model_evaluation_manifest": fingerprint(result.bundle / "manifest.json"),
        "summary": expected,
        "executed_cells": len(notebook["cells"]),
        "kernel_packages": {name: version(name) for name in ("nbclient", "nbformat", "ipykernel")},
    }
    payload = json_bytes(receipt)
    identity = hashlib.sha256(payload).hexdigest()
    base = config.resolve(contract["artifacts"]["notebook_receipts_dir"])
    payloads = {"receipt.json": payload}
    if publish_receipt:
        publish_artifacts(base, identity, payloads)
    else:
        verify_artifacts(base / identity, payloads)
    return receipt


def main() -> None:
    """Execute and verify notebook07, or verify saved state only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    root = resolve_root(args.root)
    config = ModelEvaluationConfig(root=root, contract_path=args.contract)
    if args.execute:
        execute_notebook(
            root,
            notebook_path=NOTEBOOK_PATH,
            fingerprints=code_fingerprints,
            extract_summary=extract_saved_summary,
        )
    receipt = verify_execution(config, publish_receipt=args.execute)
    print(
        json_bytes(
            {
                "status": "PASS",
                "executed_cells": receipt["executed_cells"],
                "model_evaluation_bundle": receipt["summary"]["model_evaluation_bundle"],
                "receipt_mode": receipt["mode"],
            }
        ).decode()
    )


if __name__ == "__main__":
    main()
