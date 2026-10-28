from __future__ import annotations

import copy
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments.exp03 import load_protocol as load_exp03_protocol
from sat_dengue.experiments.exp03_1_contract import counts, digest, protocol
from sat_dengue.experiments.exp03_1_demo import generate, synthetic_bundle
from sat_dengue.experiments.exp03_1_engine import execution_plan, reuse_decision, variant_predictors
from sat_dengue.experiments.exp03_1_evaluation import (
    error_class,
    grouped_metrics,
    metrics,
    paired_effect,
    paired_interval,
    reused_delay_diagnostic,
    select_threshold,
)
from sat_dengue.experiments.exp03_1_preflight import preflight
from sat_dengue.experiments.exp03_1_reporting import read_bundle, validate_bundle, write_bundle
from sat_dengue.tracking.exp03_1 import aggregate_projection


def identities() -> dict[str, str]:
    return {
        name: f"{index:064x}" for index, name in enumerate(protocol()["reuse_identity_fields"], 1)
    }


def bundle() -> dict:
    decision = reuse_decision(identities(), identities())
    plan = execution_plan(decision)
    return {
        "schema": "exp03-1-scientific-bundle-v1",
        "experiment_id": "EXP031",
        "scientific_id": "EXP03.1",
        "protocol_sha256": digest(protocol()),
        "reuse_decision": decision,
        "execution_plan": plan,
        "predictions": [
            {
                "cell_id": "M00-gam-t1-development_2020",
                "municipality_code": "50001",
                "target_month": "2020-01",
                "score": 0.2,
                "alert": False,
            }
        ],
        "thresholds": [
            {"cell_id": "M00-gam-t1-development_2020", "threshold": None, "budget": 1.0}
        ],
        "metrics": [{"family": "gam", "horizon": 1, "status": "synthetic_only"}],
        "diagnostics": [{"kind": "persistence", "status": "synthetic_only"}],
        "execution_counters": {
            "real_private_reads": 0,
            "real_reservations": 0,
            "real_fits": 0,
            "real_calibrations": 0,
            "real_searches": 0,
            "permanent_mlflow_writes": 0,
        },
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "synthetic": True,
    }


def test_reuse_and_refit_paths_and_exact_v09_predictors() -> None:
    same = identities()
    assert reuse_decision(same, same)["decision"] == "reused"
    assert execution_plan(reuse_decision(same, same))["counts"] == {
        "total": 96,
        "reused": 36,
        "new_fits": 60,
    }
    for field in protocol()["reuse_identity_fields"]:
        changed = copy.deepcopy(same)
        changed[field] = "f" * 64
        decision = reuse_decision(changed, same)
        assert decision["decision"] == "refitted" and field in decision["mismatched"]
        assert execution_plan(decision)["counts"] == {"total": 96, "reused": 0, "new_fits": 96}
    malformed = copy.deepcopy(same)
    malformed[protocol()["reuse_identity_fields"][0]] = "not-a-sha256"
    assert reuse_decision(malformed, malformed)["decision"] == "refitted"
    v09 = load_exp03_protocol()["design"]["variants"]["V09"]
    assert variant_predictors(v09, "M00") == v09
    assert len(variant_predictors(v09, "M01")) == len(v09) + 3
    assert len(variant_predictors(v09, "M02")) == len(v09) + 6
    with pytest.raises(ValueError, match="ordered V09"):
        variant_predictors([*v09, "invented"], "M00")
    assert counts()["terminal_cells"] == 24


def test_metrics_reconstruct_alert_quality_and_distinguish_far_fpr() -> None:
    frame = pd.DataFrame(
        {
            "truth": [1, 0, 0, 1],
            "score": [0.9, 0.8, 0.1, 0.7],
            "alert": [True, True, False, False],
            "municipality_code": ["a", "a", "b", "b"],
            "target_year": [2020] * 4,
        }
    )
    result = metrics(frame, exposure=2.0, bins=2)
    assert result["detected"] == 1 and result["missed"] == 1 and result["false_alerts"] == 1
    assert result["far"] == 0.5 and result["fpr"] == 0.5
    assert result["false_alerts_per_monitored_municipality_year"] == 0.5
    assert result["brier"] == pytest.approx(0.1875)
    tied = frame.assign(score=[0.8, 0.8, 0.2, 0.2])
    reordered = tied.iloc[[1, 0, 3, 2]].reset_index(drop=True)
    assert (
        metrics(tied, exposure=2.0)["average_precision"]
        == metrics(reordered, exposure=2.0)["average_precision"]
    )
    right = frame.assign(score=[0.8, 0.6, 0.2, 0.4], alert=[True, False, False, False])
    paired = paired_effect(
        frame.assign(year_month=["a", "b", "c", "d"]),
        right.assign(year_month=["a", "b", "c", "d"]),
        ["year_month"],
    )
    assert paired.alert_delta.tolist() == [0, 1, 0, 0]


