from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/interim/stage2_derived_recompute_reconciliation"
PANEL = ROOT / "data/interim/stage2_panel_review"
LEGACY = ROOT / "data/interim/stage2_monthly_sensitivity_associations"

CLIMATE_VARS = [
    "rain_mm_day",
    "temp_mean_c",
    "dewpoint_mean_c",
    "soil_water_l1_mean",
    "surface_runoff_mm_day",
    "total_evaporation_mm_day_ecmwf",
    "wind_u_mean_ms",
    "wind_v_mean_ms",
    "solar_radiation_mj_m2_day",
]


@dataclass
class Snapshot:
    label: str
    root: Path
    panel_dir: Path
    legacy_dir: Path


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dir_identity(path: Path) -> dict[str, Any]:
    files = []
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = file_path.relative_to(path)
        files.append(
            {
                "path": str(rel),
                "bytes": file_path.stat().st_size,
                "sha256": sha256(file_path),
            }
        )
    digest = hashlib.sha256()
    for row in files:
        digest.update(f"{row['path']}:{row['bytes']}:{row['sha256']}\n".encode())
    return {"files": files, "file_count": len(files), "aggregate_digest": digest.hexdigest()}


def inventory_dependencies() -> dict[str, Any]:
    inventory = {
        "generated_utc": now_utc(),
        "inventory_complete": True,
        "executed_scripts": [
            {
                "path": "scripts/stage2_panel_review.py",
                "phases": ["panel", "analysis", "rules", "validate"],
                "climate_dependency": (
                    "direct monthly climate aggregation and downstream associations"
                ),
            }
        ],
        "stored_outputs": [
            "data/interim/stage2_panel_review/climate_monthly.csv",
            "data/interim/stage2_panel_review/monthly_panel_s1.csv",
            "data/interim/stage2_panel_review/monthly_panel_s2.csv",
            "data/interim/stage2_panel_review/monthly_panel_s3.csv",
            "data/interim/stage2_panel_review/associations_raw.csv",
            "data/interim/stage2_panel_review/associations_controlled.csv",
            "data/interim/stage2_panel_review/associations_raw_comparison.csv",
            "data/interim/stage2_panel_review/associations_controlled_comparison.csv",
            "data/interim/stage2_panel_review/associations_stability_summary.csv",
            "data/interim/stage2_panel_review/review_summary.json",
            "data/interim/stage2_panel_review/metadata.json",
        ],
        "historical_outputs_not_rerun_in_this_task": [
            {
                "path": "data/interim/stage2_monthly_sensitivity_associations/",
                "status": "retained_historical_reference",
                "reason": (
                    "Legacy PLAN_005 outputs; current Stage 2 review "
                    "uses stage2_panel_review pipeline."
                ),
            }
        ],
        "notebooks_and_docs_impacted": [
            "notebooks/02_stage2_monthly_sensitivity_associations.ipynb",
            "docs/product/stage-2/DATA-03-panel-review.md",
            "docs/product/stage-2/DATA-04-retrospective-use-rules.md",
        ],
        "limits": [
            (
                "Notebook cells were not re-executed in this task; notebook "
                "references are documented as impacted surface."
            ),
            (
                "Historical outputs under "
                "stage2_monthly_sensitivity_associations are preserved "
                "as historical and may remain stale for "
                "post-incorporation interpretation."
            ),
        ],
    }
    write_json(OUT / "inventory_climate_dependencies.json", inventory)
    return inventory


def execution_order() -> dict[str, Any]:
    payload = {
        "generated_utc": now_utc(),
        "required_phase_order": ["panel", "analysis", "rules", "validate"],
        "source": "scripts/stage2_panel_review.py main() dispatch",
        "validate_rebuilds_outputs": False,
        "notes": (
            "validate checks existing artifacts and source-hash policy, "
            "but does not rebuild panel/analysis/rules outputs by itself."
        ),
    }
    write_json(OUT / "execution_order_and_phases.json", payload)
    return payload


