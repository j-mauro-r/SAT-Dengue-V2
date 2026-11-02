"""Generated-only NB2, temporal and publication acceptance; no private performance."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from kedro.io import DataCatalog, DatasetError, MemoryDataset
from kedro.runner import SequentialRunner
from test_canonical_model_table import panel as panel

from sat_dengue.canonical.table import CLIMATE, PREDICTORS, build_table
from sat_dengue.configuration import canonical_bytes, validate_parameters
from sat_dengue.datasets import exp_beta02 as datasets
from sat_dengue.experiments import exp_beta02 as beta
from sat_dengue.experiments import exp_beta02_engine as engine
from sat_dengue.experiments import exp_beta02_model as nb
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]
PARAMETERS = {"profile": "exp_beta02", "tracking": "disabled"}


def sources(panel: pd.DataFrame) -> dict[str, Any]:
    table, columns = build_table(panel)
    protocol = json.loads((ROOT / datasets.PROTOCOL_PATH).read_text())
    protocol["evaluation_years"] = [2022]
    protocol["model"]["minimum_training_rows"] = 4  # Small generated fixture only.
    return {
        "table": table,
        "columns": columns,
        "protocol": protocol,
        "reference": None,
        "secondary": None,
        "evidence_type": "synthetic_generated_data",
        "provenance": {"sources": {}, "execution": {"code": {}}},
    }


def run(prepared: dict[str, Any]) -> dict[str, Any]:
    return engine.policy(engine.risk(engine.forecast(engine.train(prepared))))


def test_nb2_likelihood_gradient_matches_independent_distribution() -> None:
    from scipy.stats import nbinom  # type: ignore[import-untyped]

    x = np.column_stack([np.ones(5), np.linspace(-1, 1, 5)])
    y, theta = np.array([0, 2, 1, 8, 4]), np.array([0.6, 0.2, -0.4])
    value, gradient = nb.objective(theta, x, y, 1.0)
    r, mu = np.exp(-theta[-1]), np.exp(x @ theta[:-1])
    expected = -nbinom.logpmf(y, r, r / (r + mu)).sum() + theta[1] ** 2 / 2
    assert value == pytest.approx(expected, abs=1e-10)
    numerical = []
    for i in range(len(theta)):
        step = np.zeros(len(theta))
        step[i] = 1e-5
        numerical.append(
            (nb.objective(theta + step, x, y, 1.0)[0] - nb.objective(theta - step, x, y, 1.0)[0])
            / 2e-5
        )
    np.testing.assert_allclose(gradient, numerical, rtol=1e-6, atol=1e-7)


def test_count_distribution_strict_h5_and_unavailable_t2() -> None:
    from scipy.stats import nbinom

    frame = pd.DataFrame({"dengue_notifications_count": [0.0, 1.0, 2.0]})
    model = {
        "predictors": list(frame),
        "center": [0.0],
        "scale": [1.0],
        "coefficients": [np.log(4.0), 0.0],
        "alpha": 0.5,
    }
    distribution = nb.forecast(frame, model)
    np.testing.assert_allclose(distribution["mean"], 4.0)
    np.testing.assert_allclose(nbinom.var(distribution.nb_r, distribution.nb_p), 12.0)
    result = nb.risks(distribution, [0.0, 2.0, 2.75], 1)
    np.testing.assert_allclose(
        result.score, [1 - nbinom.pmf(0, 2, 1 / 3), nbinom.sf(2, 2, 1 / 3), nbinom.sf(2, 2, 1 / 3)]
    )
    second = nb.risks(distribution, [0.0, 2.0, 2.75], 2)
    assert second.score.isna().all() and second.onset_status.eq("NO_EVALUABLE").all()
    assert second.excess_score.equals(result.excess_score)


def test_exact_count_join_preserves_targets_and_excludes_future_controls(
    panel: pd.DataFrame,
) -> None:
    source = sources(panel)
    prepared = beta.prepare(source, PARAMETERS)
    lookup = (
        source["table"]
        .set_index(["municipality_code", "year_month"])
        .dengue_notifications_count.to_dict()
    )
    for frame in prepared["cohorts"].values():
        assert frame.count_target.tolist() == [
            lookup[(m, t)]
            for m, t in frame[["municipality_code", "target_month"]].itertuples(
                index=False, name=None
            )
        ]
        assert frame.target_month.lt("2025-01").all()
        assert not set(PREDICTORS) & {"count_target", "onset_target", "target_month", "y_t1"}
    changed = copy.deepcopy(source)
    changed["table"][["y_t1", "y_t2", "p75_t1", "p75_t2"]] = 9999
    again = beta.prepare(changed, PARAMETERS)
    for horizon in prepared["cohorts"]:
        pd.testing.assert_frame_equal(prepared["cohorts"][horizon], again["cohorts"][horizon])


def test_global_chronology_and_full_reference_pairing(panel: pd.DataFrame) -> None:
    prepared = beta.prepare(sources(panel), PARAMETERS)
    for horizon, frame in prepared["cohorts"].items():
        parts = beta.role_parts(frame, 2022, prepared["protocol"])["parts"]
        assert parts["train"].target_month.le("2020-12").all()
        assert parts["selection"].year_month.ge("2020-12").all()
        assert parts["evaluation"].year_month.ge("2021-12").all()
        if horizon == 2:
            assert parts["evaluation"].target_month.ge("2022-02").all()
        base = parts["evaluation"].copy()
        old = base.rename(columns={"year_month": "origin_month", "onset_target": "truth"})
        old["score"], old["alert"], old["horizon"] = 0.2, False, horizon
        assert beta.paired(base, old, horizon, 2022) is not None
        assert beta.paired(base, old.iloc[1:], horizon, 2022) is None
        old.loc[old.index[0], "truth"] = 1 - old.iloc[0].truth
        assert beta.paired(base, old, horizon, 2022) is None
    with pytest.raises(ValueError, match="Unapproved"):
        beta.role_parts(frame, 2025, prepared["protocol"])


def test_future_labels_cannot_change_fits_transforms_probabilities_or_policy(
    panel: pd.DataFrame,
) -> None:
    prepared = beta.prepare(sources(panel), PARAMETERS)
    first = run(copy.deepcopy(prepared))
    changed = copy.deepcopy(prepared)
    for frame in changed["cohorts"].values():
        mask = frame.target_year.eq(2022)
        frame.loc[mask, "count_target"] = 9999
        frame.loc[mask, "onset_target"] = 1 - frame.loc[mask, "onset_target"]
    second = run(changed)
    assert first["policies"] == second["policies"]
    for a, b in zip(first["cells"], second["cells"], strict=True):
        assert canonical_bytes(a["model"]) == canonical_bytes(b["model"])
        values = nb.transformed(a["parts"]["train"], a["model"]["predictors"])
        np.testing.assert_allclose(a["model"]["center"], values.mean(axis=0))
    pd.testing.assert_frame_equal(
        first["forecasts"][["mean", "excess_score", "score", "alert"]],
        second["forecasts"][["mean", "excess_score", "score", "alert"]],
    )
    assert (
        first["forecasts"]
        .loc[first["forecasts"].horizon.eq(2), ["score", "alert"]]
        .isna()
        .all()
        .all()
    )
    assert set(first["cells"][0]["model"]["predictors"]) == set(PREDICTORS) - set(CLIMATE)


def test_generated_graph_determinism_and_no_overwrite(
    panel: pd.DataFrame, repo_tmp_path: Path
) -> None:
    source = sources(panel)
    expected = engine.evaluate(run(beta.prepare(copy.deepcopy(source), PARAMETERS)))
    again = engine.evaluate(run(beta.prepare(copy.deepcopy(source), PARAMETERS)))
    assert expected["payloads"] == again["payloads"]
    manifest = json.loads(expected["payloads"]["manifest.json"])
    assert manifest["real_model_fits"] == 0 and manifest["generated_model_fits"] == 4
    output = datasets.CountBundleDataset(str(repo_tmp_path))
    catalog = DataCatalog(
        {
            "exp_beta02_sources": MemoryDataset(source),
            "parameters": MemoryDataset(PARAMETERS),
            "exp_beta02_bundle": output,
        }
    )
    SequentialRunner().run(register_pipelines()["exp_beta02"], catalog)
    receipt = output.load()
    folder = ROOT / receipt["path"]
    assert (folder / "manifest.json").read_bytes() == expected["payloads"]["manifest.json"]
    with pytest.raises(DatasetError, match="replacement is forbidden"):
        output.save(expected)
    path = folder / "count_metrics.csv"
    path.chmod(0o600)
    path.write_bytes(b"altered")
    with pytest.raises(DatasetError, match="payload changed"):
        output.load()


def test_profile_and_protocol_fail_closed(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for overrides in ({"tracking": "enabled"}, {"experiment_id": "EXP01"}, {"alpha": 0.5}):
        with pytest.raises(ValueError):
            validate_parameters({**PARAMETERS, **overrides})
    graph = register_pipelines()["exp_beta02"]
    assert len(graph.nodes) == 6
    assert graph.inputs() == {"parameters", "exp_beta02_sources"}
    assert graph.outputs() == {"exp_beta02_bundle"}
    path = repo_tmp_path / "protocol.json"
    path.write_text("{}")
    monkeypatch.setattr(datasets, "PROTOCOL_PATH", str(path))
    with pytest.raises(DatasetError, match="protocol identity"):
        datasets.CountSourcesDataset().load()


def test_nonconvergence_fails_without_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    import scipy.optimize  # type: ignore[import-untyped]

    calls = []

    def failed(*args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        return SimpleNamespace(success=False, message="forced failure")

    monkeypatch.setattr(scipy.optimize, "minimize", failed)
    protocol = json.loads((ROOT / datasets.PROTOCOL_PATH).read_text())
    frame = pd.DataFrame({"count_target": [1.0] * 30, "month_of_year": [1.0] * 30})
    with pytest.raises(ValueError, match="did not converge"):
        nb.fit(frame, ["month_of_year"], protocol["model"])
    assert len(calls) == 1
