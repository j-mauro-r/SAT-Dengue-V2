"""Focused V4 regressions: no fitting, tracking, experiments or private data."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from kedro.io import DatasetError

from sat_dengue.canonical.national import build_national
from sat_dengue.canonical.national_v4 import (
    CONSUMED,
    DATASET,
    add_temporal_metadata,
    aggregate_notifications,
    build_v4,
    compare_tables,
)
from sat_dengue.canonical.table import CLIMATE, COUNTS, KEYS, build_table
from sat_dengue.config_loader import CATALOG, ValidatedConfigLoader
from sat_dengue.configuration import NATIONAL_AUTHORITY, canonical_bytes, validate_parameters
from sat_dengue.data.consolidation import compute_y_labels
from sat_dengue.datasets.national_v4 import V4BundleDataset, assemble_v4
from sat_dengue.pipeline_registry import register_pipelines
from sat_dengue.training_preparation.contract import PreparationError
from sat_dengue.training_preparation.roles import LEARNED_ROLES, require_learnable
from sat_dengue.training_preparation.serialization import bytes_record

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def v4_sources() -> dict[str, Any]:
    contract = json.loads((ROOT / NATIONAL_AUTHORITY["path"]).read_text())
    rows = []
    for code in ("05001", "50001", "73001"):
        for i, period in enumerate(pd.period_range("2006-06", "2026-01", freq="M")):
            count, severe = i % 17, i % 3
            row = {
                "municipality_code": code,
                "year_month": str(period),
                "department_code": code[:2],
                "municipality_name": "Fixture",
                COUNTS[0]: count,
                COUNTS[1]: severe,
                COUNTS[2]: count + severe,
                "requires_record_review": False,
                "historical_territory_applicability": "UNVERIFIED",
                "in_epi_coverage": True,
                "epi_count_status": "records_present" if count + severe else "zero_in_coverage",
                "expected_days_in_month": period.days_in_month,
                "climate_days_observed": period.days_in_month,
            }
            row.update({f"{n}_zero_from_absence": row[n] == 0 for n in COUNTS[:2]})
            for name in CLIMATE:
                row[name] = -2.0 if "evaporation" in name else 2.0
                row[f"{name}_valid_days"] = period.days_in_month
            rows.append(row)
    panel = pd.DataFrame(rows)
    regional, _ = compute_y_labels(panel.loc[panel.department_code.isin(["50", "73"])])
    regional, _ = build_table(regional)
    calendar = panel.loc[panel.year_month.between("2011-06", "2025-12")].copy()
    monthly_names = [
        "expected_days_in_month",
        "climate_days_observed",
        *CLIMATE,
        *(f"{n}_valid_days" for n in CLIMATE),
    ]
    monthly = calendar[[*KEYS, *monthly_names]].copy()
    calendar = calendar.drop(
        columns=[*monthly_names, COUNTS[2], "in_epi_coverage", "epi_count_status"]
    )
    contract["window"].update(municipalities=3, rows=3 * 163)
    national, schema = build_national(
        calendar.loc[calendar.year_month.le("2024-12")],
        monthly.loc[monthly.year_month.le("2024-12")],
        regional,
        contract,
    )
    contract["window"].update(end="2025-12", months=175, rows=3 * 175)
    return {
        "calendar": calendar,
        "monthly": monthly,
        "regional": regional,
        "national": national,
        "columns": schema["columns"],
        "contract": contract,
        "reconciliation": {},
        "provenance": {
            "sources": {},
            "execution": {"code": {}, "git_revision": "fixture"},
            "generated_at": "2026-11-07T00:00:00Z",
        },
    }


def _build(sources: dict[str, Any]) -> dict[str, Any]:
    return build_v4(
        *(
            sources[n]
            for n in ("calendar", "monthly", "regional", "national", "contract", "columns")
        )
    )


def test_grid_common_parity_types_missingness_and_maturity(v4_sources: dict[str, Any]) -> None:
    result = _build(v4_sources)
    table = result["table"]
    assert len(table) == 3 * 175
    assert table.year_month.min() == "2011-06" and table.year_month.max() == "2025-12"
    assert not table.duplicated(KEYS).any()
    assert table.groupby("municipality_code").year_month.nunique().eq(175).all()
    assert [f["name"] for f in result["columns"]][: len(v4_sources["columns"])] == list(
        v4_sources["national"]
    )
    assert not {"INI_SIN", "COD_DPTO_R", "COD_MUN_R", "ID", "patient_id"} & set(table)
    for h, immature_months in ((1, 1), (2, 2)):
        outside = table[f"target_period_t{h}"].gt("2025-12")
        assert outside.sum() == 3 * immature_months
        assert table.loc[outside, f"maturity_t{h}"].eq("target_outside_panel").all()
        assert table.loc[outside, [f"y_t{h}", f"onset_T{h}"]].isna().all().all()
        assert table.loc[~outside, f"maturity_t{h}"].eq("mature").all()
        assert table.loc[table.year_month.ge("2025-01"), f"scientific_role_t{h}"].eq(CONSUMED).all()
    assert all(r["material_rows"] == 0 for r in result["parity"])
    regional_edges = [r for r in result["parity"] if r["explained_boundary_rows"]]
    assert len(regional_edges) == 8
    assert {r["explained_boundary_rows"] for r in regional_edges} == {2}
    assert all(
        r["cause"] == "necessary_2026_target_exclusion_from_V4_panel" for r in regional_edges
    )
    assert any(r["changed_rows"] for r in result["edge_changes"])
    assert len(result["temporal_roles"]) == 2 * len(table)
    poisoned = table.copy()
    poisoned.loc[poisoned.year_month.eq("2025-12"), "y_t1"] = 1
    with pytest.raises(ValueError, match="Invented future"):
        add_temporal_metadata(poisoned)


def test_parity_never_waives_missingness_material_counts_or_schema(
    v4_sources: dict[str, Any],
) -> None:
    national = v4_sources["national"]
    for name, value in ((COUNTS[0], 999999), (CLIMATE[0], 2.1), ("y_t1", pd.NA)):
        bad = national.copy()
        index = bad.index[bad.y_t1.notna()][0]
        bad.loc[index, name] = value
        with pytest.raises(ValueError, match="material parity"):
            compare_tables(bad, national, label="fixture")
    with pytest.raises(ValueError, match="keys"):
        compare_tables(national.iloc[1:], national, label="fixture")
    with pytest.raises(ValueError, match="calendar"):
        sources = copy.deepcopy(v4_sources)
        sources["calendar"] = sources["calendar"].iloc[1:]
        _build(sources)


def test_raw_aggregation_preserves_duplicates_residence_onset_and_review() -> None:
    catalog = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "department_code": ["50"],
            "municipality_name": ["Fixture"],
        }
    )
    # Duplicate notifications count twice; unresolved geography is excluded and audited.
    raw = pd.DataFrame(
        {
            "COD_DPTO_R": ["50", "50", "99", "50", "50"],
            "COD_MUN_R": ["1"] * 5,
            "INI_SIN": ["10/12/2025"] * 3 + ["01/01/2026", "10/12/2025"],
            "COD_EVE": ["210"] * 4 + ["220"],
        }
    )
    severe = raw.iloc[:1].assign(COD_EVE="220")
    calendar, report = aggregate_notifications(
        [("210", raw.iloc[:2]), ("210", raw.iloc[2:]), ("220", severe)], catalog
    )
    last = calendar.loc[calendar.year_month.eq("2025-12")]
    assert last[COUNTS[0]].item() == 2 and last[COUNTS[1]].item() == 1
    assert last.requires_record_review.item()
    assert calendar.loc[calendar.year_month.eq("2025-11"), COUNTS[:2]].eq(0).all().all()
    assert report["streams"]["210"]["unassigned_in_window"] == 1
    assert report["streams"]["210"]["outside_panel"] == 1


@pytest.mark.parametrize("role", LEARNED_ROLES)
@pytest.mark.parametrize("origin,target", [("2025-01", "2025-02"), ("2024-12", "2025-01")])
def test_all_learned_roles_refuse_consumed_origins_or_targets(
    role: str, origin: str, target: str
) -> None:
    frame = pd.DataFrame({"year_month": [origin], "target_period_t1": [target]})
    with pytest.raises(PreparationError, match="Consumed 2025"):
        require_learnable(frame, 1, role)
    require_learnable(
        pd.DataFrame({"year_month": ["2024-10"], "target_period_t1": ["2024-11"]}), 1, role
    )


def test_unknown_learning_metadata_and_missing_chronology_fail_closed() -> None:
    frame = pd.DataFrame(
        {"year_month": ["2024-10"], "target_period_t1": ["2024-11"], "maturity_t1": ["unknown"]}
    )
    with pytest.raises(PreparationError, match="metadata"):
        require_learnable(frame, 1, "training")
    with pytest.raises(PreparationError, match="requires"):
        require_learnable(frame.drop(columns="year_month"), 1, "training")


def test_reproducible_payload_manifest_and_immutable_publisher(
    v4_sources: dict[str, Any], repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parameters = {"profile": DATASET, "tracking": "disabled"}
    first = assemble_v4(v4_sources, parameters)
    second = assemble_v4(v4_sources, parameters)
    assert first["payloads"] == second["payloads"]
    manifest = json.loads(first["payloads"]["manifest.json"])
    assert manifest["rows"] == 525 and manifest["columns"] == len(v4_sources["columns"]) + 7
    assert manifest["table"] == bytes_record(first["payloads"][DATASET + ".csv"])
    effective = json.loads(first["payloads"]["contract.json"])
    assert effective["schema"].endswith("v4")
    assert len(effective["columns"]) == manifest["columns"]
    assert "No post-2024" not in effective["history"]
    assert "target<2025" not in effective["eligibility"]
    publisher = V4BundleDataset(str(repo_tmp_path / "success"))
    publisher.save(first)
    assert publisher.load()["manifest"] == manifest
    with pytest.raises(DatasetError, match="already exists"):
        publisher.save(first)
    tampered = copy.deepcopy(first)
    tampered["payloads"][DATASET + ".csv"] += b"tamper"
    with pytest.raises(DatasetError, match="disagree"):
        V4BundleDataset(str(repo_tmp_path / "tamper")).save(tampered)
    import sat_dengue.datasets.legacy_preparation.persistence as persistence

    def fail(*args: Any) -> None:
        raise OSError("injected atomic failure")

    monkeypatch.setattr(persistence.os, "rename", fail)
    with pytest.raises(DatasetError, match="atomic failure"):
        V4BundleDataset(str(repo_tmp_path / "failure")).save(first)
    assert list((repo_tmp_path / "failure").iterdir()) == []
    assert canonical_bytes({k: v for k, v in manifest.items() if k != "bundle_id"})


def test_independent_graph_and_disabled_tracking_profile() -> None:
    pipelines = register_pipelines()
    assert pipelines[DATASET].inputs() == {"national_v4_sources", "parameters"}
    for name in ("__default__", "replay", "training_replay", "preparation"):
        if name in pipelines:
            assert DATASET not in pipelines[name].outputs()
    assert ValidatedConfigLoader(conf_source=str(ROOT / "conf"))["catalog"] == CATALOG
    assert validate_parameters({"profile": DATASET, "tracking": "disabled"})
    with pytest.raises(ValueError, match="disabled tracking"):
        validate_parameters({"profile": DATASET, "tracking": "enabled"})