def make_snapshot(label: str) -> Snapshot:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = OUT / "snapshots" / f"{label}_{stamp}_{uuid.uuid4().hex[:8]}"
    if target.exists():
        raise RuntimeError(f"Snapshot path collision: {target}")
    target.mkdir(parents=True, exist_ok=False)

    panel_copy = target / "stage2_panel_review"
    legacy_copy = target / "stage2_monthly_sensitivity_associations"
    shutil.copytree(PANEL, panel_copy)
    shutil.copytree(LEGACY, legacy_copy)
    return Snapshot(label=label, root=target, panel_dir=panel_copy, legacy_dir=legacy_copy)


def snapshot_identity(snapshot: Snapshot) -> dict[str, Any]:
    panel_identity = dir_identity(snapshot.panel_dir)
    legacy_identity = dir_identity(snapshot.legacy_dir)
    return {
        "generated_utc": now_utc(),
        "label": snapshot.label,
        "snapshot_root": str(snapshot.root.relative_to(ROOT)),
        "snapshots": {
            "stage2_panel_review": {
                "path": str(snapshot.panel_dir.relative_to(ROOT)),
                **panel_identity,
            },
            "stage2_monthly_sensitivity_associations": {
                "path": str(snapshot.legacy_dir.relative_to(ROOT)),
                **legacy_identity,
            },
        },
    }


def run_panel_phases() -> dict[str, Any]:
    cmd = [
        [
            str(ROOT / ".venv/bin/python"),
            "scripts/stage2_panel_review.py",
            "--phase",
            "panel",
            "--authorized-plan",
            "PLAN_011_manifest_traceability_and_derived_recompute",
            "--transition-reason",
            "Authorized post-January-2020 derived recomputation",
            "--transition-evidence-path",
            "data/interim/stage2_manifest_traceability/conservation_verification.json",
            "--transition-backup-reference",
            "data/interim/stage2_january_2020_incorporation/backups/google_earth_engine.pre_incorp_jan2020.20261019T011733Z.e853900e.csv",
        ],
        [str(ROOT / ".venv/bin/python"), "scripts/stage2_panel_review.py", "--phase", "analysis"],
        [str(ROOT / ".venv/bin/python"), "scripts/stage2_panel_review.py", "--phase", "rules"],
        [str(ROOT / ".venv/bin/python"), "scripts/stage2_panel_review.py", "--phase", "validate"],
    ]

    executed = []
    for argv in cmd:
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        executed.append(
            {
                "command": argv,
                "exit_code": proc.returncode,
                "stdout_tail": proc.stdout.splitlines()[-20:],
                "stderr_tail": proc.stderr.splitlines()[-20:],
            }
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(argv)}")

    payload = {"generated_utc": now_utc(), "executed": executed}
    write_json(OUT / "recompute_execution_log.json", payload)
    return payload


def _scenario_totals(panel_path: Path) -> dict[str, int]:
    frame = pd.read_csv(panel_path)
    return {
        "rows": int(len(frame)),
        "dengue_recorded_count": int(frame["dengue_recorded_count"].sum()),
        "severe_recorded_count": int(frame["severe_recorded_count"].sum()),
    }


def _associations_delta(before_path: Path, after_path: Path, key_cols: list[str]) -> dict[str, Any]:
    before = pd.read_csv(before_path)
    after = pd.read_csv(after_path)
    merged = before.merge(
        after, on=key_cols, how="outer", suffixes=("_before", "_after"), indicator=True
    )
    comparable = merged[merged["_merge"].eq("both")].copy()
    changed_n_obs = int((comparable["n_obs_before"] != comparable["n_obs_after"]).sum())
    changed_support = int((comparable["support_before"] != comparable["support_after"]).sum())
    changed_rho = int((comparable["rho_before"] != comparable["rho_after"]).sum())
    return {
        "before_rows": int(len(before)),
        "after_rows": int(len(after)),
        "row_membership": merged["_merge"].value_counts().to_dict(),
        "changed_n_obs": changed_n_obs,
        "changed_support": changed_support,
        "changed_rho": changed_rho,
    }


