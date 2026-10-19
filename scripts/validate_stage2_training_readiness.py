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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

RESERVED_BLOCK_START = "2025-01"
DEVELOPMENT_END = "2024-12"
ALLOWED_ADDITIVE_PANEL_COLUMNS = {
    "p25_canal_t",
    "p50_canal_t",
    "p75_canal_t",
    "zona_canal_t",
}


@dataclass(frozen=True)
class ValidationMessage:
    """Structured validation message.

    Args:
        check: Check identifier.
        status: PASS, FAIL, BLOCKED or UNVERIFIED.
        detail: Human-readable detail.
    """

    check: str
    status: str
    detail: str


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


def period_to_yyyymm(value: str) -> str:
    """Normalize a period-like value into YYYY-MM.

    Args:
        value: Input period text.

    Returns:
        Normalized period string.
    """

    return str(pd.Period(str(value), freq="M"))


def add_months(period: str, months: int) -> str:
    """Shift YYYY-MM by a month offset.

    Args:
        period: Base period.
        months: Signed month shift.

    Returns:
        Shifted period.
    """

    return str(pd.Period(period, freq="M") + months)


def panel_y_p75_signature(panel: pd.DataFrame) -> str:
    """Compute stable signature over existing Y/P75 columns.

    Args:
        panel: Panel dataframe.

    Returns:
        SHA-256 over a canonical CSV payload for Y/P75 columns.
    """

    columns = [
        "municipality_code",
        "year_month",
        "target_period_t1",
        "target_period_t2",
        "p75_t1",
        "p75_t2",
        "y_evaluable_t1",
        "y_evaluable_t2",
        "y_status_t1",
        "y_status_t2",
        "y_t1",
        "y_t2",
    ]
    available = [column for column in columns if column in panel.columns]
    payload = panel.sort_values(["municipality_code", "year_month"])[available].to_csv(index=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


def compute_edge_contribution(
    panel: pd.DataFrame,
    backed_start: str,
    backed_end: str,
) -> dict[str, Any]:
    """Count in-coverage rows outside backed year metadata interval.

    Args:
        panel: Monthly panel.
        backed_start: Backed interval start YYYY-MM.
        backed_end: Backed interval end YYYY-MM.

    Returns:
        Edge contribution summary.
    """

    scoped = panel.copy()
    scoped["year_month"] = scoped["year_month"].astype(str).map(period_to_yyyymm)
    in_coverage = scoped["in_epi_coverage"].fillna(False)
    out_of_backed = (scoped["year_month"] < backed_start) | (scoped["year_month"] > backed_end)
    edge = scoped[in_coverage & out_of_backed]

    dengue_sum = float(
        pd.to_numeric(
            edge.get("dengue_notifications_count"),
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )
    dengue_grave_sum = float(
        pd.to_numeric(
            edge.get("dengue_grave_notifications_count"),
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )
    y_eval_t1 = int(edge.get("y_evaluable_t1", pd.Series(dtype=bool)).fillna(False).sum())
    y_eval_t2 = int(edge.get("y_evaluable_t2", pd.Series(dtype=bool)).fillna(False).sum())

    return {
        "backed_interval": {"start": backed_start, "end": backed_end},
        "rows": int(len(edge)),
        "months": sorted(edge["year_month"].unique().tolist()),
        "dengue_count_sum": dengue_sum,
        "dengue_grave_count_sum": dengue_grave_sum,
        "y_evaluable_t1_rows": y_eval_t1,
        "y_evaluable_t2_rows": y_eval_t2,
    }


def build_model_eligibility_policy(
    notification_min_year: int,
    notification_max_year: int,
    *,
    reserved_block_start: str = RESERVED_BLOCK_START,
) -> dict[str, Any]:
    """Build conservative model-eligibility policy from year metadata.

    Args:
        notification_min_year: Minimum notification year in source metadata.
        notification_max_year: Maximum notification year in source metadata.
        reserved_block_start: Reserved holdout start month.

    Returns:
        Eligibility policy dictionary.
    """

    backed_start = f"{notification_min_year:04d}-01"
    backed_end = f"{notification_max_year:04d}-12"
    earliest_target_with_5y_history = add_months(backed_start, 12 * 5)
    latest_target_before_reserved = add_months(reserved_block_start, -1)

    target_end = min(backed_end, latest_target_before_reserved)
    earliest_cutoff_t1 = add_months(earliest_target_with_5y_history, -1)
    earliest_cutoff_t2 = add_months(earliest_target_with_5y_history, -2)

    return {
        "source_coverage_backed_by_notification_year": {
            "start": backed_start,
            "end": backed_end,
        },
        "development_target_eligibility": {
            "target_min": earliest_target_with_5y_history,
            "target_max": target_end,
            "reserved_block_start": reserved_block_start,
            "rationale": (
                "Conservative modeling eligibility: require target periods fully inside "
                "notification-year-backed interval, below reserved block, and with five same-month "
                "historical observations."
            ),
        },
        "earliest_cutoff_with_eligible_target": {
            "t1": earliest_cutoff_t1,
            "t2": earliest_cutoff_t2,
        },
        "important_distinctions": {
            "coverage": "Backed interval from source notification-year metadata.",
            "history_sufficiency": "Per-row five-year same-month availability for each horizon.",
            "operational_availability": (
                "Retrospective consolidated data do not prove real-time historical "
                "as-of availability."
            ),
        },
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

    baseline_snapshot = {
        "captured_utc": utc_now_iso(),
        "git": {
            "branch": run_git(root, "branch", "--show-current"),
            "revision": run_git(root, "rev-parse", "HEAD"),
            "dirty_paths": run_git(root, "status", "--short"),
        },
        "inputs": {
            "fingerprints": manifest["input_fingerprints_before"],
            "source_rows": manifest["reconciliation"]["source_rows"],
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

    return messages


def validate_notebook_surface(root: Path) -> list[ValidationMessage]:
    """Validate notebook structural constraints and display cardinality.

    Args:
        root: Repository root.

    Returns:
        Validation messages.
    """

    notebook_path = root / "notebooks/03_consolidated_dataset_pipeline.ipynb"
    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = payload.get("cells", [])

    try:
        visual_assets = load_visual_assets_module(root)
        code_only = visual_assets.assert_notebook_code_only(notebook_path)
    except (RuntimeError, FileNotFoundError):
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

    code_sources = [
        "\n".join(cell.get("source", [])) for cell in cells if cell.get("cell_type") == "code"
    ]
    combined = "\n\n".join(code_sources)
    figure_count = combined.count("plt.show()")
    table_count = combined.count("display(")

    figure_status = "PASS" if figure_count == 2 else "FAIL"
    table_status = "PASS" if table_count == 2 else "FAIL"

    return [
        code_only_msg,
        ValidationMessage(
            check="notebook_figures_count",
            status=figure_status,
            detail=f"Found {figure_count} plt.show() calls (expected 2).",
        ),
        ValidationMessage(
            check="notebook_tables_count",
            status=table_status,
            detail=f"Found {table_count} display(...) calls (expected 2).",
        ),
    ]


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


def validate_temporal_selector_consistency(root: Path) -> list[ValidationMessage]:
    """Validate horizon target-period consistency in panel-level labels.

    Args:
        root: Repository root.

    Returns:
        Validation messages.
    """

    visual_assets = load_visual_assets_module(root)
    panel_path = root / "data/processed/panel_mensual_dengue_clima.csv"
    panel = pd.read_csv(panel_path)
    panel["year_month"] = panel["year_month"].astype(str).map(period_to_yyyymm)

    t1 = panel[panel["y_evaluable_t1"].fillna(False)]
    t2 = panel[panel["y_evaluable_t2"].fillna(False)]

    t1_reserved = int((t1["target_period_t1"].astype(str) >= RESERVED_BLOCK_START).sum())
    t2_reserved = int((t2["target_period_t2"].astype(str) >= RESERVED_BLOCK_START).sum())

    selected_t1 = visual_assets.select_supervised_rows(
        panel,
        1,
        reference_max_period=DEVELOPMENT_END,
        target_max_period=DEVELOPMENT_END,
    )
    selected_t2 = visual_assets.select_supervised_rows(
        panel,
        2,
        reference_max_period=DEVELOPMENT_END,
        target_max_period=DEVELOPMENT_END,
    )

    selected_t1_violations = int(
        (selected_t1["target_period_t1"].astype(str) >= RESERVED_BLOCK_START).sum()
    )
    selected_t2_violations = int(
        (selected_t2["target_period_t2"].astype(str) >= RESERVED_BLOCK_START).sum()
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
            status="PASS" if selected_t1_violations == 0 else "FAIL",
            detail=(
                "Horizon T+1 supervised selector reserved-target violations: "
                f"{selected_t1_violations}"
            ),
        ),
        ValidationMessage(
            check="supervised_selector_reserved_t2",
            status="PASS" if selected_t2_violations == 0 else "FAIL",
            detail=(
                "Horizon T+2 supervised selector reserved-target violations: "
                f"{selected_t2_violations}"
            ),
        ),
    ]
    return messages


def write_report(path: Path, report: dict[str, Any]) -> None:
    """Write JSON report to disk.

    Args:
        path: Output path.
        report: Report payload.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def statuses_summary(messages: list[ValidationMessage]) -> dict[str, int]:
    """Count statuses in validation messages."""

    counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "UNVERIFIED": 0}
    for message in messages:
        counts[message.status] = counts.get(message.status, 0) + 1
    return counts


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
        report = {
            "generated_utc": utc_now_iso(),
            "status": "BLOCKED",
            "reason": f"Baseline file not found: {args.baseline}",
            "messages": [],
        }
        write_report(args.output_dir / "readiness_report.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))

    messages = []
    messages.extend(compare_snapshot(baseline, current))
    messages.extend(validate_notebook_surface(root))
    messages.extend(validate_scope_reporting(root))
    messages.extend(validate_temporal_selector_consistency(root))

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
