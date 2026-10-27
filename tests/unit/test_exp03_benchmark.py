"""Generated-only consumed-year transport integration and complete-grid admission."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from exp03_benchmark_fixture import _coverage, _fixture

from sat_dengue.experiments import exp01
from sat_dengue.experiments.exp03_benchmark import _evaluate_frozen_grid, evaluate_benchmark
from sat_dengue.experiments.exp03_revision import CLIMATE_RECIPES, cell_counts


def test_native_transport_has_annual_common_month_and_recomputed_aggregate(
    repo_tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = repo_tmp_path / "terminal"
    panel, contract, design, specs, identity = _fixture(root)

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Consumed benchmark reached fit/calibration/selection")

    monkeypatch.setattr("sat_dengue.model_training.candidate_families.fit_model", forbidden)
    monkeypatch.setattr("sat_dengue.model_evaluation.calibration._fit_sigmoid", forbidden)
    monkeypatch.setattr("sat_dengue.experiments.exp03_evaluation.select_threshold", forbidden)
    result = _evaluate_frozen_grid(panel, contract, design, root, _coverage(), identity, specs)
    assert result["status"] == "evaluable"
    assert result["identities_verified_before_after"]
    assert set(result["execution_counters"].values()) == {0}
    assert result["used_for_selection"] is False
    assert result["G5"] == "NOT_APPROVED"
    assert result["champion"] == "not_selected"
    assert len(result["transport_2024_2025"]) == 10
    native = pd.DataFrame(result["benchmark_predictions"])
    assert set(native.transmission_profile) == {"low", "high"}
    assert native.year_month.ge("2023-12").all()
    assert not native.used_for_selection.any()
    rows = result["transport_2024_2025"]
    for row in rows:
        if row["view"] != "annual":
            continue
        local = native.loc[
            native.cell_id.eq(row["cell_id"]) & native.target_year.eq(row["target_year"])
        ]
        covered = local.loc[local.monitored, "onset_target"].sum()
        eligible = local.loc[
            local.monitored & local.eligible_at_t.fillna(False), "onset_target"
        ].sum()
        assert row["metrics"]["covered_onsets"] == covered
        assert row["metrics"]["eligible_onsets"] == eligible
        assert row["metrics"]["covered_onsets"] >= row["metrics"]["eligible_onsets"]
    h2 = [r for r in rows if r["horizon"] == 2 and r["view"] == "annual"]
    assert "2024-01" not in h2[0]["target_months"]
    assert "2025-01" in h2[1]["target_months"]
    assert len(h2[0]["common_calendar_months"]) == 11
    for horizon in (1, 2):
        annual = [r for r in rows if r["horizon"] == horizon and r["view"] == "annual"]
        pooled = next(
            r for r in rows if r["horizon"] == horizon and r["view"] == "count_pooled_descriptive"
        )
        assert pooled["metrics"]["real_onsets"] == sum(r["metrics"]["real_onsets"] for r in annual)
        assert pooled["metrics"]["false_alerts"] == sum(
            r["metrics"]["false_alerts"] for r in annual
        )
        rate = pooled["metrics"]["false_alerts_per_monitored_municipality_year"]
        assert rate == pytest.approx(
            pooled["metrics"]["false_alerts"]
            / sum(r["metrics"]["monitored_exposure"] for r in annual)
        )
    assert {r["target_year"] for r in result["performance_by_group"]} == {2024, 2025}


def test_missing_provenance_preserves_explicit_terminal_status_without_prepare(
    repo_tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = repo_tmp_path / "terminal"
    panel, contract, design, specs, identity = _fixture(root)

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Unverified maturity must not reach feature preparation")

    monkeypatch.setattr("sat_dengue.experiments.exp03_benchmark.prepare", forbidden)
    result = _evaluate_frozen_grid(panel, contract, design, root, {}, identity, specs)
    assert result["status"] == "not_evaluable"
    assert len(result["transport_2024_2025"]) == 4
    assert {r["cell_id"] for r in result["transport_2024_2025"]} == {exp01.digest(s) for s in specs}
    assert all(r["status"] == "not_evaluable" for r in result["transport_2024_2025"])
    assert not result["benchmark_predictions"]


def test_public_complete_grid_rejects_shortlist_and_manifest_tampering(repo_tmp_path: Path) -> None:
    root = repo_tmp_path / "terminal"
    panel, contract, design, specs, identity = _fixture(root)
    assert cell_counts(design)["terminal"] == 102
    with pytest.raises(ValueError, match="every declared terminal"):
        evaluate_benchmark(panel, contract, design, root, _coverage(), identity)
    with pytest.raises(ValueError, match="manifest changed"):
        _evaluate_frozen_grid(panel, contract, design, root, _coverage(), "different", specs)


def test_stored_labels_do_not_feed_benchmark_predictions(repo_tmp_path: Path) -> None:
    root = repo_tmp_path / "terminal"
    panel, contract, design, specs, identity = _fixture(root)
    first = _evaluate_frozen_grid(panel, contract, design, root, _coverage(), identity, specs)
    changed = panel.copy()
    # These externally supplied label fields are not scientific inputs. Raw counts
    # remain fixed; changing them legitimately changes later-origin predictors.
    changed["onset_target"] = 1
    changed["excess_target"] = 1
    second = _evaluate_frozen_grid(changed, contract, design, root, _coverage(), identity, specs)
    cols = ["cell_id", "municipality_code", "year_month", "raw_score", "score", "alert"]
    pd.testing.assert_frame_equal(
        pd.DataFrame(first["benchmark_predictions"])[cols],
        pd.DataFrame(second["benchmark_predictions"])[cols],
    )


def test_missing_variant_union_features_abstain_without_shrinking_monitored_exposure(
    repo_tmp_path: Path,
) -> None:
    root = repo_tmp_path / "terminal"
    panel, contract, design, specs, identity = _fixture(root)
    baseline = _evaluate_frozen_grid(panel, contract, design, root, _coverage(), identity, specs)
    changed = panel.copy()
    # Even V00 must retain the same complete-union cohort as every other variant.
    climate = list({source for source, _ in CLIMATE_RECIPES})
    changed.loc[changed.year_month.ge("2025-01"), climate] = np.nan
    stressed = _evaluate_frozen_grid(changed, contract, design, root, _coverage(), identity, specs)
    for horizon in (1, 2):

        def annual(result: dict[str, Any], h: int = horizon) -> dict[str, Any]:
            return next(
                row
                for row in result["transport_2024_2025"]
                if row["horizon"] == h and row["view"] == "annual" and row["target_year"] == 2025
            )

        first, second = annual(baseline), annual(stressed)
        assert second["metrics"]["monitored_exposure"] == first["metrics"]["monitored_exposure"]
        assert second["metrics"]["eligible_exposure"] == first["metrics"]["eligible_exposure"]
        assert second["common_months"] < first["common_months"]
        assert second["abstentions"] > first["abstentions"]
