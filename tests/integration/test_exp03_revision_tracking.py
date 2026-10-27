"""Generated structural evidence only; no private reads or persistent MLflow writes."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03_revision import build_design
from sat_dengue.tracking import exp03


@pytest.fixture
def revision(monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path("docs/product/experiments/EXP03_feature_ablation/protocol.json")
    p = json.loads(path.read_text())
    if p["design"].get("revision") != "scope-v2":
        p["design"] = build_design(p["design"])
    monkeypatch.setattr(exp03, "load_protocol", lambda: p)
    children = []
    for variant, objective, family, horizon, window in sorted(exp03.expected_grid(p["design"])):
        columns = p["design"]["variants"][variant]
        children.append(
            {
                "variant": variant,
                "objective": objective,
                "family": family,
                "horizon": horizon,
                "window": window,
                "cell_id": digest(
                    {
                        "variant": variant,
                        "objective": objective,
                        "family": family,
                        "horizon": horizon,
                        "window": window,
                    }
                ),
                "status": "non_evaluable",
                "model_fitted": False,
                "reason": "generated metadata only",
                "number_of_variables": len(columns),
                "predictors_sha256": digest(columns),
                "cohort_sha256": "a" * 64,
                "role_sha256": {"train": "b" * 64},
                "coverage": {},
                "metrics": {},
                "seed": 42,
                "evidence_type": "synthetic_generated_data",
            }
        )
    result = {
        "schema": "exp03-result-v2",
        "experiment_id": "EXP03",
        "synthetic": True,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "children": children,
        "contrasts": [],
        "real_model_fits": 0,
        "real_preparer_refits": 0,
        "calibrator_fits": 0,
        "synthetic_interface_fits": 0,
    }
    return result, {"protocol_sha256": digest(p)}


def test_objective_aware_grid_and_counter_admission(revision: tuple[dict, dict]) -> None:
    result, provenance = revision
    exp03.validate_result(result, provenance)
    assert len(result["children"]) == 408
    assert sum(c["objective"] == "excess" for c in result["children"]) == 24
    assert not any(c["objective"] == "excess" and c["horizon"] == 1 for c in result["children"])
    duplicate = copy.deepcopy(result)
    duplicate["children"][-1] = copy.deepcopy(duplicate["children"][0])
    with pytest.raises(ValueError, match="grid"):
        exp03.validate_result(duplicate, provenance)
    absent = copy.deepcopy(result)
    del absent["real_model_fits"]
    with pytest.raises(ValueError, match="fit count"):
        exp03.validate_result(absent, provenance)
    bogus = copy.deepcopy(result)
    bogus["calibrator_fits"] = 1
    with pytest.raises(ValueError, match="fit count"):
        exp03.validate_result(bogus, provenance)


def test_paired_cohort_includes_excess_control(revision: tuple[dict, dict]) -> None:
    result, provenance = revision
    control = next(c for c in result["children"] if c["objective"] == "excess")
    control["cohort_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="cohort"):
        exp03.validate_result(result, provenance)


def test_aggregate_has_no_private_dimensions_and_rejects_tampering(
    revision: tuple[dict, dict],
) -> None:
    result, provenance = revision
    for child in result["children"]:
        child["municipality_code"] = "PRIVATE"
        child["metrics"] = {
            "onset_sensitivity": None,
            "municipality_code": "PRIVATE",
            "brier": 0.25,
            "nested": {"municipality_code": "PRIVATE"},
        }
    artifact = exp03.frontier_artifact(
        {"result": result}, {**provenance, "bundle_id": "c" * 64, "kind": "synthetic"}
    )
    serialized = json.dumps(artifact)
    assert "municipality_code" not in serialized and "PRIVATE" not in serialized
    assert artifact["counters"]["real_model_fits"] == 0
    # An absent counter remains absent; it is never converted to an invented zero.
    del result["calibrator_fits"]
    partial = exp03.frontier_artifact(
        {"result": result}, {**provenance, "bundle_id": "c" * 64, "kind": "synthetic"}
    )
    assert "calibrator_fits" not in partial["counters"]
    malicious = copy.deepcopy(artifact)
    malicious["cells"][0]["metrics"]["municipality_code"] = "PRIVATE"
    malicious["frontier_sha256"] = digest(malicious["cells"])
    with pytest.raises(ValueError, match="metric"):
        exp03.validate_frontier_artifact(malicious)
    malicious = copy.deepcopy(artifact)
    malicious["cells"][0]["horizon"] = 1
    malicious["cells"][0]["objective"] = "excess"
    malicious["frontier_sha256"] = digest(malicious["cells"])
    with pytest.raises(ValueError):
        exp03.validate_frontier_artifact(malicious)


def test_complete_contrasts_reuse_objective_aware_cells(revision: tuple[dict, dict]) -> None:
    from sat_dengue.tracking.exp03_contrasts import projection, validate

    result, _ = revision
    design = exp03.load_protocol()["design"]
    comparisons = [
        dict(c, left_objective="onset", right_objective="onset") for c in design["contrasts"]
    ]
    comparisons.extend(
        {
            "id": "O" + str(i),
            "left": v,
            "right": v,
            "left_objective": "onset",
            "right_objective": "excess",
            "tier": "objective_control",
        }
        for i, v in enumerate(("V00", "V09"), 1)
    )
    rows = []
    for comparison in comparisons:
        for family in design["families"]:
            for horizon in design["horizons"]:
                if comparison["id"] in {"O1", "O2"} and horizon == 1:
                    continue
                for window in ("pooled_development", "stress_2024"):
                    cuts = (
                        [
                            w["id"]
                            for w in design["windows"]
                            if w["evidence_type"] == "retrospective_development"
                        ]
                        if window == "pooled_development"
                        else [window]
                    )
                    row = {
                        "contrast_id": comparison["id"],
                        "family": family,
                        "horizon": horizon,
                        "window": window,
                        "source_cuts": cuts,
                        "tier": comparison["tier"],
                        "paired_sensitivity_difference": None,
                        "paired_burden_difference": None,
                        "paired_interval": {},
                        "decision": {
                            "recommendation": "inconclusive",
                            "automatic_selection": False,
                        },
                    }
                    for side in ("left", "right"):
                        row[side + "_variant"] = comparison[side]
                        row[side + "_objective"] = comparison[side + "_objective"]
                        row[side + "_metrics"] = {"onset_sensitivity": None}
                        row[side + "_cells"] = [
                            c["cell_id"]
                            for cut in cuts
                            for c in result["children"]
                            if c["variant"] == comparison[side]
                            and c["objective"] == comparison[side + "_objective"]
                            and c["family"] == family
                            and c["horizon"] == horizon
                            and c["window"] == cut
                        ]
                    rows.append(row)
    validate(projection(rows), design)
    with pytest.raises(ValueError, match="Incomplete"):
        validate(projection(rows[:-1]), design)
    malicious = copy.deepcopy(projection(rows))
    malicious[0]["decision"]["municipality_code"] = "PRIVATE"
    with pytest.raises(ValueError, match="decision"):
        validate(malicious, design)
    altered = copy.deepcopy(rows)
    altered[-1]["right_cells"] = altered[-1]["left_cells"]
    with pytest.raises(ValueError, match="canonical"):
        validate(projection(altered), design)


def test_fitted_cell_without_evaluation_support_keeps_fit_counter(
    revision: tuple[dict, dict],
) -> None:
    """A completed fit is real work even when no evaluation row is scoreable."""
    result, provenance = revision
    child = result["children"][0]
    child.update(model_fitted=True, reason="no_common_evaluation_support")
    result["synthetic_interface_fits"] = 1
    artifact = exp03.frontier_artifact(
        {"result": result}, {**provenance, "bundle_id": "c" * 64, "kind": "synthetic"}
    )
    assert sum(c["model_fitted"] for c in artifact["cells"]) == 1
    assert not any(c["status"] == "evaluable" for c in artifact["cells"])
    assert artifact["counters"]["synthetic_interface_fits"] == 1
    assert artifact["counters"]["real_model_fits"] == 0
    missing = copy.deepcopy(artifact)
    del missing["cells"][0]["model_fitted"]
    missing["frontier_sha256"] = digest(missing["cells"])
    with pytest.raises(ValueError, match="aggregate cells"):
        exp03.validate_frontier_artifact(missing)
    invalid = copy.deepcopy(artifact)
    invalid["cells"][0]["model_fitted"] = 1
    invalid["frontier_sha256"] = digest(invalid["cells"])
    with pytest.raises(ValueError, match="model_fitted"):
        exp03.validate_frontier_artifact(invalid)
    hidden_fit = copy.deepcopy(artifact)
    hidden_fit["counters"]["synthetic_interface_fits"] = 0
    with pytest.raises(ValueError, match="counter"):
        exp03.validate_frontier_artifact(hidden_fit)


def test_native_result_requires_explicit_fit_evidence(revision: tuple[dict, dict]) -> None:
    result, provenance = revision
    del result["children"][0]["model_fitted"]
    with pytest.raises(ValueError, match="model_fitted"):
        exp03.validate_result(result, provenance)


def test_native_phase_counters_preserve_actual_work_and_benchmark_zero(
    revision: tuple[dict, dict],
) -> None:
    result, provenance = revision
    phases = {
        phase: {
            "model_fits": 0,
            "preparer_fits": 0,
            "calibrator_fits": 0,
            "searches": 0,
            "threshold_selections": 0,
            "kind": "inference_only"
            if phase == "consumed_2025_benchmark"
            else "synthetic_generated_data",
        }
        for phase in ("development_oof", "terminal_stress_2024", "consumed_2025_benchmark")
    }
    result["execution_counters"] = phases
    exp03.validate_result(result, provenance)
    for phase in phases:
        invalid = copy.deepcopy(result)
        invalid["execution_counters"][phase]["model_fits"] = 1
        with pytest.raises(ValueError, match="phase counter"):
            exp03.validate_result(invalid, provenance)
    # A fitted terminal cell can be non-evaluable, and still incurred all four operations.
    terminal = next(c for c in result["children"] if c["window"] == "stress_2024")
    terminal.update(model_fitted=True, reason="no_common_evaluation_support")
    result["synthetic_interface_fits"] = 1
    for key in ("model_fits", "preparer_fits", "calibrator_fits", "threshold_selections"):
        phases["terminal_stress_2024"][key] = 1
    exp03.validate_execution_counters(result, exp03.load_protocol()["design"])
    phases["terminal_stress_2024"]["threshold_selections"] = 0
    with pytest.raises(ValueError, match="threshold_selections"):
        exp03.validate_execution_counters(result, exp03.load_protocol()["design"])
    scientific = copy.deepcopy(result)
    scientific["synthetic"] = False
    del scientific["execution_counters"]
    with pytest.raises(ValueError, match="requires phase"):
        exp03.validate_execution_counters(scientific, exp03.load_protocol()["design"])
