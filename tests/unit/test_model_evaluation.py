"""Stage 5 calibration/threshold unit tests over deterministic synthetic inputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from scripts.model_evaluation.contract import (
    CONTRACT_PATH,
    ModelEvaluationConfig,
    Stage5Contract,
    Stage5Knobs,
    load_contract,
    resolve_root,
)
from scripts.model_evaluation.decision_policy import (
    POLICY_PATH,
    DecisionPolicyError,
    load_decision_policy,
)
from scripts.model_evaluation.pipeline import (
    Stage4Inputs,
    _assert_selection_independence,
    _assert_verify_allowed,
    _build_temporal_audit_row,
    _bundle_identity,
    _fit_sigmoid,
    _select_threshold_from_grid,
    _threshold_limits,
    build_model_evaluation,
)
from scripts.model_training.loading import TemporalSource
from scripts.model_training.pipeline import ModelTrainingResult


def _repo_root() -> Path:
    return resolve_root(Path(__file__))


@pytest.fixture
def contract() -> Stage5Contract:
    policy = load_decision_policy(_repo_root())
    return Stage5Contract(
        raw={"decision_policy_path": str(POLICY_PATH)},
        knobs=Stage5Knobs(
            max_false_alarm_increase_pp=policy.knobs.max_false_alarm_increase_pp,
            min_onset_sensitivity_gain_pp=policy.knobs.min_onset_sensitivity_gain_pp,
            seed=policy.knobs.seed,
        ),
        decision_policy=policy,
    )


def test_champion_decision_policy_is_the_single_human_editable_source() -> None:
    root = _repo_root()
    policy = load_decision_policy(root)
    calibration = json.loads((root / CONTRACT_PATH).read_text(encoding="utf-8"))
    assessment = json.loads(
        (root / "docs/product/stage-5/model_evaluation_contract_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert calibration["decision_policy_path"] == str(POLICY_PATH)
    assert assessment["decision_policy_path"] == str(POLICY_PATH)
    assert "knobs" not in calibration
    assert "knobs" not in assessment
    assert policy.raw["human_disposition"] == {
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "authority": "Mauricio",
        "decided_on": "2026-10-21",
        "reason": (
            "All six candidate/horizon procedures exceeded the approved false-alert "
            "increase constraint on the consumed 2025 comparison."
        ),
    }


def test_champion_decision_policy_rejects_invalid_manual_values(repo_tmp_path: Path) -> None:
    root = _repo_root()
    raw = json.loads((root / POLICY_PATH).read_text(encoding="utf-8"))
    raw["utility"]["max_false_alarm_increase_pp"] = 101
    relative = (repo_tmp_path / "invalid_champion_policy.json").relative_to(root)
    path = root / relative
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(DecisionPolicyError, match="within"):
        load_decision_policy(root, relative)


def test_base_stage5_contract_loads() -> None:
    root = _repo_root()
    loaded = load_contract(ModelEvaluationConfig(root=root, contract_path=CONTRACT_PATH))
    assert loaded.raw["candidate_families"] == ["xgboost", "lightgbm", "gam"]
    assert loaded.knobs.max_false_alarm_increase_pp == pytest.approx(5.0)
    assert loaded.knobs.min_onset_sensitivity_gain_pp == pytest.approx(10.0)


@pytest.mark.parametrize(
    "mutation_key, mutation_value, expected_message",
    [
        (
            "component_available_by_origin",
            "2019-01",
            "component availability is after external evaluation origin start",
        ),
        (
            "threshold_selection_targets",
            ["2018-12", "2019-01"],
            "component availability is after external evaluation origin start",
        ),
    ],
)
def test_reject_late_component_availability(
    mutation_key: str,
    mutation_value: object,
    expected_message: str,
    repo_tmp_path: Path,
) -> None:
    root = _repo_root()
    base = json.loads((root / CONTRACT_PATH).read_text(encoding="utf-8"))
    base["window_role_calendar"]["2018-12_t1"][mutation_key] = mutation_value
    if mutation_key == "threshold_selection_targets":
        base["window_role_calendar"]["2018-12_t1"]["component_available_by_origin"] = "2019-01"

    variant_rel = (repo_tmp_path / "invalid_calendar.json").relative_to(root)
    variant_path = root / variant_rel
    variant_path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=expected_message):
        load_contract(ModelEvaluationConfig(root=root, contract_path=variant_rel))


def test_denominator_and_criteria_rules(contract: Stage5Contract) -> None:
    min_onset, max_far = _threshold_limits(0.20, 0.30, contract)
    assert min_onset == pytest.approx(0.30)
    assert max_far == pytest.approx(0.35)

    unavailable = _select_threshold_from_grid(
        pd.DataFrame(
            [
                {
                    "threshold": 0.9,
                    "onset_sensitivity": None,
                    "onset_sensitivity_evaluable": False,
                    "detected_onsets": 0,
                    "real_onsets": 10,
                    "false_alarm_ratio": None,
                    "false_alarm_ratio_evaluable": False,
                    "false_alerts": 0,
                    "emitted_alerts": 0,
                }
            ]
        ),
        min_required_onset=min_onset,
        max_allowed_false_alarm=max_far,
    )
    assert unavailable["status"] == "no_feasible_threshold"

    selected = _select_threshold_from_grid(
        pd.DataFrame(
            [
                {
                    "threshold": 0.8,
                    "onset_sensitivity": 0.28,
                    "onset_sensitivity_evaluable": True,
                    "detected_onsets": 28,
                    "real_onsets": 100,
                    "false_alarm_ratio": 0.33,
                    "false_alarm_ratio_evaluable": True,
                    "false_alerts": 11,
                    "emitted_alerts": 33,
                },
                {
                    "threshold": 0.6,
                    "onset_sensitivity": 0.34,
                    "onset_sensitivity_evaluable": True,
                    "detected_onsets": 34,
                    "real_onsets": 100,
                    "false_alarm_ratio": 0.34,
                    "false_alarm_ratio_evaluable": True,
                    "false_alerts": 12,
                    "emitted_alerts": 35,
                },
                {
                    "threshold": 0.55,
                    "onset_sensitivity": 0.34,
                    "onset_sensitivity_evaluable": True,
                    "detected_onsets": 34,
                    "real_onsets": 100,
                    "false_alarm_ratio": 0.34,
                    "false_alarm_ratio_evaluable": True,
                    "false_alerts": 10,
                    "emitted_alerts": 35,
                },
                {
                    "threshold": 0.7,
                    "onset_sensitivity": 0.35,
                    "onset_sensitivity_evaluable": True,
                    "detected_onsets": 35,
                    "real_onsets": 100,
                    "false_alarm_ratio": 0.36,
                    "false_alarm_ratio_evaluable": True,
                    "false_alerts": 13,
                    "emitted_alerts": 36,
                },
            ]
        ),
        min_required_onset=min_onset,
        max_allowed_false_alarm=max_far,
    )
    assert selected["status"] == "selected"
    assert selected["selected_threshold"] == pytest.approx(0.55)
    assert selected["selected_onset_sensitivity"] == pytest.approx(0.34)
    assert selected["selected_false_alarm_ratio"] == pytest.approx(0.34)
    assert selected["meets_min_onset_gain"] is True


@pytest.mark.parametrize(
    "rows, expect_error",
    [
        (
            [
                {"split_role": "hyperparameter_selection", "fold": 0},
                {"split_role": "calibration_fit", "fold": 0},
            ],
            True,
        ),
        (
            [
                {"split_role": "hyperparameter_selection", "fold": 0},
                {"split_role": "threshold_selection", "fold": 0},
            ],
            True,
        ),
        (
            [
                {"split_role": "hyperparameter_selection", "fold": 0},
                {"split_role": "calibration_fit", "fold": 1},
                {"split_role": "calibration_selection", "fold": 1},
                {"split_role": "threshold_selection", "fold": 1},
            ],
            False,
        ),
    ],
)
def test_reject_selection_label_reuse(rows: list[dict[str, int | str]], expect_error: bool) -> None:
    frame = pd.DataFrame(rows)
    if expect_error:
        with pytest.raises(ValueError, match="Selection independence violated"):
            _assert_selection_independence(frame)
    else:
        hp_folds, development_folds = _assert_selection_independence(frame)
        assert hp_folds == {0}
        assert development_folds == {1}


def test_configuration_change_updates_identity() -> None:
    base_payload = {
        "stage4": "bundle-a",
        "knobs": {
            "max_false_alarm_increase_pp": 5.0,
            "min_onset_sensitivity_gain_pp": 10.0,
            "seed": 42,
        },
    }
    modified_payload = {
        **base_payload,
        "knobs": {
            "max_false_alarm_increase_pp": 6.0,
            "min_onset_sensitivity_gain_pp": 10.0,
            "seed": 42,
        },
    }
    assert _bundle_identity(base_payload) != _bundle_identity(modified_payload)


def _t2_calendar() -> dict[str, Any]:
    return {
        "hyperparameter_selection_targets": [
            "2018-02",
            "2018-03",
            "2018-04",
            "2018-05",
            "2018-06",
        ],
        "calibration_fit_targets": ["2018-08", "2018-09"],
        "calibration_selection_targets": ["2018-10", "2018-11"],
        "threshold_selection_targets": ["2018-12"],
        "external_evaluation_origin_range": {"start": "2018-12", "end": "2019-04"},
        "external_evaluation_target_range": {"start": "2019-02", "end": "2019-06"},
        "component_available_by_origin": "2018-12",
    }


def _t2_selected_internal() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    role_months = {
        "hyperparameter_selection": ["2018-02", "2018-03", "2018-04", "2018-05", "2018-06"],
        "calibration_fit": ["2018-08", "2018-09"],
        "calibration_selection": ["2018-10", "2018-11"],
        "threshold_selection": ["2018-12"],
    }
    idx = 0
    for split_role, targets in role_months.items():
        for target in targets:
            rows.append(
                {
                    "split_role": split_role,
                    "year_month": str(pd.Period(target, freq="M") - 2),
                    "target_period_t2": target,
                    "municipality_code": "05001",
                    "feature_row": idx,
                }
            )
            idx += 1
    return pd.DataFrame(rows)


@pytest.mark.parametrize("case", ["late_fit", "late_choice", "equality"])
def test_t2_real_validator_requires_labeled_availability(case: str) -> None:
    calendar = _t2_calendar()
    calendar["hyperparameter_selection_targets"] = [
        "2017-07",
        "2017-08",
        "2017-09",
        "2017-10",
        "2017-11",
        "2017-12",
    ]
    if case != "late_fit":
        calendar["calibration_fit_targets"] = ["2018-02", "2018-03"]
    if case == "equality":
        calendar["calibration_selection_targets"] = ["2018-05", "2018-06"]
        calendar["threshold_selection_targets"] = ["2018-08", "2018-09"]
    rows: list[dict[str, object]] = []
    for role in (
        "hyperparameter_selection",
        "calibration_fit",
        "calibration_selection",
        "threshold_selection",
    ):
        for target in calendar[f"{role}_targets"]:
            rows.append(
                dict(
                    split_role=role,
                    year_month=str(pd.Period(target, freq="M") - 2),
                    target_period_t2=target,
                    municipality_code="05001",
                    feature_row=len(rows),
                )
            )

    def validate() -> dict[str, object]:
        return _build_temporal_audit_row(
            candidate="xgboost",
            window="2018-12_t2",
            horizon=2,
            cutoff="2018-12",
            selected_configuration_id="xgboost_00",
            selected_internal=pd.DataFrame(rows),
            target_column="target_period_t2",
            calendar=calendar,
            reserved_start="2025-01",
            external_origin_start="2018-12",
            hp_folds={0},
            development_folds={1},
        )

    if case == "equality":
        assert validate()["chronology_pass"] is True
    else:
        expected = "2018-09 > 2018-08" if case == "late_fit" else "2018-11 > 2018-10"
        with pytest.raises(ValueError, match=f"Label availability violation .*{expected}"):
            validate()


def test_t2_temporal_audit_rejects_invalid_target_coverage_with_detail() -> None:
    frame = _t2_selected_internal()
    frame.loc[
        frame["split_role"].eq("threshold_selection"),
        "target_period_t2",
    ] = "2018-11"

    with pytest.raises(
        ValueError,
        match=(
            "xgboost 2018-12_t2 threshold_selection target coverage mismatch: "
            "missing=\\['2018-12'\\] unexpected=\\['2018-11'\\]"
        ),
    ):
        _build_temporal_audit_row(
            candidate="xgboost",
            window="2018-12_t2",
            horizon=2,
            cutoff="2018-12",
            selected_configuration_id="xgboost_00",
            selected_internal=frame,
            target_column="target_period_t2",
            calendar=_t2_calendar(),
            reserved_start="2025-01",
            external_origin_start="2018-12",
            hp_folds={0},
            development_folds={1},
        )


def test_verify_guards_reject_fitting_and_selection_attempts() -> None:
    with pytest.raises(ValueError, match="verify_only forbids operation: outer_model_fit"):
        _assert_verify_allowed(verify_only=True, operation="outer_model_fit")

    with pytest.raises(ValueError, match="verify_only forbids operation: calibrator_fit"):
        _fit_sigmoid(
            pd.Series([0.2, 0.8], dtype="Float64"),
            pd.Series([0, 1], dtype="Int64"),
            seed=42,
            allow_fit=False,
        )

    with pytest.raises(ValueError, match="verify_only forbids operation: threshold_selection"):
        _select_threshold_from_grid(
            pd.DataFrame(
                [
                    {
                        "threshold": 0.5,
                        "onset_sensitivity": 0.4,
                        "onset_sensitivity_evaluable": True,
                        "detected_onsets": 4,
                        "real_onsets": 10,
                        "false_alarm_ratio": 0.2,
                        "false_alarm_ratio_evaluable": True,
                        "false_alerts": 2,
                        "emitted_alerts": 10,
                    }
                ]
            ),
            min_required_onset=0.3,
            max_allowed_false_alarm=0.25,
            allow_selection=False,
        )


def test_execute_reuses_existing_bundle_without_fitting(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    policy = load_decision_policy(_repo_root())
    contract = Stage5Contract(
        raw={
            "candidate_families": ["xgboost"],
            "reserved_final_block_start": "2025-01",
            "calibration_policy": {"curve_bins": 10, "min_bin_support": 30},
            "threshold_policy": {"probability_precision": 12},
            "window_role_calendar": {"2018-12_t1": {}},
            "artifacts": {
                "base_dir": "artifacts/model_evaluation",
                "existing_policy": "reuse_identical",
            },
            "knobs": {
                "max_false_alarm_increase_pp": 5.0,
                "min_onset_sensitivity_gain_pp": 10.0,
                "seed": 42,
            },
            "role_reuse_policy": {},
        },
        knobs=Stage5Knobs(
            max_false_alarm_increase_pp=5.0,
            min_onset_sensitivity_gain_pp=10.0,
            seed=42,
        ),
        decision_policy=policy,
    )

    suite_bundle = tmp_path / "artifacts/model_training/candidate_suite/dummy"
    suite_bundle.mkdir(parents=True)
    stage4_inputs = Stage4Inputs(
        suite=ModelTrainingResult(bundle=suite_bundle, manifest={"windows": ["2018-12_t1"]}),
        source=TemporalSource(
            bundle=tmp_path / "artifacts/training_preparation/temporal/dummy",
            manifest={},
            development_X=pd.DataFrame(),
        ),
        stage4_contract={"selection_policy": {}},
        reference_bundle=tmp_path / "artifacts/model_training/references/dummy",
        candidate_bundles={"xgboost": tmp_path / "artifacts/model_training/candidates/dummy"},
    )

    bundle = tmp_path / "artifacts/model_evaluation/dummy-bundle"
    bundle.mkdir(parents=True)
    (bundle / "manifest.json").write_text("{}\n", encoding="utf-8")

    calls: dict[str, int] = {"verify": 0}

    def _mock_verify_existing_bundle(**_kwargs: object) -> dict[str, object]:
        calls["verify"] += 1
        return {
            "bundle_id": "dummy-bundle",
            "stage4_candidate_suite_bundle": "artifacts/model_training/candidate_suite/dummy",
            "stage4_reference_bundle": "artifacts/model_training/references/dummy",
            "files": {},
        }

    monkeypatch.setattr("scripts.model_evaluation.pipeline.load_contract", lambda _cfg: contract)
    monkeypatch.setattr(
        "scripts.model_evaluation.pipeline._load_stage4_inputs",
        lambda _cfg, _contract: stage4_inputs,
    )
    monkeypatch.setattr("scripts.model_evaluation.pipeline._identity_payload", lambda **_kwargs: {})
    monkeypatch.setattr(
        "scripts.model_evaluation.pipeline._bundle_identity",
        lambda _identity: "dummy-bundle",
    )
    monkeypatch.setattr(
        "scripts.model_evaluation.pipeline._verify_existing_bundle",
        _mock_verify_existing_bundle,
    )
    monkeypatch.setattr(
        "scripts.model_evaluation.pipeline.fit_model",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("fit_model called")),
    )

    result = build_model_evaluation(ModelEvaluationConfig(root=tmp_path), verify_only=False)
    assert result.bundle == bundle
    assert calls["verify"] == 1
