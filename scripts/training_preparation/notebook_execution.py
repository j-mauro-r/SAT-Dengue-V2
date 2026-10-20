"""Execute notebook 04 in a fresh local kernel and verify saved outputs against artifacts."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
from typing import Any

from .contract import PreparationConfig, PreparationError, read_json
from .development import code_fingerprints, resolve_root
from .persistence import json_bytes, publish_bundle, verify_bundle
from .pipeline import fingerprint
from .temporal import build_temporal, run_summary

NOTEBOOK = "notebooks/04_training_preparation_pipeline.ipynb"


def extract_saved_summary(notebook: dict[str, Any]) -> dict[str, Any]:
    """Require a fully executed code-only notebook and extract its bounded JSON summary.

    Args:
        notebook: Saved notebook document.

    Returns:
        Displayed preparation_run summary, excluding any private source rows.

    Raises:
        PreparationError: If execution evidence is incomplete or contains an error.
    """
    cells = notebook["cells"]
    if (
        not cells
        or any(c["cell_type"] != "code" for c in cells)
        or [c.get("execution_count") for c in cells] != list(range(1, len(cells) + 1))
        or any(o["output_type"] == "error" for c in cells for o in c.get("outputs", []))
    ):
        raise PreparationError("Notebook is not a successful sequential code-only execution")
    summaries = [c for c in cells if c.get("id") == "run-summary"]
    if len(summaries) != 1:
        raise PreparationError("Expected one saved run-summary cell")
    text = "".join(
        "".join(o["text"])
        for o in summaries[0]["outputs"]
        if o["output_type"] == "stream" and o["name"] == "stdout"
    )
    try:
        return json_load_summary(text)
    except (ValueError, KeyError) as exc:
        raise PreparationError("Notebook has no valid saved preparation summary") from exc


def json_load_summary(text: str) -> dict[str, Any]:
    """Parse the sole machine-readable notebook summary.

    Args:
        text: Printed JSON document.

    Returns:
        Preparation run object.
    """
    import json

    return json.loads(text)["preparation_run"]


def _execution_environment(root: Path) -> dict[str, str]:
    """Keep kernel/config/runtime writes inside this repository.

    Args:
        root: Repository root.

    Returns:
        Kernel process environment with repository-local Jupyter/IPython directories.
    """
    env = dict(os.environ)
    for key, suffix in (
        ("IPYTHONDIR", "ipython"),
        ("JUPYTER_CONFIG_DIR", "config"),
        ("JUPYTER_DATA_DIR", "data"),
        ("JUPYTER_RUNTIME_DIR", "runtime"),
    ):
        path = root / "tmp/notebook04_kernel" / suffix
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
        os.environ[key] = str(path)
    return env


def execute_notebook(root: Path) -> None:
    """Run all code cells in a newly launched kernel, then atomically save outputs.

    Args:
        root: Repository root, also used as the kernel working directory.

    Raises:
        PreparationError: If code changes concurrently or execution is incomplete.
    """
    env = _execution_environment(root)
    nbformat = import_module("nbformat")
    KernelManager = import_module("jupyter_client").KernelManager
    NotebookClient = import_module("nbclient").NotebookClient

    path = root / NOTEBOOK
    before = code_fingerprints(root)
    notebook = nbformat.read(path, as_version=4)
    km = KernelManager(
        kernel_name="python3",
        transport="ipc",
        ip=str(root / "tmp/n4"),
        connection_file=str(root / "tmp/notebook04_kernel/runtime/kernel.json"),
    )
    if km.kernel_spec is None:
        raise PreparationError("Python kernel specification is unavailable")
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
    extract_saved_summary(notebook)
    if code_fingerprints(root) != before:
        raise PreparationError("Code changed during fresh-kernel execution")
    fd, temporary = tempfile.mkstemp(prefix=".notebook04-", suffix=".ipynb", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            nbformat.write(notebook, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def verify_execution(config: PreparationConfig, *, publish_receipt: bool = False) -> dict[str, Any]:
    """Bind saved notebook bytes/outputs to current recomputed artifact identities.

    Args:
        config: Repository preparation configuration.
        publish_receipt: Write a new immutable receipt after actual fresh-kernel execution.

    Returns:
        Execution receipt payload.

    Raises:
        PreparationError: If saved outputs or current artifacts/receipt disagree.
    """
    result = build_temporal(config, verify_only=True)
    notebook = read_json(config.resolve(NOTEBOOK))
    displayed = extract_saved_summary(notebook)
    expected = run_summary(result, config.root)
    if displayed != expected:
        raise PreparationError("Saved notebook outputs do not describe current artifacts")
    receipt = {
        "schema": "notebook04-execution-v1",
        "mode": "fresh_kernel",
        "notebook_bytes": fingerprint(config.resolve(NOTEBOOK)),
        "notebook_code": code_fingerprints(config.root)[NOTEBOOK],
        "temporal_manifest": fingerprint(result.bundle / "manifest.json"),
        "summary": expected,
        "executed_cells": len(notebook["cells"]),
        "kernel_packages": {n: version(n) for n in ("nbclient", "nbformat", "ipykernel")},
    }
    payload = json_bytes(receipt)
    identity = hashlib.sha256(payload).hexdigest()
    contract = read_json(config.resolve(config.contract_path))
    base = config.resolve(contract["temporal_preparation"]["notebook_receipts_dir"])
    if publish_receipt:
        publish_bundle(base, identity, {"receipt.json": payload})
    else:
        verify_bundle(base / identity, {"receipt.json": payload})
    return receipt


def main() -> None:
    """Execute and save a fresh-kernel run, or verify an existing execution receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    config = PreparationConfig(resolve_root(args.root))
    if args.execute:
        execute_notebook(config.root)
    receipt = verify_execution(config, publish_receipt=args.execute)
    print(
        json_bytes(
            {
                "status": "PASS",
                "executed_cells": receipt["executed_cells"],
                "temporal_bundle": receipt["summary"]["temporal_bundle"],
                "receipt_mode": receipt["mode"],
            }
        ).decode()
    )


if __name__ == "__main__":
    main()
