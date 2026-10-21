"""Fresh-kernel notebook08 execution with an explicit, separately authorized science mode."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from scripts.model_training.notebook_execution import execute_notebook
from scripts.model_training.persistence import json_bytes, publish_artifacts, verify_artifacts
from scripts.training_preparation.development import resolve_root
from scripts.training_preparation.pipeline import fingerprint

from .pipeline import readiness, run_final
from .protocol import NOTEBOOK, code_fingerprints, require_authorization


def extract_summary(notebook: dict[str, Any]) -> dict[str, Any]:
    """Extract exactly one successful sequential code-only notebook result.

    Args:
        notebook: Notebook document with saved execution outputs.

    Returns:
        Machine-readable readiness or scientific-run summary.
    """
    cells = notebook["cells"]
    if (
        not cells
        or any(c["cell_type"] != "code" for c in cells)
        or [c.get("execution_count") for c in cells] != list(range(1, len(cells) + 1))
    ):
        raise ValueError("Expected successful sequential code-only notebook")
    found = []
    for cell in cells:
        for output in cell.get("outputs", []):
            if output["output_type"] == "error":
                raise ValueError("Notebook contains errors")
            if output["output_type"] == "stream":
                text = "".join(output.get("text", []))
                if '"final_evaluation_run"' in text:
                    found.append(json.loads(text)["final_evaluation_run"])
    if len(found) != 1:
        raise ValueError("Exactly one notebook summary required")
    return found[0]


def main() -> None:
    """Execute readiness by default; scientific mode always requires recorded human consent."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--execute", action="store_true")
    modes.add_argument("--verify", action="store_true")
    parser.add_argument(
        "--scientific",
        action="store_true",
        help="Explicit final science request; never substitutes for human authorization",
    )
    args = parser.parse_args()
    root = resolve_root(args.root)
    if args.scientific:
        require_authorization(root)
    if args.execute:
        os.environ["SAT_DENGUE_FINAL_MODE"] = "execute" if args.scientific else "readiness"
        execute_notebook(
            root,
            notebook_path=NOTEBOOK,
            fingerprints=code_fingerprints,
            extract_summary=extract_summary,
        )
    saved = extract_summary(json.loads((root / NOTEBOOK).read_text()))
    expected = readiness(root)
    if saved["readiness"] != expected:
        raise ValueError("Saved notebook readiness/dependencies are stale")
    if saved["mode"] != "readiness":
        verified = run_final(root, verify_only=True)
        if saved["scientific"]["summary"] != verified["summary"]:
            raise ValueError("Saved final results do not reproduce current artifacts")
    elif args.scientific:
        raise ValueError("Notebook contains readiness only; scientific execution not evidenced")
    receipt = dict(
        schema="notebook08-final-route-v1",
        notebook=fingerprint(root / NOTEBOOK),
        saved=saved,
        kernel="fresh",
    )
    payload = json_bytes(receipt)
    identity = hashlib.sha256(payload).hexdigest()
    base = root / "artifacts/model_final_notebook_executions"
    if args.execute:
        publish_artifacts(base, identity, {"receipt.json": payload})
    else:
        verify_artifacts(base / identity, {"receipt.json": payload})
    print(
        json_bytes(
            dict(
                status="PASS",
                mode=saved["mode"],
                receipt=str((base / identity).relative_to(root)),
                G5="NOT_APPROVED",
            )
        ).decode()
    )


if __name__ == "__main__":
    main()
