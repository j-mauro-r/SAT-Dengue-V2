"""Generated-only Beta acceptance in the existing test harness; no private science."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from kedro.io import DatasetError
from test_canonical_model_table import panel as panel

from sat_dengue.canonical.table import CLIMATE, PREDICTORS, build_table
from sat_dengue.configuration import validate_parameters
from sat_dengue.datasets import exp_beta01 as datasets
from sat_dengue.experiments import exp_beta01 as beta
from sat_dengue.experiments import exp_beta01_engine as engine
from sat_dengue.pipeline_registry import register_pipelines
from sat_dengue.training_preparation.serialization import bytes_record

ROOT = Path(__file__).resolve().parents[2]


def protocol() -> dict[str, Any]:
    return json.loads((ROOT / datasets.PROTOCOL_PATH).read_text())


def test_onset_cohort_has_no_future_controls_and_excludes_2025(panel: pd.DataFrame) -> None:
    table, schema = build_table(panel)
    source = {"table": table, "columns": schema, "protocol": protocol()}
    result = beta.prepare(source, {"profile": "exp_beta01", "tracking": "disabled"})
    for horizon, cohort in result["cohorts"].items():
        assert cohort.target_month.lt("2025-01").all()
        assert cohort[PREDICTORS].notna().all().all()
        assert not set(PREDICTORS) & {"onset_target", "earlier_onset_t1", "target_month"}
        if horizon == 2:
            assert cohort.loc[cohort.earlier_onset_t1, "onset_target"].eq(0).all()
    changed = table.copy()
    changed["y_t1"], changed["y_t2"] = 999, 999
    changed["p75_t1"], changed["p75_t2"] = 999, 999
    again = beta.prepare(
        {**source, "table": changed}, {"profile": "exp_beta01", "tracking": "disabled"}
    )
    for h in (1, 2):
        pd.testing.assert_frame_equal(result["cohorts"][h], again["cohorts"][h])


def cohort(horizon: int = 1) -> pd.DataFrame:
    rows = []
    for m in ("50001", "73001"):
        for i, t in enumerate(pd.period_range("2011-06", "2024-12", freq="M")):
            row: dict[str, Any] = {n: float((i % 5) + 1) for n in PREDICTORS}
            row.update(
                municipality_code=m,
                department_code=m[:2],
                year_month=str(t),
                target_month=str(t + horizon),
                target_year=(t + horizon).year,
                onset_target=int(i % 4 == 0),
            )
            rows.append(row)
    return pd.DataFrame(rows)


def test_temporal_roles_use_common_target_cutoffs_and_embargo() -> None:
    p = protocol()
    parts = beta.role_parts(cohort(2), 2024, p)["parts"]
    previous = None
    for name, frame in parts.items():
        assert frame.department_code.nunique() == 2
        if previous is not None:
            assert frame.year_month.ge(previous).all()
        if name != "evaluation":
            assert frame.target_month.lt("2024-01").all()
        previous = str(frame.target_month.max())
    assert parts["evaluation"].target_month.min() == "2024-02"
    with pytest.raises(ValueError, match="Unapproved"):
        beta.role_parts(cohort(), 2025, p)


def test_adaptation_shrinks_and_falls_back_without_support() -> None:
    frame = pd.DataFrame(
        {"department_code": ["50"] * 40 + ["73"] * 2, "onset_target": [1, 0] * 20 + [1, 0]}
    )
    spec = protocol()["adaptation"]
    result = beta.fit_adaptation(frame, np.repeat(0.1, len(frame)), spec)
    assert result["50"]["status"] == "adapted" and result["50"]["offset"] > 0
    assert result["73"]["status"] == "global_fallback" and result["73"]["offset"] == 0
    loose = beta.fit_intercept(np.repeat(0.1, 40), [1, 0] * 20, 1.0)
    assert result["50"]["offset"] < loose


def test_policy_keeps_ties_and_has_no_alert_fallback() -> None:
    result = beta.thresholds([1, 0, 1, 0], [0.9, 0.9, 0.2, 0.1], 1.0, 0.0)
    assert result["threshold"] is None
    result = beta.thresholds([1, 0, 1, 0], [0.9, 0.9, 0.2, 0.1], 1.0, 1.0)
    assert result["threshold"] == 0.2 and result["false_alerts"] == 1


def test_metric_denominator_and_false_alerts_are_prediction_native() -> None:
    f = pd.DataFrame(
        {
            "truth": [1, 0, 0],
            "alert": [True, True, False],
            "score": [0.8, 0.7, 0.1],
            "municipality_code": ["50001"] * 3,
        }
    )
    r = beta.metric_row(f, 1.0)
    assert r["detected"] == 1 and r["false_alerts"] == 1
    assert r["exposure_municipality_years"] == 0.25
    assert r["false_alerts_per_municipality_year"] == 4.0 and not r["budget_met"]


def test_reference_rejects_intersection_or_changed_truth() -> None:
    base = cohort().head(3).rename(columns={"onset_target": "truth"})
    base["arm"], base["climate"], base["horizon"], base["year"] = "G0", "ON", 1, 2011
    old = base.rename(columns={"year_month": "origin_month"}).copy()
    old["score"], old["alert"] = 0.4, False
    predictions, audit = engine.paired_reference(base, old)
    assert audit[0]["status"] == "PAIRED" and len(predictions) == 3
    old.loc[0, "truth"] = 1 - old.loc[0, "truth"]
    assert engine.paired_reference(base, old)[1][0]["status"] == "NO_EVALUABLE"
    assert engine.paired_reference(base, old.iloc[1:])[1][0]["status"] == "NO_EVALUABLE"


def test_registry_profile_and_legacy_routes_stay_separate() -> None:
    graph = register_pipelines()["exp_beta01"]
    assert len(graph.nodes) == 5
    assert graph.inputs() == {"exp_beta01_sources", "parameters"}
    assert graph.outputs() == {"exp_beta01_bundle"}
    with pytest.raises(ValueError, match="disabled tracking"):
        validate_parameters({"profile": "exp_beta01", "tracking": "enabled"})
    with pytest.raises(ValueError, match="disabled tracking"):
        validate_parameters(
            {"profile": "exp_beta01", "tracking": "disabled", "experiment_id": "EXP01"}
        )


def test_source_contract_tampering_fails_before_private_read(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = repo_tmp_path / "protocol.json"
    p.write_text(json.dumps({"tampered": True}))
    monkeypatch.setattr(datasets, "PROTOCOL_PATH", str(p))
    with pytest.raises(DatasetError, match="protocol identity"):
        datasets.BetaSourcesDataset().load()


def test_generated_execution_is_reproducible_and_holds_evaluation_labels_out() -> None:
    p = protocol()
    p["evaluation_years"] = [2020]
    p["model"]["n_estimators"] = 4
    prepared: dict[str, Any] = {
        "evidence_type": "synthetic_generated_data",
        "protocol": p,
        "cohorts": {1: cohort()},
        "reference": None,
        "provenance": {"sources": {}, "execution": {"code": {}}},
    }
    trained = engine.train(copy.deepcopy(prepared))
    adapted = engine.adapt(trained)
    predicted = engine.predict(adapted)
    result = engine.evaluate(predicted)
    again = engine.evaluate(engine.predict(engine.adapt(engine.train(copy.deepcopy(prepared)))))
    assert result["payloads"] == again["payloads"]
    manifest = json.loads(result["payloads"]["manifest.json"])
    assert manifest["real_model_fits"] == 0
    assert manifest["generated_model_fits"] == 2
    for name, record in manifest["files"].items():
        assert bytes_record(result["payloads"][name]) == record
    assert all(c["parts"]["train"].department_code.nunique() == 2 for c in trained["cells"])
    # ON/OFF are row-paired; OFF removes exactly the existing nine climate fields.
    assert set(trained["cells"][0]["predictors"]) == set(PREDICTORS) - set(CLIMATE)
    assert trained["cells"][0]["parts"]["evaluation"].equals(
        trained["cells"][1]["parts"]["evaluation"]
    )
    changed = copy.deepcopy(prepared)
    mask = changed["cohorts"][1].target_year.eq(2020)
    changed["cohorts"][1].loc[mask, "onset_target"] = (
        1 - changed["cohorts"][1].loc[mask, "onset_target"]
    )
    altered = engine.predict(engine.adapt(engine.train(changed)))
    for before, after in zip(predicted["cells"], altered["cells"], strict=True):
        assert before["model_bytes"] == after["model_bytes"]
        assert before["department_offsets"] == after["department_offsets"]
    assert predicted["policies"] == altered["policies"]
    assert predicted["predictions"].score.equals(altered["predictions"].score)

    # Formal NI uses R0, even when G0 and L1 have identical no-alert policies.
    checked = copy.deepcopy(predicted)
    perfect = (
        checked["predictions"]
        .loc[checked["predictions"].arm.eq("G0") & checked["predictions"].climate.eq("ON")]
        .rename(columns={"year_month": "origin_month"})
        .copy()
    )
    perfect["score"], perfect["alert"] = perfect.truth.astype(float), perfect.truth.astype(bool)
    checked["reference"] = perfect
    checked["predictions"]["score"], checked["predictions"]["alert"] = 0.0, False
    adjudicated = json.loads(engine.evaluate(checked)["payloads"]["conclusions.json"])
    assert adjudicated["local_adaptation"]["status"] == "NO_RESPALDADA"
    assert adjudicated["local_adaptation"]["failing_strata"] == 6


def test_immutable_publication_rejects_overwrite_and_tamper(repo_tmp_path: Path) -> None:
    p = protocol()
    p["evaluation_years"], p["model"]["n_estimators"] = [2020], 2
    prepared: dict[str, Any] = {
        "evidence_type": "synthetic_generated_data",
        "protocol": p,
        "cohorts": {1: cohort()},
        "reference": None,
        "provenance": {"sources": {}, "execution": {"code": {}}},
    }
    result = engine.evaluate(engine.predict(engine.adapt(engine.train(prepared))))
    output = datasets.BetaBundleDataset(str(repo_tmp_path))
    output.save(result)
    published = output.load()
    with pytest.raises(DatasetError, match="replacement is forbidden"):
        output.save(result)
    path = ROOT / published["path"] / "metrics.csv"
    path.chmod(0o600)
    path.write_bytes(b"tampered")
    with pytest.raises(DatasetError, match="payload changed"):
        output.load()
