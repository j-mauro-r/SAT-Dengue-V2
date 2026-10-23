"""Execute notebook 05 in a fresh kernel and verify saved Stage 4 outputs."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from collections.abc import Callable
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
from typing import Any

from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint

from .contract import ModelTrainingConfig, ModelTrainingError, read_json, resolve_root
from .persistence import json_bytes, publish_artifacts, verify_artifacts
from .pipeline import NOTEBOOK_PATH, build_model_training, code_fingerprints, run_summary


def json_load_summary(text: str) -> dict[str, Any]:
    """Parse the notebook machine-readable summary payload."""
    import json

    return json.loads(text)["model_training_run"]


def extract_saved_summary(notebook: dict[str, Any]) -> dict[str, Any]:
    """Require full successful execution and extract model_training_run summary."""
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
        raise ModelTrainingError("Notebook is not a successful sequential code-only execution")
    summary_cells = [cell for cell in cells if cell.get("id") == "run-summary"]
    if len(summary_cells) != 1:
        summary_cells = [
            cell for cell in cells if "model_training_run" in "".join(cell.get("source", []))
        ]
    if len(summary_cells) != 1:
        summary_cells = [
            cell
            for cell in cells
            if any(
                output.get("output_type") == "stream"
                and "model_training_run" in "".join(output.get("text", []))
                for output in cell.get("outputs", [])
            )
        ]
    if len(summary_cells) != 1:
        raise ModelTrainingError("Expected one summary cell containing model_training_run")
    text = "".join(
        "".join(output["text"])
        for output in summary_cells[0].get("outputs", [])
        if output.get("output_type") == "stream" and output.get("name") == "stdout"
    )
    try:
        return json_load_summary(text)
    except (KeyError, ValueError) as exc:
        raise ModelTrainingError("Notebook has no valid saved model_training_run summary") from exc


def _execution_environment(root: Path) -> dict[str, str]:
    """Keep Jupyter/IPython runtime writes inside the repository tmp tree."""
    env = dict(os.environ)
    for key, suffix in (
        ("IPYTHONDIR", "ipython"),
        ("JUPYTER_CONFIG_DIR", "config"),
        ("JUPYTER_DATA_DIR", "data"),
        ("JUPYTER_RUNTIME_DIR", "runtime"),
    ):
        path = root / "tmp/notebook05_kernel" / suffix
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
        os.environ[key] = str(path)
    return env


def execute_notebook(
    root: Path,
    *,
    notebook_path: Path = NOTEBOOK_PATH,
    fingerprints: Callable[[Path], dict[str, Any]] = code_fingerprints,
    extract_summary: Callable[[dict[str, Any]], dict[str, Any]] = extract_saved_summary,
) -> None:
    """Run every notebook cell in a fresh kernel and save outputs atomically."""
    env = _execution_environment(root)
    nbformat = import_module("nbformat")
    KernelManager = import_module("jupyter_client").KernelManager
    NotebookClient = import_module("nbclient").NotebookClient

    path = root / notebook_path
    before = fingerprints(root)
    notebook = nbformat.read(path, as_version=4)
    km = KernelManager(
        kernel_name="python3",
        transport="ipc",
        ip=str(root / "tmp/n5"),
        connection_file=str(root / "tmp/notebook05_kernel/runtime/kernel.json"),
    )
    if km.kernel_spec is None:
        raise ModelTrainingError("Python kernel specification is unavailable")
    km.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    client = NotebookClient(
        notebook,
        km=km,
        timeout=900,
        record_timing=False,
        resources={"metadata": {"path": str(root)}},
    )
    try:
        client.execute(cwd=str(root), env=env)
    finally:
        if km.has_kernel:
            km.shutdown_kernel(now=True)
        km.cleanup_resources()
    extract_summary(notebook)
    if fingerprints(root) != before:
        raise ModelTrainingError("Code changed during fresh-kernel execution")
    fd, temporary = tempfile.mkstemp(prefix=".notebook05-", suffix=".ipynb", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            nbformat.write(notebook, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def verify_execution(
    config: ModelTrainingConfig,
    *,
    publish_receipt: bool = False,
) -> dict[str, Any]:
    """Verify saved notebook output identity against current Stage 4 artifacts."""
    result = build_model_training(config, verify_only=True)
    notebook = read_json(config.resolve(NOTEBOOK_PATH))
    displayed = extract_saved_summary(notebook)
    expected = run_summary(result, config.root)
    if displayed != expected:
        raise ModelTrainingError("Saved notebook outputs do not describe current artifacts")

    contract = read_json(config.resolve(config.contract_path))
    receipt = {
        "schema": "notebook05-execution-v1",
        "mode": "fresh_kernel",
        "notebook_bytes": fingerprint(config.resolve(NOTEBOOK_PATH)),
        "notebook_code": code_fingerprints(config.root)[str(NOTEBOOK_PATH)],
        "model_training_manifest": fingerprint(result.bundle / "manifest.json"),
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
    """Execute and verify notebook 05, or verify saved state only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    config = ModelTrainingConfig(resolve_root(args.root))
    if args.execute:
        execute_notebook(config.root)
    receipt = verify_execution(config, publish_receipt=args.execute)
    print(
        json_bytes(
            {
                "status": "PASS",
                "executed_cells": receipt["executed_cells"],
                "model_training_bundle": receipt["summary"]["model_training_bundle"],
                "receipt_mode": receipt["mode"],
            }
        ).decode()
    )