def compare_outputs(before: Snapshot, after: Snapshot) -> dict[str, Any]:
    before_panel = before.panel_dir
    after_panel = after.panel_dir

    climate_before = pd.read_csv(before_panel / "climate_monthly.csv")
    climate_after = pd.read_csv(after_panel / "climate_monthly.csv")
    before_non_jan = climate_before[climate_before["year_month"] != "2020-01"].sort_values(
        ["mun_full", "year_month"]
    )
    after_non_jan = climate_after[climate_after["year_month"] != "2020-01"].sort_values(
        ["mun_full", "year_month"]
    )
    non_jan_equal = before_non_jan.reset_index(drop=True).equals(
        after_non_jan.reset_index(drop=True)
    )

    jan = climate_after[climate_after["year_month"] == "2020-01"].copy()
    complete_variables = 0
    for var in CLIMATE_VARS:
        valid_col = f"{var}_valid_days"
        if valid_col in jan.columns and jan[valid_col].eq(31).all():
            complete_variables += 1

    scenario_keys = {
        "S1": "monthly_panel_s1.csv",
        "S2": "monthly_panel_s2.csv",
        "S3": "monthly_panel_s3.csv",
    }
    epi_conservation = {
        "dengue_counts_unchanged": True,
        "severe_counts_unchanged": True,
        "by_scenario": {},
    }
    for name, filename in scenario_keys.items():
        before_totals = _scenario_totals(before_panel / filename)
        after_totals = _scenario_totals(after_panel / filename)
        epi_conservation["by_scenario"][name] = {
            "before": before_totals,
            "after": after_totals,
        }
        if before_totals["dengue_recorded_count"] != after_totals["dengue_recorded_count"]:
            epi_conservation["dengue_counts_unchanged"] = False
        if before_totals["severe_recorded_count"] != after_totals["severe_recorded_count"]:
            epi_conservation["severe_counts_unchanged"] = False

    raw_delta = _associations_delta(
        before_panel / "associations_raw.csv",
        after_panel / "associations_raw.csv",
        ["scenario", "level", "feature", "horizon"],
    )
    controlled_delta = _associations_delta(
        before_panel / "associations_controlled.csv",
        after_panel / "associations_controlled.csv",
        ["scenario", "level", "feature", "horizon", "controls"],
    )

    changed_files = []
    for path in sorted(p for p in before_panel.rglob("*") if p.is_file()):
        rel = path.relative_to(before_panel)
        other = after_panel / rel
        if not other.exists():
            changed_files.append({"path": str(rel), "change": "missing_in_after"})
            continue
        if sha256(path) != sha256(other):
            changed_files.append({"path": str(rel), "change": "content_changed"})

    payload = {
        "generated_utc": now_utc(),
        "january_coverage": {
            "municipalities": int(jan["mun_full"].nunique()),
            "days": int(jan["climate_days"].max()) if not jan.empty else 0,
            "complete_variables": complete_variables,
        },
        "epidemiological_conservation": epi_conservation,
        "climate_non_january_aggregate_equal": bool(non_jan_equal),
        "associations_delta": {
            "raw": raw_delta,
            "controlled": controlled_delta,
            "interpretation": (
                "Differences in n_obs/support/rho are expected when newly "
                "available January climate data propagates through horizons "
                "and moving windows."
            ),
        },
        "changed_panel_output_files": changed_files,
        "outputs_still_historical_or_stale": [
            {
                "path": "data/interim/stage2_monthly_sensitivity_associations/",
                "status": "historical_reference_not_recomputed_in_this_task",
            }
        ],
    }
    write_json(OUT / "derived_comparison_summary.json", payload)
    return payload


def run() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inventory_dependencies()
    execution_order()

    before = make_snapshot("before")
    before_id = snapshot_identity(before)
    write_json(OUT / "before_snapshot_identity.json", before_id)

    run_panel_phases()

    after = make_snapshot("after")
    after_id = snapshot_identity(after)
    write_json(OUT / "after_snapshot_identity.json", after_id)

    comparison = compare_outputs(before, after)
    print(
        json.dumps(
            {
                "status": "ok",
                "january_coverage": comparison["january_coverage"],
                "epi_conservation": comparison["epidemiological_conservation"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["run"], required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "run":
        run()


if __name__ == "__main__":
    main()
