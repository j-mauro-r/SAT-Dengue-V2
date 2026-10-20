from __future__ import annotations

from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data/interim/stage2_monthly_sensitivity_associations"


@pytest.mark.skipif(
    not OUT_DIR.exists(), reason="Stage 2 monthly sensitivity outputs not generated"
)
def test_anomaly_cardinality_reference_matches() -> None:
    card = pd.read_csv(OUT_DIR / "anomaly_cardinality_summary.csv")
    values = dict(zip(card["metric"], card["value"], strict=False))
    assert int(values["total_anomalies"]) == 8556
    assert int(values["same_year_month"]) == 784
    assert int(values["different_year_month"]) == 7772
    assert int(values["matches_reference"]) == 1


@pytest.mark.skipif(
    not OUT_DIR.exists(), reason="Stage 2 monthly sensitivity outputs not generated"
)
def test_scenario_cardinality_and_monotonic_exclusion() -> None:
    s1 = pd.read_csv(OUT_DIR / "monthly_panel_s1.csv")
    s2 = pd.read_csv(OUT_DIR / "monthly_panel_s2.csv")
    s3 = pd.read_csv(OUT_DIR / "monthly_panel_s3.csv")

    assert len(s1) == len(s2) == len(s3)
    assert s1[["mun_full", "year_month"]].equals(s2[["mun_full", "year_month"]])
    assert s1[["mun_full", "year_month"]].equals(s3[["mun_full", "year_month"]])

    assert int((s2["dengue_count"] > s1["dengue_count"]).sum()) == 0
    assert int((s3["dengue_count"] > s1["dengue_count"]).sum()) == 0

    assert int(s1["dengue_count"].sum() - s2["dengue_count"].sum()) == 7772
    assert int(s1["dengue_count"].sum() - s3["dengue_count"].sum()) == 8556


@pytest.mark.skipif(
    not OUT_DIR.exists(), reason="Stage 2 monthly sensitivity outputs not generated"
)
def test_field_inventory_is_complete() -> None:
    inv = pd.read_csv(OUT_DIR / "field_analytic_eligibility.csv")
    assert inv["field"].nunique() == 69
    assert {"analytic_role", "monthly_representation", "eligible_for_association"}.issubset(
        inv.columns
    )
