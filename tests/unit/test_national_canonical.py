"""Focused engineering fixtures; real national parity is a separate local gate."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from pandas.testing import assert_frame_equal  # type: ignore[import-untyped]

from sat_dengue.canonical.national import (
    aggregate_view,
    build_national,
    compare_baseline,
    eligibility_report,
    predictor_matrix,
)
from sat_dengue.canonical.table import CLIMATE, COUNTS, KEYS, build_table
from sat_dengue.config_loader import CATALOG, ValidatedConfigLoader
from sat_dengue.configuration import NATIONAL_AUTHORITY, validate_parameters
from sat_dengue.data.consolidation import CLIMATE_DAILY_VARIABLES, compute_y_labels
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def inputs() -> tuple[Any, ...]:
    contract = json.loads((ROOT / NATIONAL_AUTHORITY["path"]).read_text())
    periods = pd.period_range("2006-06", "2024-12", freq="M")
    rows = []
    for code in ("05001", "50001", "73001"):
        for i, period in enumerate(periods):
            row = {
                "municipality_code": code,
                "year_month": str(period),
                "department_code": code[:2],
                "municipality_name": "Fixture",
                COUNTS[0]: i % 17,
                COUNTS[1]: i % 3,
                COUNTS[2]: i % 17 + i % 3,
                "in_epi_coverage": True,
                "epi_count_status": "zero_in_coverage"
                if i % 17 + i % 3 == 0
                else "records_present",
                "expected_days_in_month": period.days_in_month,
                "climate_days_observed": period.days_in_month,
                "requires_record_review": False,
                "historical_territory_applicability": "UNVERIFIED",
            }
            for name in COUNTS[:2]:
                row[f"{name}_zero_from_absence"] = row[name] == 0
            for name in CLIMATE:
                row[name] = -3.0 if "evaporation" in name else 3.0
                row[f"{name}_valid_days"] = period.days_in_month
            rows.append(row)
    panel = pd.DataFrame(rows)
    reference = panel.loc[panel.department_code.isin(["50", "73"])].copy()
    reference, _ = compute_y_labels(reference)
    baseline, _ = build_table(reference)
    calendar = panel.loc[panel.year_month.ge("2011-06")].copy()
    monthly = calendar[
        [
            *KEYS,
            "expected_days_in_month",
            "climate_days_observed",
            *CLIMATE,
            *(f"{n}_valid_days" for n in CLIMATE),
        ]
    ].copy()
    calendar = calendar.drop(
        columns=[
            "in_epi_coverage",
            "epi_count_status",
            COUNTS[2],
            *[n for n in monthly if n not in KEYS],
        ]
    )
    contract["window"].update(municipalities=3, rows=len(calendar))
    return calendar, monthly, baseline, contract


def test_grid_h5_warmup_roles_counts_and_reference_parity(inputs: tuple[Any, ...]) -> None:
    calendar, monthly, baseline, contract = inputs
    table, schema = build_national(*inputs)
    assert len(table) == 3 * 163
    assert not table.duplicated(KEYS).any()
    assert table[COUNTS[0]].sum() == calendar[COUNTS[0]].sum()
    assert (
        table.loc[
            table.municipality_code.eq("05001") & table.year_month.eq("2011-06"), "p75_canal_t"
        ]
        .isna()
        .all()
    )
    assert (
        table.loc[
            table.municipality_code.eq("50001") & table.year_month.eq("2011-06"), "p75_canal_t"
        ]
        .notna()
        .all()
    )
    assert table.loc[table.year_month.eq("2024-12"), ["onset_T1", "onset_T2"]].isna().all().all()
    report = compare_baseline(table, baseline)
    assert report.material_unexplained_rows.sum() == 0
    assert not set(predictor_matrix(table, contract, True)) & set(schema["column_roles"]["target"])
    assert eligibility_report(table)["real_model_fits"] == 0
    broken = calendar.iloc[1:]
    with pytest.raises(ValueError, match="calendar"):
        build_national(broken, monthly, baseline, contract)


def test_future_values_cannot_change_origin_predictors(inputs: tuple[Any, ...]) -> None:
    before, _ = build_national(*inputs)
    calendar, monthly, baseline, contract = copy.deepcopy(inputs)
    future = calendar.year_month.gt("2020-12")
    calendar.loc[future, COUNTS[0]] = 10000
    monthly.loc[monthly.year_month.gt("2020-12"), CLIMATE] = 90000.0
    after, _ = build_national(calendar, monthly, baseline, contract)
    origin = before.year_month.le("2020-12")
    assert_frame_equal(
        predictor_matrix(before, contract, True).loc[origin],
        predictor_matrix(after, contract, True).loc[origin],
    )
    poisoned = copy.deepcopy(contract)
    poisoned["columns"][
        next(i for i, f in enumerate(poisoned["columns"]) if f["name"] == COUNTS[0])
    ]["available_month_offset"] = 1
    with pytest.raises(ValueError, match="Future predictor"):
        predictor_matrix(before, poisoned, True)


def _daily() -> pd.DataFrame:
    rows = []
    for code in ("05001", "88001"):
        for date in pd.date_range("2020-01-01", "2020-01-31"):
            rows.append(
                {
                    "date": str(date.date()),
                    "mpio_cdpmp": code,
                    "dpto_ccdgo": code[:2],
                    **{n: "" if code == "88001" else "2.0" for n in CLIMATE_DAILY_VARIABLES},
                }
            )
    return pd.DataFrame(rows)


def test_monthly_aggregation_handles_chunk_boundaries_and_all_missing() -> None:
    daily = _daily()
    chunks = (daily.iloc[i : i + 13] for i in range(0, len(daily), 13))
    result = aggregate_view(chunks, "2020-01", "2020-01")
    island = result.loc[result.municipality_code.eq("88001")]
    mainland = result.loc[result.municipality_code.eq("05001")]
    assert island[CLIMATE].isna().all().all()
    assert mainland.rain_mm_month_sum.item() == 62
    assert mainland.temp_mean_c_month_mean.item() == 2
    partial = aggregate_view([daily.drop(index=0)], "2020-01", "2020-01")
    assert partial.loc[partial.municipality_code.eq("05001"), CLIMATE].isna().all().all()
    with pytest.raises(ValueError, match="Duplicate"):
        aggregate_view([pd.concat([daily, daily.iloc[:1]])], "2020-01", "2020-01")
    with pytest.raises(ValueError, match="Repeated completed"):
        aggregate_view([daily, daily], "2020-01", "2020-01")


def test_mismatched_coverage_and_unexplained_reference_difference_block(
    inputs: tuple[Any, ...],
) -> None:
    calendar, monthly, baseline, contract = copy.deepcopy(inputs)
    monthly.loc[monthly.index[0], f"{CLIMATE[0]}_valid_days"] = 0
    with pytest.raises(ValueError, match="coverage"):
        build_national(calendar, monthly, baseline, contract)
    table, _ = build_national(*inputs)
    table.loc[table.municipality_code.eq("50001"), COUNTS[0]] += 1
    assert compare_baseline(table, baseline).material_unexplained_rows.sum() > 0


def test_independent_kedro_route_and_strict_profile() -> None:
    pipeline = register_pipelines()["canonical_model_table_national_v1"]
    assert len(pipeline.nodes) == 1
    assert pipeline.inputs() == {"national_canonical_sources", "parameters"}
    assert "canonical_model_table_national_v1" not in register_pipelines()["replay"].outputs()
    assert CATALOG["canonical_model_table_national_v1"]["filepath"].endswith(
        "canonical_model_table_national_v1"
    )
    assert ValidatedConfigLoader(conf_source=str(ROOT / "conf"))["catalog"] == CATALOG
    assert validate_parameters(
        {"profile": "canonical_model_table_national_v1", "tracking": "disabled"}
    )
    with pytest.raises(ValueError, match="disabled tracking"):
        validate_parameters({"profile": "canonical_model_table_national_v1", "tracking": "enabled"})
