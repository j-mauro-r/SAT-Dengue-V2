"""Frozen EXP03 2024/consumed-2025 transport, without fitting or selection.

Supplied observations are prepared as of each forecast origin. This module reads
only verified native model artifacts; it has no scientific source reader, model
fit, calibration fit, threshold selector or tracking client.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03_evaluation import group_summary, metrics
from sat_dengue.experiments.exp03_features import exposure_table, prepare
from sat_dengue.experiments.exp03_persistence import _load_terminal, consumed_2025_benchmark
from sat_dengue.experiments.exp03_revision import cell_grid, validate_design

ZERO_COUNTERS = {
    "model_fits": 0,
    "preparer_fits": 0,
    "calibrator_fits": 0,
    "searches": 0,
    "threshold_selections": 0,
}


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.astype(object).where(pd.notna(frame), None).to_dict(orient="records")


def _profile_membership(profiles: dict[str, Any]) -> dict[str, str]:
    if "membership" in profiles:
        membership = profiles["membership"]
        result = {str(r["municipality_code"]): str(r["transmission_profile"]) for r in membership}
        if len(result) != len(membership):
            raise ValueError("Duplicate frozen historical profile membership")
        return result
    return {str(k): str(v) for k, v in profiles.items()}


def evaluate_benchmark(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    design: dict[str, Any],
    terminal_root: Path,
    coverage_metadata: dict[str, Any],
    expected_manifest_sha256: str,
) -> dict[str, Any]:
    """Evaluate all declared terminal cells, with 2025 permanently descriptive.

    Missing coverage/maturity provenance yields explicit not-evaluable records
    for every terminal cell and year. It never triggers a fit or data acquisition.
    """
    validate_design(design)
    terminal = [s for s in cell_grid(design) if s["window"] == "stress_2024"]
    return _evaluate_frozen_grid(
        panel,
        contract,
        design,
        terminal_root,
        coverage_metadata,
        expected_manifest_sha256,
        terminal,
    )


def _evaluate_frozen_grid(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    design: dict[str, Any],
    terminal_root: Path,
    coverage_metadata: dict[str, Any],
    expected_manifest_sha256: str,
    terminal_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Implementation seam: small generated grids can exercise native inference.

    Production callers use evaluate_benchmark, which supplies the complete grid.
    No omitted terminal cell or replacement fit is admitted here either.
    """
    manifest, cells, identity = _load_terminal(Path(terminal_root))
    if identity != expected_manifest_sha256:
        raise ValueError("Terminal freeze manifest changed before transport")
    expected = {digest(s): s for s in terminal_specs}
    if len(expected) != len(terminal_specs) or set(expected) != set(cells):
        raise ValueError("Benchmark requires every declared terminal cell; no shortlist")
    for cell_id, cell in cells.items():
        spec = expected[cell_id]
        if any(cell.metadata.get(k) != v for k, v in spec.items()):
            raise ValueError("Frozen cell metadata differs from declared terminal grid")
        if cell.predictor.columns != design["variants"][spec["variant"]]:
            raise ValueError("Frozen predictor recipes differ from declared variant")
        if cell.predictor.family != spec["family"]:
            raise ValueError("Frozen model family differs from declared terminal cell")
        if cell.provenance.get("matrix_sha256") not in (None, digest(design)):
            raise ValueError("Frozen matrix identity differs from benchmark design")
    result: dict[str, Any] = {
        "schema": "exp03-transport-v2",
        "status": "not_evaluable",
        "reason": None,
        "terminal_cell_count": len(cells),
        "manifest_sha256": identity,
        "execution_counters": dict(ZERO_COUNTERS),
        "transport_2024_2025": [],
        "benchmark_predictions": [],
        "performance_by_group": [],
        "exposure_by_cluster": [],
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "used_for_selection": False,
        "development_uncertainty": "excluded",
    }
    governed = all(
        coverage_metadata.get(k)
        for k in ("governed_coverage", "maturity_verified", "provenance_sha256")
    )
    if not governed:
        reason = "governed_coverage_or_maturity_unverified"
        result["reason"] = reason
        for cell_id, spec in expected.items():
            for year in (2024, 2025):
                result["transport_2024_2025"].append(
                    {
                        **spec,
                        "cell_id": cell_id,
                        "target_year": year,
                        "status": "not_evaluable",
                        "reason": reason,
                        "target_months": [],
                        "full_year_coverage": False,
                        "artifact_identity": manifest["cells"][cell_id]["identity"],
                        "evidence_type": "retrospective_stress"
                        if year == 2024
                        else "consumed_retrospective_benchmark",
                        **ZERO_COUNTERS,
                    }
                )
        return result
    prepared: dict[int, pd.DataFrame] = {}
    dates: dict[int, pd.DataFrame] = {}
    for horizon in sorted({s["horizon"] for s in terminal_specs}):
        all_rows = prepare(panel, contract, horizon, allow_benchmark=True)
        source_dates = all_rows.attrs["source_months"]
        selected = all_rows.loc[
            all_rows.target_month.between("2024-01", "2025-12") & all_rows.year_month.ge("2023-12")
        ].copy()
        selected.attrs = {}
        selected["window"] = "stress_2024"
        selected["role"] = "evaluation"
        selected["common_predictors_available"] = selected[design["predictors"]].notna().all(axis=1)
        prepared[horizon] = selected
        dates[horizon] = source_dates.loc[selected.index, design["predictors"]]
    frames: dict[str, pd.DataFrame] = {}
    native_frames: dict[str, pd.DataFrame] = {}
    ledgers: dict[str, pd.DataFrame] = {}
    for cell_id, spec in expected.items():
        cell = cells[cell_id]
        frame = prepared[spec["horizon"]].copy()
        frame["transmission_profile"] = frame.municipality_code.map(
            _profile_membership(cell.profiles)
        ).fillna("profile_unavailable")
        monitored, eligible = frame.monitored, frame.eligible_at_t.fillna(False)
        common = monitored & eligible & frame.common_predictors_available
        frame["benchmark_common_cohort"] = common
        # The inference interface receives no outcome labels or evaluation strata.
        columns = list(
            dict.fromkeys(
                [
                    "municipality_code",
                    "year_month",
                    "target_month",
                    "eligible_at_t",
                    *cell.predictor.columns,
                ]
            )
        )
        scored = frame.loc[common, columns].copy()
        scored["latest_source_month"] = dates[spec["horizon"]].loc[scored.index].max(axis=1)
        frames[cell_id] = scored
        native_frames[cell_id] = frame
        ledgers[cell_id] = exposure_table({"evaluation": frame})
    # Exactly one complete-grid inference call. All fitting/selection is absent.
    inference = consumed_2025_benchmark(
        Path(terminal_root),
        frames,
        coverage_metadata,
        expected_manifest_sha256=expected_manifest_sha256,
    )
    if inference["status"] != "evaluable" or set(inference["execution_counters"].values()) != {0}:
        raise ValueError("Frozen inference failed or reported nonzero execution counters")
    for cell_id, spec in expected.items():
        cell, frame, ledger = cells[cell_id], native_frames[cell_id], ledgers[cell_id]
        scored = inference["predictions"][cell_id]
        frame["raw_score"], frame["score"] = np.nan, np.nan
        frame["alert"] = False
        frame["unsupported"] = False
        for column in ("raw_score", "score", "alert", "unsupported"):
            frame.loc[scored.index, column] = scored[column]
        frame["abstention"] = frame.eligible_at_t.fillna(False) & ~frame.benchmark_common_cohort
        frame["coverage_status"] = np.select(
            [
                ~frame.monitored,
                ~frame.eligible_at_t.fillna(False),
                ~frame.common_predictors_available,
            ],
            ["unknown_source_or_outcome", "ineligible_Y_T", "missing_common_predictors"],
            default="common_complete_case",
        )
        for key, value in spec.items():
            if key != "window":
                frame[key] = value
        frame["cell_id"] = cell_id
        frame["threshold"] = cell.threshold
        frame["artifact_identity"] = manifest["cells"][cell_id]["identity"]
        frame["evidence_type"] = np.where(
            frame.target_year.eq(2024), "retrospective_stress", "consumed_retrospective_benchmark"
        )
        frame["used_for_selection"] = False
        result["benchmark_predictions"].extend(_records(frame))
        result["exposure_by_cluster"].extend(_records(ledger.assign(cell_id=cell_id)))
        months = {
            year: set(
                frame.loc[frame.target_year.eq(year) & frame.monitored, "target_month"].str[-2:]
            )
            for year in (2024, 2025)
        }
        common_months = sorted(months[2024] & months[2025])

        def summarize(
            mask: pd.Series,
            year: int | str,
            view: str,
            *,
            frame: pd.DataFrame = frame,
            spec: dict[str, Any] = spec,
            cell_id: str = cell_id,
            common_months: list[str] = common_months,
            cell: Any = cell,
        ) -> dict[str, Any]:
            full = frame.loc[mask].copy()
            full.attrs = {}
            selected = full.loc[full.benchmark_common_cohort].copy()
            selected.attrs = {}
            selected.attrs["covered_onsets"] = int(full.loc[full.monitored, "onset_target"].sum())
            selected.attrs["eligible_onsets"] = int(
                full.loc[full.monitored & full.eligible_at_t.fillna(False), "onset_target"].sum()
            )
            local = exposure_table({"evaluation": full})
            d = float(local.monitored_exposure.sum()) if not local.empty else 0.0
            e = float(local.eligible_exposure.sum()) if not local.empty else 0.0
            metric = metrics(selected, selected.alert, d, e, selected.score, spec["objective"])
            metric["raw_probability"] = metrics(
                selected, selected.alert, d, e, selected.raw_score, spec["objective"]
            )
            actual = sorted(full.loc[full.monitored, "target_month"].unique())
            return {
                **spec,
                "cell_id": cell_id,
                "target_year": year,
                "view": view,
                "status": "evaluable" if len(selected) else "not_evaluable",
                "reason": None if len(selected) else "no_common_eligible_predictions",
                "target_months": actual,
                "common_calendar_months": common_months,
                "full_year_coverage": len(actual) == 12 if isinstance(year, int) else None,
                "monitored_months": int(round(d * 12)),
                "eligible_months": int(round(e * 12)),
                "common_months": len(selected),
                "abstentions": int(full.abstention.sum()),
                "eligible_onsets_excluded": selected.attrs["eligible_onsets"]
                - metric["real_onsets"],
                "artifact_identity": manifest["cells"][cell_id]["identity"],
                "manifest_sha256": identity,
                "evidence_type": "retrospective_stress"
                if year == 2024
                else "consumed_retrospective_benchmark"
                if year == 2025
                else "descriptive_consumed_2024_2025_context",
                "used_for_selection": False,
                "development_uncertainty": "excluded",
                "B_primary": cell.budget,
                "metrics": metric,
                **ZERO_COUNTERS,
            }

        for year in (2024, 2025):
            annual_mask = frame.target_year.eq(year)
            result["transport_2024_2025"].append(summarize(annual_mask, year, "annual"))
            common_mask = annual_mask & frame.target_month.str[-2:].isin(common_months)
            result["transport_2024_2025"].append(
                summarize(common_mask, year, "common_calendar_months")
            )
            subset = frame.loc[annual_mask & frame.benchmark_common_cohort].copy()
            subset.attrs = {}
            local = ledger.loc[ledger.target_year.eq(year)]
            if not local.empty:
                groups = group_summary(
                    subset, subset.alert, local, score=subset.score, objective=spec["objective"]
                )
                for row in groups["groups"]:
                    result["performance_by_group"].append(
                        {
                            **spec,
                            "cell_id": cell_id,
                            "target_year": year,
                            "evidence_type": "retrospective_stress"
                            if year == 2024
                            else "consumed_retrospective_benchmark",
                            "used_for_selection": False,
                            **row,
                        }
                    )
        result["transport_2024_2025"].append(
            summarize(pd.Series(True, index=frame.index), "2024-2025", "count_pooled_descriptive")
        )
    result.update(
        status="evaluable",
        reason=None,
        identities_verified_before_after=inference["identities_verified_before_after"],
    )
    return result