def test_budget_whole_ties_no_alert_and_group_reporting() -> None:
    truth = pd.Series([1, 0, 0], dtype="Int64")
    scores = pd.Series([0.8, 0.8, 0.2])
    selected = select_threshold(truth, scores, exposure=0.0)
    assert selected["threshold"] is None and selected["false_alerts"] == 0
    selected = select_threshold(truth, scores, exposure=1.0)
    assert selected["threshold"] == 0.8 and selected["alerts"] == 2
    frame = pd.DataFrame(
        {
            "truth": [1, 0],
            "score": [0.8, 0.2],
            "alert": [True, False],
            "municipality_code": ["50001", "73001"],
            "target_year": [2020, 2020],
            "contrast": ["Q1", "Q1"],
            "family": ["gam", "gam"],
            "horizon": [1, 1],
            "department_code": ["50", "73"],
            "transmission_profile": ["low", "high"],
            "exposure": [1.0, 1.0],
        }
    )
    assert len(grouped_metrics(frame)) == 2
    duplicated_month = pd.concat([frame, frame.assign(score=[0.7, 0.3])], ignore_index=True)
    assert all(
        row["false_alerts_per_monitored_municipality_year"] == 0
        for row in grouped_metrics(duplicated_month)
    )


def test_paired_development_interval_and_support_controls() -> None:
    frame = pd.DataFrame(
        {
            "municipality_code": ["a", "a", "b", "b"],
            "target_year": [2020, 2021, 2020, 2021],
            "window": ["development_2020", "development_2021"] * 2,
            "left_value": [1.0, 2.0, 3.0, 4.0],
            "right_value": [0.0, 1.0, 2.0, 3.0],
        }
    )
    interval = paired_interval(frame, repeats=20)
    assert interval["paired_weights_shared"] and interval["valid_draws"] > 0
    with pytest.raises(ValueError, match="Stress"):
        paired_interval(frame.assign(window="stress_2024"))
    assert (
        paired_interval(frame.loc[frame.municipality_code.eq("a")])["status"]
        == "insufficient_cluster_support"
    )


def test_reused_delay_diagnostic_is_frozen_and_separates_strict_unavailability() -> None:
    conditional = {
        "diagnostic": "conditional_stale_feature_stress",
        "effective_source_months": ["2023-12"],
        "frozen_components": ["model", "preparer", "calibrator", "threshold"],
        "new_fits": 0,
    }
    strict = {
        "diagnostic": "strict_current_unavailable",
        "status": "unable_to_issue",
        "new_fits": 0,
    }
    result = reused_delay_diagnostic(conditional, strict)
    assert result["new_fits"] == 0 and result["source_experiment"] == "EXP03"
    with pytest.raises(ValueError, match="delay"):
        reused_delay_diagnostic({**conditional, "new_fits": 1}, strict)


@pytest.mark.parametrize(
    "values,expected",
    [
        ((0, 1, 1), "onset"),
        ((1, 1, 0), "continuation"),
        ((1, 0, 0), "onset_previously_at_t1"),
        ((0, 0, 0), "no_excess"),
        ((None, 0, 0), "unknown"),
    ],
)
def test_persistence_error_classes(values: tuple, expected: str) -> None:
    assert error_class(*values) == expected


def test_safe_bundle_tracking_and_blocked_preflight(repo_tmp_path: Path) -> None:
    value = bundle()
    validate_bundle(value)
    target = Path("tmp") / repo_tmp_path.name / "exp03-1-bundle.json"
    identity = write_bundle(value, target)
    assert read_bundle(target, identity) == value
    aggregate = aggregate_projection(value)
    assert "municipality_code" not in repr(aggregate)
    receipt = preflight({"profile": "exp03_1", "tracking": "disabled", "experiment_id": "EXP031"})
    assert not receipt["execution_ready"] and not any(receipt["effects"].values())
    assert receipt["G5"] == "NOT_APPROVED" and receipt["champion"] == "not_selected"
    real = copy.deepcopy(value)
    real["synthetic"] = False
    with pytest.raises(PermissionError):
        validate_bundle(real)
    private = copy.deepcopy(value)
    private["metrics"] = [{"private": "private://data"}]
    with pytest.raises(ValueError, match="private"):
        aggregate_projection(private)
    post_2024 = copy.deepcopy(value)
    post_2024["predictions"][0]["target_month"] = "2025-01"
    with pytest.raises(ValueError, match="post-2024"):
        validate_bundle(post_2024)
    wrong_budget = copy.deepcopy(value)
    wrong_budget["thresholds"][0]["budget"] = 2.0
    with pytest.raises(ValueError, match="budget"):
        validate_bundle(wrong_budget)
    wrong_protocol = copy.deepcopy(value)
    wrong_protocol["protocol_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="protocol"):
        validate_bundle(wrong_protocol)
    with pytest.raises(PermissionError, match="unauthorized"):
        preflight({"profile": "exp03_1", "tracking": "enabled", "experiment_id": "EXP031"})


def test_source_free_example_is_complete_and_marked(repo_tmp_path: Path) -> None:
    output = Path("tmp") / repo_tmp_path.name / "complete-example"
    generated = generate(output)
    assert set(generated) == {"bundle", "bundle_sha256", "aggregate", "marker"}
    assert "synthetic_generated_data" in Path(generated["marker"]).read_text(encoding="utf-8")
    assert synthetic_bundle()["execution_counters"]["real_fits"] == 0
    with pytest.raises(ValueError, match="repository-local"):
        generate(Path.cwd().resolve().parent)
