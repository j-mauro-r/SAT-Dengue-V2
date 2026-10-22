"""Execute notebook08 from a fresh kernel or verify it without fitting."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.model_evaluation.contract import resolve_root
from scripts.model_training.notebook_execution import execute_notebook
from scripts.model_training.persistence import json_bytes, publish_artifacts, verify_artifacts
from scripts.training_preparation.pipeline import fingerprint

from .pipeline import NOTEBOOK, build_assessment, code_fingerprints


def extract_summary(notebook: dict[str, Any]) -> dict[str, Any]:
    """Require successful sequential code-only execution and one exact summary."""
    cells = notebook["cells"]
    if not cells or any(c["cell_type"] != "code" for c in cells):
        raise ValueError("Expected code-only notebook")
    if [c.get("execution_count") for c in cells] != list(range(1, len(cells) + 1)):
        raise ValueError("Notebook must execute all cells sequentially")
    outputs = [o for c in cells for o in c.get("outputs", [])]
    if any(o["output_type"] == "error" for o in outputs):
        raise ValueError("Notebook contains execution errors")
    summaries = []
    for output in outputs:
        if output.get("output_type") == "stream":
            text = "".join(output.get("text", []))
            if '"model_assessment_run"' in text:
                summaries.append(json.loads(text)["model_assessment_run"])
    if len(summaries) != 1:
        raise ValueError("Exactly one machine-readable summary required")
    return summaries[0]


def main() -> None:
    """Run or verify notebook outputs and immutable receipt, never reserved results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--execute", action="store_true")
    modes.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    root = resolve_root(args.root)
    if args.execute:
        execute_notebook(
            root,
            notebook_path=NOTEBOOK,
            fingerprints=code_fingerprints,
            extract_summary=extract_summary,
        )
    summary = build_assessment(root, verify_only=True)
    notebook = json.loads((root / NOTEBOOK).read_text())
    if extract_summary(notebook) != summary:
        raise ValueError("Saved notebook outputs differ from current artifacts")
    receipt = {
        "schema": "notebook08-execution-v1",
        "mode": "fresh_kernel",
        "notebook": fingerprint(root / NOTEBOOK),
        "summary": summary,
        "manifest": fingerprint(root / summary["bundle"] / "manifest.json"),
    }
    payload = json_bytes(receipt)
    identity = hashlib.sha256(payload).hexdigest()
    base = root / "artifacts/model_assessment_notebook_executions"
    if args.execute:
        publish_artifacts(base, identity, {"receipt.json": payload})
    else:
        verify_artifacts(base / identity, {"receipt.json": payload})
    print(
        json_bytes(
            {
                "status": "PASS",
                "bundle": summary["bundle"],
                "receipt": str((base / identity).relative_to(root)),
                "reserved": "pending",
            }
        ).decode()
    )


if __name__ == "__main__":
    main()
