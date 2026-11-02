"""Engineering fixtures only; synthetic rows are never national scientific evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.data import national_diagnostics as diagnostics


def catalog() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "municipality_code": ["05001", "73001", "94883"],
            "department_code": ["05", "73", "94"],
            "municipality_name": ["A", "B", "C"],
            "territory_type": ["AM", "AM", "ANM"],
        }
    )


def row(**overrides: str) -> dict[str, str]:
    return {
        "COD_DPTO_R": "05",
        "COD_MUN_R": "001",
        "INI_SIN": "02/01/2020",
        "COD_EVE": "210",
        "CONSECUTIVE": "example-1",
        "FEC_NOT": "01/01/2013",
        **overrides,
    }


def local_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build small clearly synthetic sources; isolate pinned real-source identity checks."""
    monkeypatch.setattr(diagnostics, "SOURCE_IDENTITIES", {})
    (tmp_path / "data/sources").mkdir(parents=True)
    (tmp_path / "data/raw").mkdir()
    reference = catalog()
    records = [
        {
            "CODIGO_DPTO_MPIO": r.municipality_code,
            "CODIGO_DEPARTAMENTO": r.department_code,
            "CODIGO_MUNICIPIO": r.municipality_code[2:],
            "NOMBRE_MUNICIPIO": r.municipality_name,
            "CODIGO_TIPO_MUNICIPIO": r.territory_type,
        }
        for r in reference.itertuples()
    ]
    (tmp_path / diagnostics.SOURCES[3]).write_text(json.dumps({"resultado": records}))
    pd.DataFrame(
        [
            row(),
            row(),
            row(COD_MUN_R="999"),
            row(INI_SIN="invalid"),
            row(INI_SIN="01/01/2025"),
            row(COD_EVE="220"),
            row(COD_DPTO_R=""),
        ]
    ).to_csv(tmp_path / diagnostics.SOURCES[0], index=False)
    pd.DataFrame([row(COD_EVE="220", COD_DPTO_R="73")]).to_csv(
        tmp_path / diagnostics.SOURCES[1], index=False
    )
    return tmp_path


def test_independent_flags_and_no_date_corrections() -> None:
    config = diagnostics.AnalysisConfig(start_month="2020-01", end_month="2020-03")
    raw = pd.DataFrame(
        [
            row(),
            row(COD_MUN_R="999"),
            row(COD_DPTO_R="99"),
            row(COD_MUN_R=""),
            row(INI_SIN="31/02/2020"),
            row(COD_EVE="220"),
            row(COD_EVE="999"),
            row(INI_SIN="01/01/2025"),
        ]
    )
    before = raw.copy(deep=True)
    result = diagnostics.classify_notifications(raw, catalog(), "210", config)
    assert result["accepted"].tolist() == [True, False, False, False, False, False, False, False]
    assert result["territory_status"].iloc[:4].tolist() == [
        "valid",
        "historical_or_potentially_homologable",
        "requires_review",
        "incomplete_or_unknown",
    ]
    assert result.loc[0, "year_month"] == "2020-01"  # FEC_NOT differs by years, intentionally.
    pd.testing.assert_frame_equal(raw, before)


def test_streaming_conservation_zeros_and_duplicates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = local_sources(tmp_path, monkeypatch)
    config = diagnostics.AnalysisConfig(start_month="2020-01", end_month="2020-03", chunksize=1)
    before = [diagnostics.fingerprint(root / p) for p in diagnostics.SOURCES[:2]]
    result = diagnostics.run_analysis(root, config)
    assert result["summary"]["status"] == "READY_WITH_LIMITATIONS"
    tables = result["tables"]
    panel = tables["municipality_month"]
    assert len(panel) == 9
    assert panel["dengue_notifications_count"].sum() == 2
    assert panel["dengue_grave_notifications_count"].sum() == 1
    assert not panel.duplicated(["municipality_code", "year_month"]).any()
    assert (panel[list(diagnostics.COUNTS.values())] >= 0).all().all()
    empty_territory = panel.loc[panel["municipality_code"].eq("94883")]
    assert empty_territory["eligible_for_canonical_review"].all()
    assert empty_territory["dengue_notifications_count_zero_from_absence"].all()
    assert not empty_territory["dengue_notifications_count_has_rows"].any()
    duplicate = tables["duplicates"].query("source == 'dengue.csv' and category == 'exact'").iloc[0]
    assert (duplicate["groups"], duplicate["rows_in_groups"], duplicate["excess_rows"]) == (1, 2, 1)
    assert tables["record_reconciliation"]["notifications"].sum() == 8
    assert tables["territorial_totals"].iloc[0]["unresolved_notifications"] == 2
    assert [diagnostics.fingerprint(root / p) for p in diagnostics.SOURCES[:2]] == before
    assert not list((root / config.output_dir).glob(".duplicate-index-*"))


