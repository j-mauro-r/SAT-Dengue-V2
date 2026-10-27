"""Contrato público EXP02: identidad, comparación aislada y límites científicos."""

import json
from pathlib import Path

from sat_dengue.tracking.experiments import resolve_experiment

PROTOCOL = Path("docs/product/experiments/EXP02_label_stability/protocol.json")


def test_exp02_has_own_registered_identity_and_unexecuted_science():
    protocol = json.loads(PROTOCOL.read_text())
    tags = resolve_experiment("EXP02")
    assert tags["objective_slug"] == "label_episode_stability"
    assert tags["pipeline"] == "exp02"
    assert protocol["labels"]["epidemic_axis"] == "pending_scientific_definition"
    assert protocol["labels"]["epidemic_policy"] == "include_all_years"
    assert protocol["execution"]["real_execution_authorized"] is False
    assert protocol["acceptance"]["G5"] == "NOT_APPROVED"
    assert protocol["acceptance"]["champion"] == "not_selected"
    assert protocol["acceptance"]["window_selection"] == "prohibited_automatic_winner"
    assert "ablation" not in json.dumps(tags)
    assert "EXP03" not in json.dumps(protocol)


def test_exp02_only_changes_target_with_fixed_predictors_and_calendar():
    protocol = json.loads(PROTOCOL.read_text())
    baseline = json.loads(
        Path("docs/product/experiments/EXP01_direct_onset/protocol.json").read_text()
    )
    design = protocol["design"]
    assert design["history_years"] == [5, 7, 9]
    assert design["predictor_channel_years"] == design["selection_anchor_years"] == 5
    for field in ["predictors", "families", "windows"]:
        assert design[field] == baseline["design"][field]
    assert design["expected_predictive_children"] == 3 * 3 * 2 * 3
    assert design["expected_label_children"] == 3 * 3
    assert design["expected_children"] == 63
    assert design["maximum_model_fits"] == design["maximum_calibrator_fits"] == 54
    for window in design["windows"]:
        for role in ["train", "calibration", "selection"]:
            assert window[role][1] < "2024-01"
        assert window["evaluation"][1] < "2025-01"
    assert design["windows"][-1]["evaluation"] == ["2024-01", "2024-12"]
    assert design["windows"][-1]["evidence_type"] == "retrospective_stress"
    assert protocol["restrictions"]["exclude_2025"] is True
