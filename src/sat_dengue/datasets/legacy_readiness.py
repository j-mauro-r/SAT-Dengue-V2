"""Validate Stage 2 training-readiness invariants and artifact preservation.

This script provides two bounded capabilities used by PLAN_017:

1. Freeze a reproducible baseline receipt (JSON) with source fingerprints,
   lineage counts, panel keys/schema and Y/P75 signatures.
2. Validate a regenerated state against that baseline while allowing only the
   additive endemic-channel fields introduced by this plan.

The script does not train models and does not mutate source datasets.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.readiness import (
    ALLOWED_ADDITIVE_PANEL_COLUMNS as ALLOWED_ADDITIVE_PANEL_COLUMNS,
)
from sat_dengue.data.readiness import (
    CANAL_ZONE_VALUES as CANAL_ZONE_VALUES,
)
from sat_dengue.data.readiness import (
    INPUT_FINGERPRINT_RELATIVE_PATHS as INPUT_FINGERPRINT_RELATIVE_PATHS,
)
from sat_dengue.data.readiness import (
    NOTEBOOK_ANALYSIS_MANIFEST as NOTEBOOK_ANALYSIS_MANIFEST,
)
from sat_dengue.data.readiness import (
    NOTEBOOK_FINGERPRINT_MODULE_PATHS as NOTEBOOK_FINGERPRINT_MODULE_PATHS,
)
from sat_dengue.data.readiness import (
    NOTEBOOK_PATH_RELATIVE as NOTEBOOK_PATH_RELATIVE,
)
from sat_dengue.data.readiness import (
    NOTEBOOK_REQUIRED_OUTPUT_SECTION_MARKERS as NOTEBOOK_REQUIRED_OUTPUT_SECTION_MARKERS,
)
from sat_dengue.data.readiness import (
    RESERVED_BLOCK_START as RESERVED_BLOCK_START,
)
from sat_dengue.data.readiness import (
    TEMPORAL_WINDOW_TRAIN_ENDPOINTS as TEMPORAL_WINDOW_TRAIN_ENDPOINTS,
)
from sat_dengue.data.readiness import (
    ValidationMessage as ValidationMessage,
)
from sat_dengue.data.readiness import (
    add_months as add_months,
)
from sat_dengue.data.readiness import (
    build_model_eligibility_policy as build_model_eligibility_policy,
)
from sat_dengue.data.readiness import (
    collect_manifest_paths as collect_manifest_paths,
)
from sat_dengue.data.readiness import (
    compute_edge_contribution as compute_edge_contribution,
)
from sat_dengue.data.readiness import (
    extract_development_target_bounds as extract_development_target_bounds,
)
from sat_dengue.data.readiness import (
    independent_classify_endemic_zone as independent_classify_endemic_zone,
)
from sat_dengue.data.readiness import (
    independent_history_periods as independent_history_periods,
)
from sat_dengue.data.readiness import (
    independent_percentile_type7 as independent_percentile_type7,
)
from sat_dengue.data.readiness import (
    independent_select_supervised_rows as independent_select_supervised_rows,
)
from sat_dengue.data.readiness import (
    panel_y_p75_signature as panel_y_p75_signature,
)
from sat_dengue.data.readiness import (
    parse_expected_byte_count as parse_expected_byte_count,
)
from sat_dengue.data.readiness import (
    period_to_yyyymm as period_to_yyyymm,
)
from sat_dengue.data.readiness import (
    recompute_channel_independently as recompute_channel_independently,
)
from sat_dengue.data.readiness import (
    statuses_summary as statuses_summary,
)


def utc_now_iso() -> str:
    """Return UTC timestamp in ISO-8601 format."""

    return datetime.now(UTC).isoformat()


def sha256_file(path: Path) -> str:
    """Compute SHA-256 digest for a file.

    Args:
        path: File path.

    Returns:
        Hex digest.
    """

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_hash_record(path: Path) -> dict[str, Any]:
    """Build a hash/size record for a file.

    Args:
        path: File path.

    Returns:
        Dictionary with sha256 and bytes.
    """

    return {
        "sha256": sha256_file(path),
        "bytes": int(path.stat().st_size),
    }


def recompute_input_fingerprints(root: Path) -> dict[str, dict[str, Any]]:
    """Recompute canonical input fingerprints from current files.

    Args:
        root: Repository root.

    Returns:
        Mapping of relative input path to fingerprint record.
    """

    fingerprints: dict[str, dict[str, Any]] = {}
    for relative_path in INPUT_FINGERPRINT_RELATIVE_PATHS:
        absolute_path = root / relative_path
        if not absolute_path.exists():
            raise RuntimeError(f"Required input file not found: {relative_path}")
        fingerprints[relative_path] = file_hash_record(absolute_path)
    return fingerprints


def resolve_repo_root(start: Path | None = None) -> Path:
    """Resolve repository root from current path or an anchor.

    Args:
        start: Optional anchor path.

    Returns:
        Resolved repository root.

    Raises:
        RuntimeError: If root cannot be resolved.
    """

    anchor = (start or Path(__file__).resolve()).resolve()
    for candidate in [anchor, *anchor.parents]:
        if (candidate / "AGENTS.md").exists() and (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("Unable to resolve repository root")


def load_visual_assets_module(root: Path) -> Any:
    """Load stage2 notebook visual-assets module from tracked script path.

    Args:
        root: Repository root.

    Returns:
        Loaded module object.

    Raises:
        RuntimeError: If module cannot be loaded.
    """

    module_path = root / "scripts/stage2_notebook_visual_assets.py"
    spec = importlib.util.spec_from_file_location("stage2_visual_assets", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load stage2_notebook_visual_assets.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_git(root: Path, *args: str) -> str:
    """Run a git command and return trimmed stdout.

    Args:
        root: Repository root.
        args: Git command arguments.

    Returns:
        Command stdout.

    Raises:
        RuntimeError: If git exits non-zero.
    """

    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        error_detail = completed.stderr.strip()
        raise RuntimeError(
            f"git {' '.join(args)} failed with code {completed.returncode}: {error_detail}"
        )
    return completed.stdout.strip()


def read_notification_year_metadata(consolidated_path: Path) -> dict[str, Any]:
    """Read notification-year metadata from consolidated rows.

    Args:
        consolidated_path: Consolidated CSV path.

    Returns:
        Metadata dictionary with supported notification-year range.
    """

    years = pd.read_csv(
        consolidated_path,
        usecols=["ANO"],
        dtype=str,
        keep_default_na=False,
    )["ANO"].str.strip()

    parsed = pd.to_numeric(years, errors="coerce").dropna().astype(int)
    if parsed.empty:
        return {
            "source": "consolidated.ANO",
            "min_year": None,
            "max_year": None,
            "unique_years": [],
            "count_rows_with_year": 0,
        }

    unique_years = sorted(parsed.unique().tolist())
    return {
        "source": "consolidated.ANO",
        "min_year": int(parsed.min()),
        "max_year": int(parsed.max()),
        "unique_years": unique_years,
        "count_rows_with_year": int(parsed.shape[0]),
    }


def capture_snapshot(root: Path) -> dict[str, Any]:
    """Capture current preservation and readiness snapshot.

    Args:
        root: Repository root.

    Returns:
        Snapshot dictionary.
    """

    manifest_path = (
        root / "data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    panel_path = root / manifest["outputs"]["panel_mensual_dengue_clima"]["path"]
    consolidated_path = root / manifest["outputs"]["dengue_y_dengue_grave"]["path"]

    panel = pd.read_csv(panel_path)
    panel["municipality_code"] = panel["municipality_code"].astype(str).str.zfill(5)
    panel["year_month"] = panel["year_month"].astype(str).map(period_to_yyyymm)

    notification_years = read_notification_year_metadata(consolidated_path)
    if notification_years["min_year"] is None or notification_years["max_year"] is None:
        raise RuntimeError("Unable to derive notification year metadata from consolidated output")

    policy = build_model_eligibility_policy(
        int(notification_years["min_year"]),
        int(notification_years["max_year"]),
    )
    backed = policy["source_coverage_backed_by_notification_year"]

    recomputed_inputs = recompute_input_fingerprints(root)

    baseline_snapshot = {
        "captured_utc": utc_now_iso(),
        "git": {
            "branch": run_git(root, "branch", "--show-current"),
            "revision": run_git(root, "rev-parse", "HEAD"),
            "dirty_paths": run_git(root, "status", "--short"),
        },
        "inputs": {
            "fingerprints": recomputed_inputs,
            "source_rows": manifest["reconciliation"]["source_rows"],
            "manifest_input_fingerprints_before": manifest.get("input_fingerprints_before", {}),
            "manifest_input_fingerprints_after": manifest.get("input_fingerprints_after", {}),
            "raw_lineage_rule": (
                "Preserve original source rows and lineage without rewriting sources."
            ),
        },
        "coverage": {
            "manifest": manifest["coverage"],
            "notification_year_metadata": notification_years,
            "edge_contribution_outside_backed_interval": compute_edge_contribution(
                panel,
                backed_start=str(backed["start"]),
                backed_end=str(backed["end"]),
            ),
            "model_eligibility_policy": policy,
        },
        "panel": {
            "path": str(panel_path.relative_to(root)),
            "rows": int(len(panel)),
            "columns": panel.columns.tolist(),
            "column_count": int(len(panel.columns)),
            "duplicate_keys": int(panel.duplicated(["municipality_code", "year_month"]).sum()),
            "y_p75_signature_sha256": panel_y_p75_signature(panel),
            "y_status_counts": {
                "t1": {
                    str(key): int(value)
                    for key, value in panel["y_status_t1"].value_counts(dropna=False).items()
                },
                "t2": {
                    str(key): int(value)
                    for key, value in panel["y_status_t2"].value_counts(dropna=False).items()
                },
            },
        },
        "output_hashes": {
            "consolidated_sha256": sha256_file(consolidated_path),
            "panel_sha256": sha256_file(panel_path),
            "traceability_sha256": sha256_file(
                root / manifest["outputs"]["y_label_history_traceability"]["path"]
            ),
            "channel_traceability_sha256": sha256_file(
                root / manifest["outputs"]["current_endemic_channel_traceability"]["path"]
            ),
            "execution_manifest_sha256": sha256_file(manifest_path),
        },
        "limitations": {
            "retrospective_only": (
                "Temporal ordering on consolidated retrospective data does not certify historical "
                "operational availability snapshots."
            ),
        },
    }

    return baseline_snapshot


def compare_snapshot(
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> list[ValidationMessage]:
    """Compare current snapshot against baseline invariants.

    Args:
        baseline: Stored baseline snapshot.
        current: Current snapshot.

    Returns:
        Validation messages.
    """

    messages: list[ValidationMessage] = []

    baseline_fp = baseline["inputs"]["fingerprints"]
    current_fp = current["inputs"]["fingerprints"]
    if baseline_fp == current_fp:
        messages.append(
            ValidationMessage(
                check="input_fingerprints",
                status="PASS",
                detail="Source/input fingerprints unchanged.",
            )
        )
    else:
        messages.append(
            ValidationMessage(
                check="input_fingerprints",
                status="FAIL",
                detail="Source/input fingerprints changed.",
            )
        )

    manifest_before = current["inputs"].get("manifest_input_fingerprints_before", {})
    manifest_after = current["inputs"].get("manifest_input_fingerprints_after", {})
    if manifest_before == current_fp and manifest_after == current_fp:
        messages.append(
            ValidationMessage(
                check="manifest_input_fingerprint_alignment",
                status="PASS",
                detail="Execution manifest input fingerprints match recomputed current inputs.",
            )
        )
    else:
        messages.append(
            ValidationMessage(
                check="manifest_input_fingerprint_alignment",
                status="FAIL",
                detail=(
                    "Execution manifest input fingerprints do not match recomputed current inputs."
                ),
            )
        )

    if baseline["inputs"]["source_rows"] == current["inputs"]["source_rows"]:
        messages.append(
            ValidationMessage(
                check="source_lineage_counts",
                status="PASS",
                detail="Source row lineage totals unchanged.",
            )
        )
    else:
        messages.append(
            ValidationMessage(
                check="source_lineage_counts",
                status="FAIL",
                detail="Source row lineage totals changed.",
            )
        )

    if baseline["panel"]["rows"] == current["panel"]["rows"]:
        messages.append(
            ValidationMessage(
                check="panel_row_count",
                status="PASS",
                detail=f"Panel row count preserved ({current['panel']['rows']}).",
            )
        )
    else:
        messages.append(
            ValidationMessage(
                check="panel_row_count",
                status="FAIL",
                detail=(
                    "Panel row count changed "
                    f"({baseline['panel']['rows']} -> {current['panel']['rows']})."
                ),
            )
        )

    if int(current["panel"]["duplicate_keys"]) == 0:
        messages.append(
            ValidationMessage(
                check="panel_key_uniqueness",
                status="PASS",
                detail="No duplicate municipality-month keys.",
            )
        )
    else:
        messages.append(
            ValidationMessage(
                check="panel_key_uniqueness",
                status="FAIL",
                detail="Duplicate municipality-month keys detected.",
            )
        )

    baseline_columns = set(baseline["panel"]["columns"])
    current_columns = set(current["panel"]["columns"])
    removed = sorted(baseline_columns - current_columns)
    added = sorted(current_columns - baseline_columns)
    disallowed_added = sorted(set(added) - ALLOWED_ADDITIVE_PANEL_COLUMNS)

    if removed:
        messages.append(
            ValidationMessage(
                check="panel_columns_removed",
                status="FAIL",
                detail=f"Baseline panel columns removed: {removed}",
            )
        )
    else:
        messages.append(
            ValidationMessage(
                check="panel_columns_removed",
                status="PASS",
                detail="No baseline panel columns were removed.",
            )
        )

    if disallowed_added:
        messages.append(
            ValidationMessage(
                check="panel_columns_added",
                status="FAIL",
                detail=f"Unexpected new panel columns: {disallowed_added}",
            )
        )
    else:
        allowed_detail = added if added else []
        messages.append(
            ValidationMessage(
                check="panel_columns_added",
                status="PASS",
                detail=f"Only allowed additive columns found: {allowed_detail}",
            )
        )

    if baseline["panel"]["y_p75_signature_sha256"] == current["panel"]["y_p75_signature_sha256"]:
        messages.append(
            ValidationMessage(
                check="y_p75_signature",
                status="PASS",
                detail="Existing Y/P75 columns are byte-equivalent after canonical serialization.",
            )
        )
    else:
        messages.append(
            ValidationMessage(
                check="y_p75_signature",
                status="FAIL",
                detail="Existing Y/P75 values changed unexpectedly.",
            )
        )

    baseline_outputs = baseline.get("output_hashes", {})
    current_outputs = current.get("output_hashes", {})
    for output_key, check_name in [
        ("consolidated_sha256", "baseline_consolidated_hash"),
        ("traceability_sha256", "baseline_traceability_hash"),
    ]:
        baseline_value = baseline_outputs.get(output_key)
        current_value = current_outputs.get(output_key)
        if baseline_value is None:
            messages.append(
                ValidationMessage(
                    check=check_name,
                    status="UNVERIFIED",
                    detail=f"Baseline does not contain {output_key}; check skipped.",
                )
            )
            continue
        if baseline_value == current_value:
            messages.append(
                ValidationMessage(
                    check=check_name,
                    status="PASS",
                    detail=f"Baseline-preserved output hash matched for {output_key}.",
                )
            )
        else:
            messages.append(
                ValidationMessage(
                    check=check_name,
                    status="FAIL",
                    detail=(
                        f"Baseline-preserved output hash mismatch for {output_key}: "
                        f"{baseline_value} -> {current_value}."
                    ),
                )
            )

    return messages


def notebook_cell_heading(cell: dict[str, Any]) -> str:
    """Extract normalized heading text from a notebook cell source.

    Args:
        cell: Notebook cell payload.

    Returns:
        First non-empty source line stripped, or empty string.
    """

    for line in cell.get("source", []):
        text = str(line).strip()
        if text:
            return text
    return ""


def find_code_cell_by_heading(
    cells: list[dict[str, Any]],
    heading_marker: str,
) -> tuple[int, dict[str, Any]] | None:
    """Locate a code cell by heading marker.

    Args:
        cells: Notebook cells.
        heading_marker: Substring expected in heading line.

    Returns:
        Tuple ``(cell_number, cell_payload)`` when found, else None.
    """

    for index, cell in enumerate(cells, start=1):
        if cell.get("cell_type") != "code":
            continue
        if heading_marker in notebook_cell_heading(cell):
            return index, cell
    return None


def output_text(output: dict[str, Any], key: str) -> str:
    """Extract normalized output text block from an output object.

    Args:
        output: Notebook output payload.
        key: Output key to extract (for example ``text``).

    Returns:
        Concatenated text.
    """

    value = output.get(key, "")
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value)


def parse_json_object_from_text(text: str) -> dict[str, Any] | None:
    """Parse the first JSON object found in a free-form text block.

    Args:
        text: Raw text block that may contain preamble lines.

    Returns:
        Parsed JSON object when found, else None.
    """

    decoder = json.JSONDecoder()
    for position, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[position:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def extract_stream_json_from_cell(cell: dict[str, Any]) -> dict[str, Any] | None:
    """Extract a JSON object from stream outputs of a code cell.

    Args:
        cell: Notebook cell payload.

    Returns:
        Parsed JSON dictionary when found, else None.
    """

    stream_chunks: list[str] = []
    for output in cell.get("outputs", []):
        if output.get("output_type") == "stream":
            stream_chunks.append(output_text(output, "text"))
    if not stream_chunks:
        return None
    return parse_json_object_from_text("".join(stream_chunks))


class _TableHTMLParser(HTMLParser):
    """Parse the first HTML table into row lists."""

    def __init__(self) -> None:
        super().__init__()
        self.in_table = False
        self.found_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table" and not self.found_table:
            self.in_table = True
            self.found_table = True
            return
        if not self.in_table:
            return
        if tag == "tr":
            self.in_row = True
            self.current_row = []
            return
        if tag in {"th", "td"} and self.in_row:
            self.in_cell = True
            self.current_cell = []

    def handle_data(self, data: str) -> None:
        if self.in_table and self.in_row and self.in_cell:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_table:
            return
        if tag in {"th", "td"} and self.in_cell:
            value = " ".join("".join(self.current_cell).split())
            self.current_row.append(value)
            self.current_cell = []
            self.in_cell = False
            return
        if tag == "tr" and self.in_row:
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []
            self.in_row = False
            return
        if tag == "table" and self.in_table:
            self.in_table = False


def extract_display_table_from_cell(cell: dict[str, Any]) -> pd.DataFrame | None:
    """Extract the first HTML table represented in a cell output.

    Args:
        cell: Notebook cell payload.

    Returns:
        Parsed dataframe or None when no table representation is found.
    """

    for output in cell.get("outputs", []):
        if output.get("output_type") not in {"display_data", "execute_result"}:
            continue
        data = output.get("data", {})
        if not isinstance(data, dict) or "text/html" not in data:
            continue
        html_value = data["text/html"]
        html_text = "".join(html_value) if isinstance(html_value, list) else str(html_value)
        if "<table" not in html_text.lower():
            continue
        parser = _TableHTMLParser()
        parser.feed(html_text)
        rows = parser.rows
        if len(rows) < 2:
            continue
        header = rows[0]
        body = rows[1:]
        if header and header[0] == "" and all(len(row) == len(header) for row in body):
            header = header[1:]
            body = [row[1:] for row in body]
        if not body:
            continue
        return pd.DataFrame(body, columns=header)
    return None


def compute_notebook_execution_fingerprint(
    root: Path,
    notebook_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute source-only notebook and module fingerprint for execution binding.

    The notebook hash excludes cell outputs, execution counters, and volatile
    metadata. It fingerprints only code-cell source payload plus stable ids.

    Args:
        root: Repository root.
        notebook_payload: Optional preloaded notebook payload.

    Returns:
        Fingerprint dictionary.
    """

    notebook_path = root / NOTEBOOK_PATH_RELATIVE
    payload = notebook_payload or json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = payload.get("cells", [])

    canonical_cells: list[dict[str, Any]] = []
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        metadata = cell.get("metadata", {})
        stable_metadata: dict[str, Any] = {}
        if isinstance(metadata, dict) and "language" in metadata:
            stable_metadata["language"] = metadata.get("language")

        canonical_cell: dict[str, Any] = {
            "cell_type": cell.get("cell_type"),
            "id": cell.get("id"),
            "source": cell.get("source", []),
        }
        if stable_metadata:
            canonical_cell["metadata"] = stable_metadata
        canonical_cells.append(canonical_cell)

    canonical_notebook = {
        "nbformat": payload.get("nbformat"),
        "nbformat_minor": payload.get("nbformat_minor"),
        "cells": canonical_cells,
    }
    notebook_canonical = json.dumps(
        canonical_notebook,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    notebook_source_sha256 = hashlib.sha256(notebook_canonical.encode("utf-8")).hexdigest()

    modules: dict[str, dict[str, Any]] = {}
    for relative_path in NOTEBOOK_FINGERPRINT_MODULE_PATHS:
        module_path = root / relative_path
        if not module_path.exists():
            raise RuntimeError(
                f"Required module for notebook fingerprint not found: {relative_path}"
            )
        modules[relative_path] = file_hash_record(module_path)

    composite_payload = {
        "notebook_source_sha256": notebook_source_sha256,
        "modules": modules,
    }
    composite_canonical = json.dumps(
        composite_payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    composite_sha256 = hashlib.sha256(composite_canonical.encode("utf-8")).hexdigest()

    return {
        "algorithm": "sha256",
        "notebook": {
            "path": NOTEBOOK_PATH_RELATIVE,
            "source_sha256": notebook_source_sha256,
        },
        "modules": modules,
        "composite_sha256": composite_sha256,
    }


def validate_notebook_surface(root: Path) -> list[ValidationMessage]:
    """Validate notebook saved outputs and execution/artifact coherence.

    Args:
        root: Repository root.

    Returns:
        Validation messages.
    """

    notebook_path = root / NOTEBOOK_PATH_RELATIVE
    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = payload.get("cells", [])

    messages: list[ValidationMessage] = []

    try:
        visual_assets = load_visual_assets_module(root)
        code_only = visual_assets.assert_notebook_code_only(notebook_path)
    except (RuntimeError, FileNotFoundError, AttributeError):
        non_code = [
            {
                "id": cell.get("id"),
                "cell_type": cell.get("cell_type"),
            }
            for cell in cells
            if cell.get("cell_type") != "code"
        ]
        code_only = {
            "cell_count": len(cells),
            "code_only": len(non_code) == 0,
            "non_code_cells": non_code,
        }
    if bool(code_only["code_only"]):
        code_only_msg = ValidationMessage(
            check="notebook_code_only",
            status="PASS",
            detail="Notebook has code-only cells.",
        )
    else:
        code_only_msg = ValidationMessage(
            check="notebook_code_only",
            status="FAIL",
            detail=f"Notebook contains non-code cells: {code_only['non_code_cells']}",
        )
    messages.append(code_only_msg)

    output_errors: list[str] = []
    for cell_number, cell in enumerate(cells, start=1):
        heading = notebook_cell_heading(cell)
        for output in cell.get("outputs", []):
            if output.get("output_type") != "error":
                continue
            ename = str(output.get("ename", "error"))
            evalue = str(output.get("evalue", "")).strip()
            location = f"cell {cell_number} ({heading})"
            output_errors.append(f"{location}: {ename} {evalue}".strip())

    messages.append(
        ValidationMessage(
            check="notebook_error_outputs",
            status="FAIL" if output_errors else "PASS",
            detail=(
                "Notebook contains error outputs: " + " | ".join(output_errors)
                if output_errors
                else "Notebook saved outputs contain no error output objects."
            ),
        )
    )

    missing_sections: list[str] = []
    missing_execution: list[str] = []
    missing_outputs: list[str] = []
    for marker in NOTEBOOK_REQUIRED_OUTPUT_SECTION_MARKERS:
        located = find_code_cell_by_heading(cells, marker)
        if located is None:
            missing_sections.append(marker)
            continue
        cell_number, cell = located
        heading = notebook_cell_heading(cell)
        if cell.get("execution_count") is None:
            missing_execution.append(f"cell {cell_number} ({heading})")
        if not cell.get("outputs", []):
            missing_outputs.append(f"cell {cell_number} ({heading})")

    messages.append(
        ValidationMessage(
            check="notebook_required_sections_present",
            status="FAIL" if missing_sections else "PASS",
            detail=(
                "Notebook is missing required result/control sections: "
                + ", ".join(missing_sections)
                if missing_sections
                else "All required result/control sections were located by chapter heading."
            ),
        )
    )
    messages.append(
        ValidationMessage(
            check="notebook_required_cells_executed",
            status="FAIL" if missing_execution else "PASS",
            detail=(
                "Required cells missing execution_count: " + ", ".join(missing_execution)
                if missing_execution
                else "Required result/control cells have saved execution counts."
            ),
        )
    )
    messages.append(
        ValidationMessage(
            check="notebook_required_cells_have_outputs",
            status="FAIL" if missing_outputs else "PASS",
            detail=(
                "Required cells missing saved outputs: " + ", ".join(missing_outputs)
                if missing_outputs
                else "Required result/control cells have saved outputs."
            ),
        )
    )

    figure_output_cells: list[int] = []
    table_output_cells: list[int] = []
    for cell_number, cell in enumerate(cells, start=1):
        for output in cell.get("outputs", []):
            if output.get("output_type") not in {"display_data", "execute_result"}:
                continue
            data = output.get("data", {})
            if not isinstance(data, dict):
                continue
            if "image/png" in data:
                figure_output_cells.append(cell_number)
            if "text/html" in data:
                html_value = data.get("text/html", "")
                html_text = (
                    "".join(str(item) for item in html_value)
                    if isinstance(html_value, list)
                    else str(html_value)
                )
                if "<table" in html_text.lower():
                    table_output_cells.append(cell_number)

    messages.append(
        ValidationMessage(
            check="notebook_figures_count",
            status="PASS" if len(figure_output_cells) == 2 else "FAIL",
            detail=(
                f"Found {len(figure_output_cells)} saved figure render outputs "
                f"(expected 2); cells={figure_output_cells}."
            ),
        )
    )
    messages.append(
        ValidationMessage(
            check="notebook_tables_count",
            status="PASS" if len(table_output_cells) == 2 else "FAIL",
            detail=(
                f"Found {len(table_output_cells)} saved table render outputs "
                f"(expected 2); cells={table_output_cells}."
            ),
        )
    )

    panel_cell = find_code_cell_by_heading(cells, "Chapter 1 - Section 6: Monthly panel inspection")
    if panel_cell is None:
        messages.append(
            ValidationMessage(
                check="notebook_panel_summary_alignment",
                status="FAIL",
                detail="Panel inspection cell was not found by heading.",
            )
        )
    else:
        cell_number, cell = panel_cell
        saved_panel_summary = extract_stream_json_from_cell(cell)
        if saved_panel_summary is None:
            messages.append(
                ValidationMessage(
                    check="notebook_panel_summary_alignment",
                    status="FAIL",
                    detail=(
                        f"Cell {cell_number} (Chapter 1 - Section 6) does not contain "
                        "a parseable JSON stream summary."
                    ),
                )
            )
        else:
            panel = pd.read_csv(root / "data/processed/panel_mensual_dengue_clima.csv")
            expected_rows = int(len(panel))
            expected_columns = int(len(panel.columns))
            try:
                observed_rows = int(saved_panel_summary.get("rows", -1))
                observed_columns = int(saved_panel_summary.get("columns", -1))
            except (TypeError, ValueError):
                observed_rows = -1
                observed_columns = -1

            panel_ok = observed_rows == expected_rows and observed_columns == expected_columns
            messages.append(
                ValidationMessage(
                    check="notebook_panel_summary_alignment",
                    status="PASS" if panel_ok else "FAIL",
                    detail=(
                        "Saved panel summary matches real panel dimensions "
                        f"(rows={expected_rows}, columns={expected_columns})."
                        if panel_ok
                        else (
                            f"Cell {cell_number} panel summary mismatch: "
                            f"saved(rows={observed_rows}, columns={observed_columns}) "
                            f"!= real(rows={expected_rows}, columns={expected_columns})."
                        )
                    ),
                )
            )

    chapter6_cell = find_code_cell_by_heading(
        cells,
        "Chapter 6 - Relationships with Y and lag diagnostics by horizon",
    )
    if chapter6_cell is None:
        messages.append(
            ValidationMessage(
                check="notebook_chapter6_summary_alignment",
                status="FAIL",
                detail="Chapter 6 cell was not found by heading.",
            )
        )
    else:
        cell_number, cell = chapter6_cell
        saved_chapter6_summary = extract_stream_json_from_cell(cell)
        chapter6_path = root / "tmp/stage2_y_reconciliation/chapter6_summary.json"
        if saved_chapter6_summary is None:
            messages.append(
                ValidationMessage(
                    check="notebook_chapter6_summary_alignment",
                    status="FAIL",
                    detail=f"Cell {cell_number} Chapter 6 output does not contain parseable JSON.",
                )
            )
        elif not chapter6_path.exists():
            messages.append(
                ValidationMessage(
                    check="notebook_chapter6_summary_alignment",
                    status="FAIL",
                    detail="Artifact tmp/stage2_y_reconciliation/chapter6_summary.json is missing.",
                )
            )
        else:
            artifact_chapter6_summary = json.loads(chapter6_path.read_text(encoding="utf-8"))
            compared_fields = (
                "aggregate_rows",
                "detail_rows",
                "method",
                "selection_rows_by_horizon",
                "selection_bounds_by_horizon",
            )
            mismatched_fields = [
                field
                for field in compared_fields
                if saved_chapter6_summary.get(field) != artifact_chapter6_summary.get(field)
            ]
            messages.append(
                ValidationMessage(
                    check="notebook_chapter6_summary_alignment",
                    status="FAIL" if mismatched_fields else "PASS",
                    detail=(
                        "Saved Chapter 6 stream summary matches chapter6_summary.json for "
                        "selection and support fields."
                        if not mismatched_fields
                        else (f"Cell {cell_number} Chapter 6 mismatch fields: {mismatched_fields}.")
                    ),
                )
            )

    chapter8_cell = find_code_cell_by_heading(
        cells,
        "Chapter 8 - Temporal validation protocol structure",
    )
    if chapter8_cell is None:
        messages.append(
            ValidationMessage(
                check="notebook_temporal_table_alignment",
                status="FAIL",
                detail="Chapter 8 cell was not found by heading.",
            )
        )
    else:
        cell_number, cell = chapter8_cell
        saved_table = extract_display_table_from_cell(cell)
        audit_csv_path = (
            root / "tmp/stage2_y_reconciliation/chapter8_table2_temporal_validation_audit.csv"
        )
        if saved_table is None:
            messages.append(
                ValidationMessage(
                    check="notebook_temporal_table_alignment",
                    status="FAIL",
                    detail=(
                        f"Cell {cell_number} Chapter 8 output does not include a parseable "
                        "HTML table representation."
                    ),
                )
            )
        elif not audit_csv_path.exists():
            messages.append(
                ValidationMessage(
                    check="notebook_temporal_table_alignment",
                    status="FAIL",
                    detail=(
                        "Artifact tmp/stage2_y_reconciliation/"
                        "chapter8_table2_temporal_validation_audit.csv is missing."
                    ),
                )
            )
        else:
            expected_table = pd.read_csv(audit_csv_path)
            compare_columns = [
                "window_id",
                "horizon",
                "train_rows",
                "train_municipalities",
                "validation_rows",
                "validation_municipalities",
                "temporal_validation_result",
            ]
            missing_saved_columns = sorted(set(compare_columns) - set(saved_table.columns))
            missing_expected_columns = sorted(set(compare_columns) - set(expected_table.columns))

            if missing_saved_columns or missing_expected_columns:
                messages.append(
                    ValidationMessage(
                        check="notebook_temporal_table_alignment",
                        status="FAIL",
                        detail=(
                            "Temporal table columns mismatch; "
                            f"missing_saved={missing_saved_columns}, "
                            f"missing_csv={missing_expected_columns}."
                        ),
                    )
                )
            else:
                saved_view = saved_table[compare_columns].copy()
                expected_view = expected_table[compare_columns].copy()

                for column in [
                    "train_rows",
                    "train_municipalities",
                    "validation_rows",
                    "validation_municipalities",
                ]:
                    saved_view[column] = pd.to_numeric(saved_view[column], errors="coerce").astype(
                        "Int64"
                    )
                    expected_view[column] = pd.to_numeric(
                        expected_view[column], errors="coerce"
                    ).astype("Int64")

                for column in ["window_id", "horizon", "temporal_validation_result"]:
                    saved_view[column] = saved_view[column].astype(str).str.strip()
                    expected_view[column] = expected_view[column].astype(str).str.strip()

                order_columns = ["window_id", "horizon"]
                saved_view = saved_view.sort_values(order_columns).reset_index(drop=True)
                expected_view = expected_view.sort_values(order_columns).reset_index(drop=True)
                aligned = saved_view.equals(expected_view)

                messages.append(
                    ValidationMessage(
                        check="notebook_temporal_table_alignment",
                        status="PASS" if aligned else "FAIL",
                        detail=(
                            "Saved Chapter 8 table matches audit CSV for horizon, counts, "
                            "and validation result columns."
                            if aligned
                            else (
                                f"Cell {cell_number} Chapter 8 table differs from audit CSV "
                                f"for columns {compare_columns}."
                            )
                        ),
                    )
                )

    chapter10_cell = find_code_cell_by_heading(
        cells, "Chapter 10 - Analysis manifest and scope validator"
    )
    embedded_manifest: dict[str, Any] | None = None
    if chapter10_cell is None:
        messages.append(
            ValidationMessage(
                check="notebook_embedded_manifest_alignment",
                status="FAIL",
                detail="Chapter 10 cell was not found by heading.",
            )
        )
    else:
        cell_number, cell = chapter10_cell
        chapter10_stream = extract_stream_json_from_cell(cell)
        manifest_path = root / NOTEBOOK_ANALYSIS_MANIFEST
        if chapter10_stream is None:
            messages.append(
                ValidationMessage(
                    check="notebook_embedded_manifest_alignment",
                    status="FAIL",
                    detail=f"Cell {cell_number} Chapter 10 output does not contain parseable JSON.",
                )
            )
        elif not manifest_path.exists():
            messages.append(
                ValidationMessage(
                    check="notebook_embedded_manifest_alignment",
                    status="FAIL",
                    detail=f"Notebook analysis manifest missing: {NOTEBOOK_ANALYSIS_MANIFEST}",
                )
            )
        else:
            embedded_manifest = chapter10_stream.get("analysis_manifest")
            current_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(embedded_manifest, dict):
                messages.append(
                    ValidationMessage(
                        check="notebook_embedded_manifest_alignment",
                        status="FAIL",
                        detail=(
                            f"Cell {cell_number} Chapter 10 output missing "
                            "analysis_manifest payload."
                        ),
                    )
                )
            else:
                keys = sorted(set(embedded_manifest) | set(current_manifest))
                differing_keys = [
                    key for key in keys if embedded_manifest.get(key) != current_manifest.get(key)
                ]
                messages.append(
                    ValidationMessage(
                        check="notebook_embedded_manifest_alignment",
                        status="FAIL" if differing_keys else "PASS",
                        detail=(
                            "Embedded analysis manifest matches notebook_analysis_manifest.json."
                            if not differing_keys
                            else (
                                "Embedded analysis manifest differs from current file for keys: "
                                + ", ".join(differing_keys[:8])
                            )
                        ),
                    )
                )

    if embedded_manifest is None:
        messages.append(
            ValidationMessage(
                check="notebook_execution_fingerprint_alignment",
                status="FAIL",
                detail=(
                    "Embedded manifest not available; execution fingerprint cannot be validated."
                ),
            )
        )
    else:
        current_fingerprint = compute_notebook_execution_fingerprint(root, payload)
        stored_fingerprint = embedded_manifest.get("notebook_execution_fingerprint")
        if not isinstance(stored_fingerprint, dict):
            messages.append(
                ValidationMessage(
                    check="notebook_execution_fingerprint_alignment",
                    status="FAIL",
                    detail="Embedded analysis manifest is missing notebook_execution_fingerprint.",
                )
            )
        else:
            fingerprint_ok = stored_fingerprint == current_fingerprint
            mismatch_parts: list[str] = []
            if isinstance(stored_fingerprint.get("notebook"), dict) and isinstance(
                current_fingerprint.get("notebook"), dict
            ):
                if stored_fingerprint["notebook"].get("source_sha256") != current_fingerprint[
                    "notebook"
                ].get("source_sha256"):
                    mismatch_parts.append("notebook_source_sha256")
            if stored_fingerprint.get("modules") != current_fingerprint.get("modules"):
                mismatch_parts.append("module_hashes")
            if stored_fingerprint.get("composite_sha256") != current_fingerprint.get(
                "composite_sha256"
            ):
                mismatch_parts.append("composite_sha256")

            messages.append(
                ValidationMessage(
                    check="notebook_execution_fingerprint_alignment",
                    status="PASS" if fingerprint_ok else "FAIL",
                    detail=(
                        "Saved notebook execution fingerprint matches current "
                        "notebook and module sources."
                        if fingerprint_ok
                        else (
                            "Notebook execution fingerprint mismatch in "
                            + ", ".join(mismatch_parts or ["unknown_fields"])
                            + "; rerun and save notebook outputs."
                        )
                    ),
                )
            )

    return messages


def validate_scope_reporting(root: Path) -> list[ValidationMessage]:
    """Validate bounded-scope notebook declarations for Stage 2 closeout.

    Args:
        root: Repository root.

    Returns:
        Validation messages.
    """

    notebook_path = root / "notebooks/03_consolidated_dataset_pipeline.ipynb"
    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = payload.get("cells", [])
    code_sources = [
        "\n".join(cell.get("source", [])) for cell in cells if cell.get("cell_type") == "code"
    ]
    combined = "\n\n".join(code_sources)

    sample_size_declared = "sample_size = 150_000" in combined
    profile_helper_used = "visual_assets.summarize_profile_scope" in combined
    partial_scope_declared = "partial evidence" in combined.lower()
    correlation_helper_used = "visual_assets.build_correlation_diagnostics" in combined
    month_adjustment_declared = "global calendar-month mean centering" in combined

    return [
        ValidationMessage(
            check="scope_sample_size_declared",
            status="PASS" if sample_size_declared else "FAIL",
            detail=(
                "Notebook declares 150,000-row profiling sample scope."
                if sample_size_declared
                else "Notebook is missing explicit 150,000-row profiling sample declaration."
            ),
        ),
        ValidationMessage(
            check="scope_profile_helper_used",
            status="PASS" if profile_helper_used else "FAIL",
            detail=(
                "Notebook delegates profile-scope summary to shared tested helper."
                if profile_helper_used
                else "Notebook does not use shared profile-scope helper."
            ),
        ),
        ValidationMessage(
            check="scope_partial_findings_declared",
            status="PASS" if partial_scope_declared else "FAIL",
            detail=(
                "Notebook declares profile findings as partial evidence."
                if partial_scope_declared
                else "Notebook does not declare profile findings as partial evidence."
            ),
        ),
        ValidationMessage(
            check="scope_correlation_helper_used",
            status="PASS" if correlation_helper_used else "FAIL",
            detail=(
                "Notebook delegates correlation diagnostics to shared tested helper."
                if correlation_helper_used
                else "Notebook does not use shared correlation diagnostics helper."
            ),
        ),
        ValidationMessage(
            check="scope_month_adjustment_declared",
            status="PASS" if month_adjustment_declared else "FAIL",
            detail=(
                "Notebook declares global calendar-month adjustment scope "
                "for correlation diagnostics."
                if month_adjustment_declared
                else "Notebook is missing global calendar-month adjustment scope declaration."
            ),
        ),
    ]


def validate_temporal_selector_consistency(
    root: Path,
    policy: dict[str, Any] | None = None,
) -> list[ValidationMessage]:
    """Validate horizon target-period consistency in panel-level labels.

    Args:
        root: Repository root.
        policy: Optional model-eligibility policy payload.

    Returns:
        Validation messages.
    """

    panel_path = root / "data/processed/panel_mensual_dengue_clima.csv"
    panel = pd.read_csv(panel_path)
    panel["year_month"] = panel["year_month"].astype(str).map(period_to_yyyymm)

    active_policy = policy or capture_snapshot(root)["coverage"]["model_eligibility_policy"]
    target_min, target_max, reserved_block_start = extract_development_target_bounds(active_policy)

    t1 = panel[panel["y_evaluable_t1"].fillna(False)]
    t2 = panel[panel["y_evaluable_t2"].fillna(False)]

    t1_reserved = int((t1["target_period_t1"].astype(str) >= reserved_block_start).sum())
    t2_reserved = int((t2["target_period_t2"].astype(str) >= reserved_block_start).sum())

    selected_t1 = independent_select_supervised_rows(
        panel,
        1,
        target_min_period=target_min,
        target_max_period=target_max,
        reference_max_period=target_max,
    )
    selected_t2 = independent_select_supervised_rows(
        panel,
        2,
        target_min_period=target_min,
        target_max_period=target_max,
        reference_max_period=target_max,
    )

    selected_t1_min_violations = int(
        (selected_t1["target_period_t1"].astype(str) < target_min).sum()
    )
    selected_t2_min_violations = int(
        (selected_t2["target_period_t2"].astype(str) < target_min).sum()
    )
    selected_t1_violations = int(
        (selected_t1["target_period_t1"].astype(str) >= reserved_block_start).sum()
    )
    selected_t2_violations = int(
        (selected_t2["target_period_t2"].astype(str) >= reserved_block_start).sum()
    )

    messages = [
        ValidationMessage(
            check="panel_target_period_exposure_t1",
            status="PASS",
            detail=(
                "Panel-level evaluable labels include "
                f"{t1_reserved} target periods in/after reserved block; "
                "supervised selectors must exclude them in analysis/training views."
            ),
        ),
        ValidationMessage(
            check="panel_target_period_exposure_t2",
            status="PASS",
            detail=(
                "Panel-level evaluable labels include "
                f"{t2_reserved} target periods in/after reserved block; "
                "supervised selectors must exclude them in analysis/training views."
            ),
        ),
        ValidationMessage(
            check="supervised_selector_reserved_t1",
            status=(
                "PASS"
                if selected_t1_violations == 0 and selected_t1_min_violations == 0
                else "FAIL"
            ),
            detail=(
                "Horizon T+1 supervised selector policy-bound violations: "
                "target<min="
                f"{selected_t1_min_violations}, target>=reserved={selected_t1_violations} "
                f"(min={target_min}, max={target_max}, reserved_start={reserved_block_start})"
            ),
        ),
        ValidationMessage(
            check="supervised_selector_reserved_t2",
            status=(
                "PASS"
                if selected_t2_violations == 0 and selected_t2_min_violations == 0
                else "FAIL"
            ),
            detail=(
                "Horizon T+2 supervised selector policy-bound violations: "
                "target<min="
                f"{selected_t2_min_violations}, target>=reserved={selected_t2_violations} "
                f"(min={target_min}, max={target_max}, reserved_start={reserved_block_start})"
            ),
        ),
    ]
    return messages


def validate_execution_manifest_hashes(root: Path) -> list[ValidationMessage]:
    """Validate execution-manifest hashes against real output files.

    Args:
        root: Repository root.

    Returns:
        Validation messages.
    """

    manifest_path = (
        root / "data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json"
    )
    if not manifest_path.exists():
        detail = (
            "Execution manifest missing: "
            "data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json"
        )
        return [
            ValidationMessage(
                check="execution_manifest_pipeline_code_fingerprint",
                status="FAIL",
                detail=detail,
            ),
            ValidationMessage(
                check="execution_manifest_output_files_exist",
                status="FAIL",
                detail=detail,
            ),
            ValidationMessage(
                check="execution_manifest_output_hash_alignment",
                status="FAIL",
                detail=detail,
            ),
        ]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        detail = f"Execution manifest is not valid JSON: {exc.msg}"
        return [
            ValidationMessage(
                check="execution_manifest_pipeline_code_fingerprint",
                status="FAIL",
                detail=detail,
            ),
            ValidationMessage(
                check="execution_manifest_output_files_exist",
                status="FAIL",
                detail=detail,
            ),
            ValidationMessage(
                check="execution_manifest_output_hash_alignment",
                status="FAIL",
                detail=detail,
            ),
        ]

    if not isinstance(manifest, dict):
        detail = "Execution manifest root payload must be a JSON object."
        return [
            ValidationMessage(
                check="execution_manifest_pipeline_code_fingerprint",
                status="FAIL",
                detail=detail,
            ),
            ValidationMessage(
                check="execution_manifest_output_files_exist",
                status="FAIL",
                detail=detail,
            ),
            ValidationMessage(
                check="execution_manifest_output_hash_alignment",
                status="FAIL",
                detail=detail,
            ),
        ]

    pipeline_info = manifest.get("pipeline", {})
    pipeline_module_path = root / "scripts/stage2_consolidated_dataset_pipeline.py"
    expected_module_path = "scripts/stage2_consolidated_dataset_pipeline.py"
    expected_module_sha256 = (
        sha256_file(pipeline_module_path) if pipeline_module_path.exists() else None
    )

    pipeline_fingerprint_issues: list[str] = []
    if not isinstance(pipeline_info, dict):
        pipeline_fingerprint_issues.append("pipeline_section_missing")
    else:
        if pipeline_info.get("module") != expected_module_path:
            pipeline_fingerprint_issues.append("pipeline_module_path_mismatch")
        if expected_module_sha256 is None:
            pipeline_fingerprint_issues.append("pipeline_module_file_missing")
        if "module_sha256" not in pipeline_info:
            pipeline_fingerprint_issues.append("pipeline_module_sha256_missing")
        elif (
            expected_module_sha256 is not None
            and pipeline_info.get("module_sha256") != expected_module_sha256
        ):
            pipeline_fingerprint_issues.append("pipeline_module_sha256_mismatch")

    mismatches: list[str] = []
    missing_files: list[str] = []
    outputs_raw = manifest.get("outputs")
    outputs_shape_issue: str | None = None
    if not isinstance(outputs_raw, dict):
        outputs_shape_issue = "outputs_section_missing_or_invalid"
        outputs: dict[str, Any] = {}
    else:
        outputs = outputs_raw

    for output_name, output_info in outputs.items():
        if not isinstance(output_info, dict):
            mismatches.append(f"{output_name}:entry_invalid")
            continue
        relative_path = output_info.get("path")
        if not isinstance(relative_path, str):
            mismatches.append(f"{output_name}:path_missing_or_invalid")
            continue
        file_path = root / relative_path
        if not file_path.exists():
            missing_files.append(relative_path)
            continue
        expected_sha = output_info.get("sha256")
        expected_bytes_raw = output_info.get("bytes")
        expected_bytes = parse_expected_byte_count(expected_bytes_raw)
        actual = file_hash_record(file_path)
        if not isinstance(expected_sha, str) or not expected_sha:
            mismatches.append(f"{output_name}:sha256_missing")
        elif actual["sha256"] != expected_sha:
            mismatches.append(f"{output_name}:sha256")
        if expected_bytes_raw is None:
            mismatches.append(f"{output_name}:bytes_missing")
        elif expected_bytes is None:
            mismatches.append(f"{output_name}:bytes_invalid")
        elif int(actual["bytes"]) != expected_bytes:
            mismatches.append(f"{output_name}:bytes")

    if outputs_shape_issue is not None:
        missing_detail = (
            "Execution manifest outputs section is missing or invalid; "
            "cannot verify file existence."
        )
        missing_status = "FAIL"
    elif missing_files:
        missing_detail = ", ".join(sorted(missing_files))
        missing_status = "FAIL"
    else:
        missing_detail = "All manifest output files exist."
        missing_status = "PASS"

    if outputs_shape_issue is not None:
        mismatch_detail = "Execution manifest outputs section is missing or invalid."
        mismatch_status = "FAIL"
    elif mismatches:
        mismatch_detail = ", ".join(sorted(mismatches))
        mismatch_status = "FAIL"
    else:
        mismatch_detail = "All output hash/size records match manifest values."
        mismatch_status = "PASS"

    return [
        ValidationMessage(
            check="execution_manifest_pipeline_code_fingerprint",
            status="FAIL" if pipeline_fingerprint_issues else "PASS",
            detail=(
                "Execution manifest pipeline fingerprint issues: "
                + ", ".join(sorted(pipeline_fingerprint_issues))
                if pipeline_fingerprint_issues
                else "Execution manifest stores pipeline module path and matching code SHA-256."
            ),
        ),
        ValidationMessage(
            check="execution_manifest_output_files_exist",
            status=missing_status,
            detail=missing_detail,
        ),
        ValidationMessage(
            check="execution_manifest_output_hash_alignment",
            status=mismatch_status,
            detail=mismatch_detail,
        ),
    ]


def validate_notebook_artifact_manifest(root: Path) -> list[ValidationMessage]:
    """Validate notebook artifact manifest entries against real files.

    Args:
        root: Repository root.

    Returns:
        Validation messages.
    """

    manifest_path = root / NOTEBOOK_ANALYSIS_MANIFEST
    if not manifest_path.exists():
        return [
            ValidationMessage(
                check="notebook_manifest_exists",
                status="FAIL",
                detail=f"Notebook analysis manifest missing: {NOTEBOOK_ANALYSIS_MANIFEST}",
            )
        ]

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        detail = f"Notebook analysis manifest is not valid JSON: {exc.msg}"
        return [
            ValidationMessage(
                check="notebook_manifest_file_hash_alignment",
                status="FAIL",
                detail=detail,
            ),
            ValidationMessage(
                check="notebook_manifest_missing_files",
                status="FAIL",
                detail=detail,
            ),
            ValidationMessage(
                check="notebook_manifest_resource_consistency",
                status="FAIL",
                detail=detail,
            ),
        ]

    if not isinstance(payload, dict):
        detail = "Notebook analysis manifest root payload must be a JSON object."
        return [
            ValidationMessage(
                check="notebook_manifest_file_hash_alignment",
                status="FAIL",
                detail=detail,
            ),
            ValidationMessage(
                check="notebook_manifest_missing_files",
                status="FAIL",
                detail=detail,
            ),
            ValidationMessage(
                check="notebook_manifest_resource_consistency",
                status="FAIL",
                detail=detail,
            ),
        ]
    file_entries = payload.get("files", [])
    indexed_entries: dict[str, dict[str, Any]] = {
        str(item.get("path")): item
        for item in file_entries
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }

    missing_files: list[str] = []
    mismatches: list[str] = []
    for relative_path, entry in indexed_entries.items():
        artifact_path = root / relative_path
        if not artifact_path.exists():
            missing_files.append(relative_path)
            continue
        actual = file_hash_record(artifact_path)
        expected_sha = entry.get("sha256")
        expected_bytes_raw = entry.get("bytes")
        expected_bytes = parse_expected_byte_count(expected_bytes_raw)
        if expected_sha != actual["sha256"]:
            mismatches.append(f"{relative_path}:sha256")
        if expected_bytes_raw is None:
            mismatches.append(f"{relative_path}:bytes_missing")
        elif expected_bytes is None:
            mismatches.append(f"{relative_path}:bytes_invalid")
        elif expected_bytes != int(actual["bytes"]):
            mismatches.append(f"{relative_path}:bytes")

    resource_manifest = payload.get("resource_manifest", {})
    resource_paths = {
        path
        for path in collect_manifest_paths(resource_manifest)
        if path.startswith("tmp/stage2_y_reconciliation/")
    }
    missing_resource_entries = sorted(resource_paths - set(indexed_entries))

    return [
        ValidationMessage(
            check="notebook_manifest_file_hash_alignment",
            status="FAIL" if mismatches else "PASS",
            detail=(
                "Notebook artifact hashes/sizes mismatch: " + ", ".join(sorted(mismatches))
                if mismatches
                else "All notebook artifact hashes/sizes match manifest entries."
            ),
        ),
        ValidationMessage(
            check="notebook_manifest_missing_files",
            status="FAIL" if missing_files else "PASS",
            detail=(
                "Manifest references missing files: " + ", ".join(sorted(missing_files))
                if missing_files
                else "All notebook manifest file entries are present on disk."
            ),
        ),
        ValidationMessage(
            check="notebook_manifest_resource_consistency",
            status="FAIL" if missing_resource_entries else "PASS",
            detail=(
                "Resource manifest paths not listed in files[]: "
                + ", ".join(missing_resource_entries)
                if missing_resource_entries
                else "Resource manifest paths are represented in files[]."
            ),
        ),
    ]


def validate_current_endemic_channel_integrity(root: Path) -> list[ValidationMessage]:
    """Validate endemic-channel columns with independent recomputation.

    Args:
        root: Repository root.

    Returns:
        Validation messages.
    """

    panel_path = root / "data/processed/panel_mensual_dengue_clima.csv"
    panel = pd.read_csv(panel_path)
    panel["municipality_code"] = panel["municipality_code"].astype(str).str.zfill(5)
    panel["year_month"] = panel["year_month"].astype(str).map(period_to_yyyymm)

    required_channel_columns = {
        "p25_canal_t",
        "p50_canal_t",
        "p75_canal_t",
        "zona_canal_t",
    }
    missing_columns = sorted(required_channel_columns - set(panel.columns))
    if missing_columns:
        return [
            ValidationMessage(
                check="channel_columns_present",
                status="FAIL",
                detail=f"Panel missing endemic-channel columns: {missing_columns}",
            )
        ]

    observed_thresholds = panel[["p25_canal_t", "p50_canal_t", "p75_canal_t"]].apply(
        pd.to_numeric,
        errors="coerce",
    )
    observed_zone = panel["zona_canal_t"].astype("string")

    duplicate_keys = int(panel.duplicated(["municipality_code", "year_month"]).sum())
    if duplicate_keys > 0:
        return [
            ValidationMessage(
                check="channel_panel_key_uniqueness",
                status="FAIL",
                detail=(
                    "Panel must have unique municipality_code+year_month keys for "
                    f"independent channel recomputation; duplicates={duplicate_keys}."
                ),
            )
        ]

    invalid_zone_rows = int((observed_zone.notna() & ~observed_zone.isin(CANAL_ZONE_VALUES)).sum())
    threshold_complete = observed_thresholds.notna().all(axis=1)
    threshold_any = observed_thresholds.notna().any(axis=1)
    mixed_null_rows = int(
        (
            (observed_zone.isna() & threshold_any) | (observed_zone.notna() & ~threshold_complete)
        ).sum()
    )

    monotonic_rows = observed_thresholds[threshold_complete]
    monotonic_violations = int(
        (
            (monotonic_rows["p25_canal_t"] > monotonic_rows["p50_canal_t"])
            | (monotonic_rows["p50_canal_t"] > monotonic_rows["p75_canal_t"])
        ).sum()
    )

    independent = recompute_channel_independently(panel)
    try:
        merged = panel.merge(
            independent,
            how="left",
            on=["municipality_code", "year_month"],
            validate="one_to_one",
        )
    except ValueError as exc:
        return [
            ValidationMessage(
                check="channel_independent_recompute_match",
                status="FAIL",
                detail=(f"Unable to compare panel vs independent channel recomputation: {exc}"),
            )
        ]

    evaluable_mask = merged["independent_channel_status"] == "evaluable"
    non_evaluable_mask = ~evaluable_mask

    tolerance = 1e-9
    threshold_mismatches = int(
        (
            evaluable_mask
            & (
                ((merged["p25_canal_t"] - merged["independent_p25_canal_t"]).abs() > tolerance)
                | ((merged["p50_canal_t"] - merged["independent_p50_canal_t"]).abs() > tolerance)
                | ((merged["p75_canal_t"] - merged["independent_p75_canal_t"]).abs() > tolerance)
            )
        ).sum()
    )
    zone_mismatches = int(
        (
            evaluable_mask
            & (
                merged["zona_canal_t"].astype("string")
                != merged["independent_zona_canal_t"].astype("string")
            )
        ).sum()
    )

    non_evaluable_unjustified = int(
        (
            non_evaluable_mask
            & (
                merged["zona_canal_t"].notna()
                | merged[["p25_canal_t", "p50_canal_t", "p75_canal_t"]].notna().any(axis=1)
            )
        ).sum()
    )

    evaluable_missing_values = int(
        (
            evaluable_mask
            & (
                merged["zona_canal_t"].isna()
                | merged[["p25_canal_t", "p50_canal_t", "p75_canal_t"]].isna().any(axis=1)
            )
        ).sum()
    )

    return [
        ValidationMessage(
            check="channel_allowed_values",
            status="FAIL" if invalid_zone_rows > 0 else "PASS",
            detail=f"Rows with invalid zona_canal_t values: {invalid_zone_rows}",
        ),
        ValidationMessage(
            check="channel_null_consistency",
            status="FAIL" if mixed_null_rows > 0 else "PASS",
            detail=f"Rows with mixed null/non-null threshold-zone combinations: {mixed_null_rows}",
        ),
        ValidationMessage(
            check="channel_percentile_order",
            status="FAIL" if monotonic_violations > 0 else "PASS",
            detail=f"Rows violating P25<=P50<=P75: {monotonic_violations}",
        ),
        ValidationMessage(
            check="channel_independent_recompute_match",
            status=(
                "PASS"
                if threshold_mismatches == 0
                and zone_mismatches == 0
                and non_evaluable_unjustified == 0
                and evaluable_missing_values == 0
                else "FAIL"
            ),
            detail=(
                "Independent channel recomputation mismatch counters: "
                f"threshold={threshold_mismatches}, zone={zone_mismatches}, "
                f"non_evaluable_unjustified={non_evaluable_unjustified}, "
                f"evaluable_missing={evaluable_missing_values}."
            ),
        ),
    ]


def validate_temporal_artifact_selections(
    root: Path,
    policy: dict[str, Any] | None = None,
    window_train_endpoints: tuple[str, ...] = TEMPORAL_WINDOW_TRAIN_ENDPOINTS,
) -> list[ValidationMessage]:
    """Validate chapter-6 and chapter-8 temporal artifacts against real panel rows.

    Args:
        root: Repository root.
        policy: Optional model-eligibility policy payload.
        window_train_endpoints: Train endpoints for temporal windows.

    Returns:
        Validation messages.
    """

    panel_path = root / "data/processed/panel_mensual_dengue_clima.csv"
    panel = pd.read_csv(panel_path)
    panel["municipality_code"] = panel["municipality_code"].astype(str).str.zfill(5)
    panel["year_month"] = panel["year_month"].astype(str).map(period_to_yyyymm)

    active_policy = policy or capture_snapshot(root)["coverage"]["model_eligibility_policy"]
    target_min, target_max, reserved_block_start = extract_development_target_bounds(active_policy)

    chapter6_summary_path = root / "tmp/stage2_y_reconciliation/chapter6_summary.json"
    chapter6_meta_path = root / "tmp/stage2_y_reconciliation/chapter6_lag_associations_meta.json"
    chapter8_audit_path = (
        root / "tmp/stage2_y_reconciliation/chapter8_table2_temporal_validation_audit.csv"
    )

    if (
        not chapter6_summary_path.exists()
        or not chapter6_meta_path.exists()
        or not chapter8_audit_path.exists()
    ):
        return [
            ValidationMessage(
                check="temporal_artifact_paths",
                status="FAIL",
                detail="Required chapter 6/8 temporal artifacts are missing.",
            )
        ]

    chapter6_summary = json.loads(chapter6_summary_path.read_text(encoding="utf-8"))
    chapter6_meta = json.loads(chapter6_meta_path.read_text(encoding="utf-8"))
    chapter8_audit = pd.read_csv(chapter8_audit_path)

    selected_counts: dict[str, int] = {}
    for horizon in (1, 2):
        selected = independent_select_supervised_rows(
            panel,
            horizon,
            target_min_period=target_min,
            target_max_period=target_max,
            reference_max_period=target_max,
        )
        selected_counts[f"t{horizon}"] = int(len(selected))

    summary_counts = chapter6_summary.get("selection_rows_by_horizon", {})
    summary_count_mismatch = []
    for key, expected in selected_counts.items():
        if int(summary_counts.get(key, -1)) != int(expected):
            summary_count_mismatch.append(f"{key}:{summary_counts.get(key)}!={expected}")

    meta_selection = chapter6_meta.get("selection", {})
    meta_ok = (
        str(meta_selection.get("target_min_period")) == target_min
        and str(meta_selection.get("target_max_period")) == target_max
        and str(meta_selection.get("reference_max_period")) == target_max
    )

    expected_row_count = len(window_train_endpoints) * 2
    window_horizon_expected = {
        (f"window_until_{train_end}", horizon)
        for train_end in window_train_endpoints
        for horizon in ("t1", "t2")
    }
    observed_pairs = {
        (str(row.window_id), str(row.horizon)) for row in chapter8_audit.itertuples(index=False)
    }
    pair_mismatch = sorted(window_horizon_expected - observed_pairs)

    count_mismatches: list[str] = []
    cutoff_violations = 0
    target_window_violations = 0
    reserved_violations = 0

    for train_end in window_train_endpoints:
        validation_start = add_months(train_end, 1)
        validation_end = add_months(train_end, 6)
        for horizon in (1, 2):
            horizon_label = f"t{horizon}"
            target_min_effective = max(validation_start, target_min)
            target_max_effective = min(
                validation_end,
                target_max,
                add_months(reserved_block_start, -1),
            )

            expected_validation = panel.head(0).copy()
            if target_min_effective <= target_max_effective:
                expected_validation = independent_select_supervised_rows(
                    panel,
                    horizon,
                    reference_min_period=train_end,
                    reference_max_period=validation_end,
                    target_min_period=target_min_effective,
                    target_max_period=target_max_effective,
                )

            row_match = chapter8_audit[
                (chapter8_audit["window_id"] == f"window_until_{train_end}")
                & (chapter8_audit["horizon"] == horizon_label)
            ]
            if row_match.empty:
                count_mismatches.append(f"window_until_{train_end}/{horizon_label}:missing_row")
                continue
            row = row_match.iloc[0]

            actual_validation_rows = int(row["validation_rows"])
            expected_validation_rows = int(len(expected_validation))
            if actual_validation_rows != expected_validation_rows:
                count_mismatches.append(
                    f"window_until_{train_end}/{horizon_label}:{actual_validation_rows}!={expected_validation_rows}"
                )

            reference_before_cutoff = int(row.get("validation_reference_before_cutoff_count", 0))
            if reference_before_cutoff != 0:
                cutoff_violations += 1

            if str(row.get("check_validation_target_within_declared_window", "FAIL")) != "PASS":
                target_window_violations += 1
            if str(row.get("check_reserved_block_excluded", "FAIL")) != "PASS":
                reserved_violations += 1

    return [
        ValidationMessage(
            check="chapter6_selection_rows_reported",
            status="FAIL" if summary_count_mismatch else "PASS",
            detail=(
                "Chapter 6 summary selection-row mismatch: " + ", ".join(summary_count_mismatch)
                if summary_count_mismatch
                else (
                    "Chapter 6 summary reports corrected supervised rows "
                    f"(t1={selected_counts['t1']}, t2={selected_counts['t2']})."
                )
            ),
        ),
        ValidationMessage(
            check="chapter6_meta_temporal_bounds",
            status="PASS" if meta_ok else "FAIL",
            detail=(
                "Chapter 6 metadata target/reference bounds match active policy."
                if meta_ok
                else "Chapter 6 metadata bounds do not match active policy."
            ),
        ),
        ValidationMessage(
            check="chapter8_window_horizon_grid",
            status=(
                "PASS"
                if len(chapter8_audit) == expected_row_count and not pair_mismatch
                else "FAIL"
            ),
            detail=(
                f"Chapter 8 rows={len(chapter8_audit)} expected={expected_row_count}; "
                f"missing_pairs={pair_mismatch}."
            ),
        ),
        ValidationMessage(
            check="chapter8_validation_row_counts",
            status="PASS" if not count_mismatches else "FAIL",
            detail=(
                "Chapter 8 validation-row counts match independent recomputation."
                if not count_mismatches
                else "Chapter 8 validation-row mismatches: " + ", ".join(count_mismatches)
            ),
        ),
        ValidationMessage(
            check="chapter8_cutoff_and_reserved_guards",
            status=(
                "PASS"
                if (
                    cutoff_violations == 0
                    and target_window_violations == 0
                    and reserved_violations == 0
                )
                else "FAIL"
            ),
            detail=(
                "Chapter 8 guard counters: "
                f"reference_before_cutoff={cutoff_violations}, "
                f"target_window_failures={target_window_violations}, "
                f"reserved_failures={reserved_violations}."
            ),
        ),
    ]


def write_report(path: Path, report: dict[str, Any]) -> None:
    """Write JSON report to disk.

    Args:
        path: Output path.
        report: Report payload.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        required=True,
        help="Baseline JSON path for read/compare operations.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where readiness report artifacts will be written.",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Write (or overwrite) baseline snapshot at --baseline before validation.",
    )
    return parser.parse_args()


def main() -> int:
    """Run readiness validation CLI.

    Returns:
        Exit code.
    """

    args = parse_args()
    root = resolve_repo_root()

    current = capture_snapshot(root)
    if args.write_baseline:
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(
            json.dumps(current, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    if not args.baseline.exists():
        report: dict[str, Any] = {
            "generated_utc": utc_now_iso(),
            "status": "BLOCKED",
            "reason": f"Baseline file not found: {args.baseline}",
            "messages": [],
        }
        write_report(args.output_dir / "readiness_report.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    active_policy = current["coverage"]["model_eligibility_policy"]

    messages = []
    messages.extend(compare_snapshot(baseline, current))
    messages.extend(validate_execution_manifest_hashes(root))
    messages.extend(validate_notebook_artifact_manifest(root))
    messages.extend(validate_notebook_surface(root))
    messages.extend(validate_scope_reporting(root))
    messages.extend(validate_current_endemic_channel_integrity(root))
    messages.extend(validate_temporal_selector_consistency(root, active_policy))
    messages.extend(validate_temporal_artifact_selections(root, active_policy))

    summary = statuses_summary(messages)
    final_status = "FAIL" if summary.get("FAIL", 0) > 0 else "PASS"

    report = {
        "generated_utc": utc_now_iso(),
        "baseline_path": str(args.baseline),
        "status": final_status,
        "summary": summary,
        "messages": [message.__dict__ for message in messages],
        "current": {
            "git": current["git"],
            "coverage": {
                "manifest": current["coverage"]["manifest"],
                "model_eligibility_policy": current["coverage"]["model_eligibility_policy"],
                "edge_contribution_outside_backed_interval": current["coverage"][
                    "edge_contribution_outside_backed_interval"
                ],
            },
            "panel": {
                "rows": current["panel"]["rows"],
                "column_count": current["panel"]["column_count"],
            },
        },
        "limitations": {
            "retrospective_only": current["limitations"]["retrospective_only"],
        },
    }

    write_report(args.output_dir / "readiness_report.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    return 0 if final_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