def test_chunk_size_does_not_change_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = local_sources(tmp_path, monkeypatch)
    first = diagnostics.run_analysis(root, diagnostics.AnalysisConfig(chunksize=1))
    second = diagnostics.run_analysis(root, diagnostics.AnalysisConfig(chunksize=20))
    for name in first["tables"]:
        pd.testing.assert_frame_equal(first["tables"][name], second["tables"][name])


def test_reexecution_is_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = local_sources(tmp_path, monkeypatch)
    first = diagnostics.run_analysis(root)
    second = diagnostics.run_analysis(root)
    assert first["summary"] == second["summary"]


def test_future_notifications_do_not_control_historical_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = local_sources(tmp_path, monkeypatch)
    first = diagnostics.run_analysis(root)["tables"]["municipality_month"]
    path = root / diagnostics.SOURCES[0]
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    raw = pd.concat(
        [raw, pd.DataFrame([row(INI_SIN="01/01/2026", COD_DPTO_R="94", COD_MUN_R="883")])]
    )
    raw.to_csv(path, index=False)
    second = diagnostics.run_analysis(root)["tables"]["municipality_month"]
    pd.testing.assert_frame_equal(first, second)


def test_missing_stream_never_produces_zero_calendar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = local_sources(tmp_path, monkeypatch)
    (root / diagnostics.SOURCES[1]).unlink()
    result = diagnostics.run_analysis(root)
    assert result["summary"]["status"] == "READY_FOR_LOCAL_EXECUTION"
    assert set(result["tables"]) == {"inventory"}
    assert result["summary"]["evidence"] == "NOT_SCIENTIFICALLY_VALIDATED"


def test_incorrect_identity_blocks_readiness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = local_sources(tmp_path, monkeypatch)
    monkeypatch.setattr(
        diagnostics, "SOURCE_IDENTITIES", {diagnostics.SOURCES[0]: {"sha256": "wrong"}}
    )
    assert diagnostics.run_analysis(root)["summary"]["status"] == "BLOCKED"


def test_schema_error_does_not_publish_private_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = local_sources(tmp_path, monkeypatch)
    pd.DataFrame({"COD_EVE": ["210"]}).to_csv(root / diagnostics.SOURCES[0], index=False)
    with pytest.raises(ValueError, match="Missing essential"):
        diagnostics.run_analysis(root)
    assert not list(
        (root / diagnostics.AnalysisConfig().output_dir).rglob("municipality_month.csv")
    )


@pytest.mark.parametrize(
    "settings",
    [
        {"start_month": "2021-02", "end_month": "2020-01"},
        {"end_month": "2025-01"},
        {"start_month": "2020-1"},
        {"chunksize": 0},
        {"output_dir": "../outside"},
        {"output_dir": "docs/results"},
    ],
)
def test_invalid_configuration(settings: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        diagnostics.AnalysisConfig(**settings)  # type: ignore[arg-type]


def test_rejected_event_row_is_not_absence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = local_sources(tmp_path, monkeypatch)
    path = root / diagnostics.SOURCES[0]
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    pd.concat([raw, pd.DataFrame([row(INI_SIN="01/02/2020", COD_EVE="220")])]).to_csv(
        path, index=False
    )
    calendar = diagnostics.run_analysis(root)["tables"]["municipality_month"]
    month = calendar.query("municipality_code == '05001' and year_month == '2020-02'").iloc[0]
    assert month["dengue_notifications_count"] == 0
    assert month["dengue_notifications_count_source_rows"] == 1
    assert month["dengue_notifications_count_has_rows"]
    assert not month["dengue_notifications_count_zero_from_absence"]
    assert month["requires_record_review"]
    assert not month["eligible_for_canonical_review"]


def test_missing_inputs_summary_is_strict_json(tmp_path: Path) -> None:
    result = diagnostics.run_analysis(tmp_path)
    summary = result["summary"]
    path = tmp_path / diagnostics.AnalysisConfig().output_dir / summary["execution_id"]

    def reject_constant(value: str) -> None:
        raise AssertionError(f"Invalid JSON constant: {value}")

    parsed = json.loads(
        (path / "execution_summary.json").read_text(), parse_constant=reject_constant
    )
    assert parsed == summary


def test_empty_stream_does_not_publish_calendar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = local_sources(tmp_path, monkeypatch)
    path = root / diagnostics.SOURCES[1]
    pd.DataFrame(columns=[*diagnostics.ESSENTIAL, "CONSECUTIVE"]).to_csv(path, index=False)
    result = diagnostics.run_analysis(root)
    assert result["summary"]["status"] == "BLOCKED"
    assert "municipality_month" not in result["tables"]
