"""Synthetic rejection tests for preparation boundaries; no private inputs required."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

# Milestone 2: exact calendar antecedents and publication boundaries.
from scripts.training_preparation import development as development_module
from scripts.training_preparation.contract import (
    CONTRACT_PATH,
    PreparationConfig,
    PreparationError,
    read_json,
    validate_predictors,
)
from scripts.training_preparation.development import build_development, serialize_table
from scripts.training_preparation.eligibility import build_controls, policy_from_years
from scripts.training_preparation.features import DERIVED_COLUMNS, KEYS, derive_features
from scripts.training_preparation.persistence import json_bytes, publish_bundle, verify_bundle
from scripts.training_preparation.pipeline import (
    PreparationResult,
    fingerprint,
    prepare_inputs,
    read_panel,
)
from scripts.training_preparation.validation import validate_panel, validate_roles

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def contract() -> dict[str, Any]:
    return read_json(ROOT / CONTRACT_PATH)


@pytest.fixture
def coverage() -> dict[str, Any]:
    return dict(
        panel_month_start="2020-01",
        panel_month_end="2020-03",
        epi_coverage_start_month="2020-01",
        epi_coverage_end_month="2020-03",
        climate_coverage_start_month="2020-01",
        climate_coverage_end_month="2020-03",
        scope_municipalities=2,
    )


@pytest.fixture
def panel(contract: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for municipality in ("50001", "73001"):
        for period in pd.period_range("2020-01", "2020-03", freq="M"):
            row: dict[str, Any] = {}
            for field in contract["schema"]:
                dtype = field["dtype"].lower()
                row[field["name"]] = (
                    None
                    if field["nullable"]
                    else True
                    if dtype == "bool"
                    else 0
                    if dtype in ("float64", "int64")
                    else ""
                )
            row.update(
                municipality_code=municipality,
                department_code=municipality[:2],
                municipality_name="Synthetic",
                year_month=str(period),
                in_epi_coverage=True,
                epi_count_status="zero_in_coverage",
                expected_days_in_month=period.days_in_month,
                climate_days_observed=period.days_in_month,
            )
            for c in row:
                if c.endswith("_valid_days"):
                    row[c] = period.days_in_month
                    row[c.removesuffix("_valid_days")] = 1.0
            for h in (1, 2):
                row[f"target_period_t{h}"] = str(period + h)
                row[f"y_evaluable_t{h}"] = False
                row[f"y_status_t{h}"] = "insufficient_history"
            rows.append(row)
    frame = pd.DataFrame(rows)
    for field in contract["schema"]:
        dtype = field["dtype"].lower()
        if dtype in ("float64", "int64"):
            frame[field["name"]] = frame[field["name"]].astype(
                "Float64" if dtype == "float64" else "Int64"
            )
    return frame


def test_valid_input_is_not_mutated(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any]
) -> None:
    before = panel.copy(deep=True)
    report = validate_panel(panel, contract, coverage)
    assert report["rows"] == 6
    assert report["municipalities"] == 2
    pd.testing.assert_frame_equal(panel, before)


@pytest.mark.parametrize("fault", ["missing", "unexpected", "wrong_type", "null", "infinite"])
def test_bad_schema_rejected(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any], fault: str
) -> None:
    if fault == "missing":
        panel = panel.drop(columns="year_month")
    elif fault == "unexpected":
        panel["future_count"] = 0
    elif fault == "wrong_type":
        panel["dengue_notifications_count"] = "1"
    elif fault == "null":
        panel.loc[0, "municipality_code"] = None
    else:
        panel.loc[0, "rain_mm_month_sum"] = float("inf")
    with pytest.raises(PreparationError):
        validate_panel(panel, contract, coverage)


def test_duplicate_keys_rejected(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any]
) -> None:
    with pytest.raises(PreparationError, match="Duplicate"):
        validate_panel(pd.concat([panel, panel.iloc[[0]]]), contract, coverage)


@pytest.mark.parametrize("removed", [[1], [0], [0, 1, 2]])
def test_month_gap_edge_and_missing_municipality_rejected(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any], removed: list[int]
) -> None:
    with pytest.raises(PreparationError, match="support|coverage"):
        validate_panel(panel.drop(index=removed), contract, coverage)


@pytest.mark.parametrize(
    "column",
    [
        "y_t1",
        "y_t2",
        "target_period_t1",
        "p75_t2",
        "history_valid_years_t1",
        "y_evaluable_t2",
        "municipality_code",
        "total_notifications_count",
        "future_observed_dengue",
        "p75_canal_t",
    ],
)
def test_forbidden_predictors_rejected(contract: dict[str, Any], column: str) -> None:
    with pytest.raises(PreparationError, match="Forbidden"):
        validate_predictors([column], contract)


def test_edited_role_contract_cannot_admit_target(contract: dict[str, Any]) -> None:
    altered = copy.deepcopy(contract)
    altered["roles"]["predictors"].append("y_t1")
    with pytest.raises(PreparationError):
        validate_roles(altered)


@pytest.mark.parametrize(
    "column,value",
    [
        ("zona_canal_t", "unknown"),
        ("year_month", "2020-13"),
        ("in_epi_coverage", False),
        ("rain_mm_month_sum_valid_days", 2),
        ("y_t1", 1),
        ("target_period_t2", "2021-03"),
        ("dengue_notifications_count", -1),
        ("department_code", "50"),
    ],
)
def test_semantic_faults_rejected(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any], column: str, value: Any
) -> None:
    panel.loc[5, column] = value
    with pytest.raises(PreparationError):
        validate_panel(panel, contract, coverage)


def test_read_csv_preserves_empty_traces_and_zero(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any], tmp_path: Path
) -> None:
    path = tmp_path / "panel.csv"
    panel.to_csv(path, index=False)
    restored = read_panel(path, contract)
    assert restored["history_periods_used_t1"].eq("").all()
    assert restored["dengue_notifications_count"].eq(0).all()
    assert restored["y_t1"].isna().all()
    validate_panel(restored, contract, coverage)
    path.write_text(path.read_text().replace("True", "garbage", 1))
    with pytest.raises(PreparationError, match="Invalid CSV"):
        read_panel(path, contract)


def test_reader_rejects_duplicate_header(tmp_path: Path, contract: dict[str, Any]) -> None:
    path = tmp_path / "panel.csv"
    path.write_text("municipality_code,municipality_code\n50001,50001\n")
    with pytest.raises(PreparationError, match="Duplicate CSV"):
        read_panel(path, contract)


def test_input_path_cannot_escape_repository(tmp_path: Path) -> None:
    with pytest.raises(PreparationError, match="outside repository"):
        PreparationConfig(tmp_path).resolve("../private.csv")


def test_code_only_notebook_delegates_without_consolidation() -> None:
    notebook = read_json(ROOT / "notebooks/04_training_preparation_pipeline.ipynb")
    assert all(c["cell_type"] == "code" for c in notebook["cells"])
    source = "".join("".join(c["source"]) for c in notebook["cells"])
    assert "build_temporal(config)" in source
    assert "stage2_consolidated_dataset_pipeline" not in source
    for cell in notebook["cells"]:
        compile("".join(cell["source"]), "notebook04", "exec")


def test_manifest_tamper_detected_before_parsing(tmp_path: Path, contract: dict[str, Any]) -> None:
    contract_path = tmp_path / CONTRACT_PATH
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(json.dumps(contract))
    panel_path = tmp_path / "data/processed/dengue_y_dengue_grave.csv"
    panel_path.parent.mkdir(parents=True)
    panel_path.write_text("synthetic\n")
    expected = fingerprint(panel_path)
    panel_path.write_text("tampered\n")
    manifest_path = tmp_path / PreparationConfig(tmp_path).manifest_path
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "outputs": {
                    "dengue_y_dengue_grave": {
                        "path": str(panel_path.relative_to(tmp_path)),
                        **expected,
                    }
                }
            }
        )
    )
    with pytest.raises(PreparationError, match="fingerprint mismatch"):
        prepare_inputs(PreparationConfig(tmp_path))


@pytest.fixture
def feature_history(contract: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for code, counts in (("50001", [10, 7, 13, 19]), ("73001", [100, 200, 300, 400])):
        for month, count in zip(("2019-11", "2019-12", "2020-01", "2020-02"), counts, strict=True):
            row: dict[str, Any] = {"municipality_code": code, "year_month": month}
            row.update({c: float(count) for c in contract["roles"]["predictors"]})
            row["zona_canal_t"] = "ALERTA" if code == "50001" else "EXCESO"
            row["dengue_grave_notifications_count"] = count / 10
            row["total_evaporation_mm_month_sum_ecmwf"] = -float(count)
            row["wind_u_ms_month_mean"] = -float(count)
            rows.append(row)
    return pd.DataFrame(rows).sample(frac=1, random_state=7).reset_index(drop=True)


def test_two_municipalities_calendar_change_mean_and_first_history(
    feature_history: pd.DataFrame, contract: dict[str, Any]
) -> None:
    before = feature_history.copy(deep=True)
    result = derive_features(feature_history, contract).set_index(KEYS)
    a = result.loc[("50001", "2020-01")]
    b = result.loc[("73001", "2020-01")]
    assert a["dengue_lag_1"] == 7 and b["dengue_lag_1"] == 200
    assert a["dengue_lag_2"] == 10 and b["dengue_lag_2"] == 100
    assert a["grave_lag_1"] == 0.7 and b["grave_lag_1"] == 20
    assert a["zona_canal_lag_1"] == "ALERTA" and b["zona_canal_lag_1"] == "EXCESO"
    assert a["dengue_media_3m"] == 10  # (13 + 7 + 10) / 3
    assert result.loc[("50001", "2020-02"), "dengue_media_3m"] == 13  # (19 + 13 + 7) / 3
    assert result.loc[("50001", "2020-02"), "dengue_lag_3"] == 10
    assert result.loc[("50001", "2019-12"), "dengue_cambio_1m"] == -3
    for code in ("50001", "73001"):
        first = result.loc[(code, "2019-11")]
        assert first[[c for c in DERIVED_COLUMNS if c not in ("mes_sin", "mes_cos")]].isna().all()
    pd.testing.assert_frame_equal(before, feature_history)


def test_all_climate_lags_and_original_signs(
    feature_history: pd.DataFrame, contract: dict[str, Any]
) -> None:
    result = derive_features(feature_history, contract)
    for source in contract["roles"]["predictors"]:
        pd.testing.assert_series_equal(
            result[source], feature_history.sort_values(KEYS)[source].reset_index(drop=True)
        )
    row = result.set_index(KEYS).loc[("50001", "2020-01")]
    for name, definition in contract["derived_features"].items():
        if definition["operation"] == "lag" and definition["source"] in (
            "rain_mm_month_sum",
            "temp_mean_c_month_mean",
            "dewpoint_mean_c_month_mean",
            "surface_runoff_mm_month_sum",
        ):
            assert row[name] == (7 if definition["months"] == 1 else 10)
    assert row["total_evaporation_mm_month_sum_ecmwf"] == -13
    assert row["wind_u_ms_month_mean"] == -13


def test_gap_is_not_a_previous_row_and_mean_requires_exact_months(
    feature_history: pd.DataFrame, contract: dict[str, Any]
) -> None:
    gap = feature_history.loc[
        ~(
            (feature_history.municipality_code == "50001")
            & (feature_history.year_month == "2019-12")
        )
    ]
    result = derive_features(gap, contract).set_index(KEYS)
    row = result.loc[("50001", "2020-01")]
    assert pd.isna(row["dengue_lag_1"]) and row["dengue_lag_2"] == 10
    assert pd.isna(row["dengue_media_3m"]) and pd.isna(row["dengue_cambio_1m"])
    assert pd.isna(result.loc[("50001", "2020-02"), "dengue_media_3m"])
    assert result.loc[("73001", "2020-01"), "dengue_media_3m"] == 200


def test_mean_requires_three_observed_values(
    feature_history: pd.DataFrame, contract: dict[str, Any]
) -> None:
    mask = (feature_history.municipality_code == "50001") & (
        feature_history.year_month == "2019-12"
    )
    feature_history.loc[mask, "dengue_notifications_count"] = float("nan")
    result = derive_features(feature_history, contract).set_index(KEYS)
    assert pd.isna(result.loc[("50001", "2020-01"), "dengue_media_3m"])
    assert result.loc[("73001", "2020-01"), "dengue_media_3m"] == 200


def test_future_perturbation_and_row_order_do_not_change_prior_features(
    feature_history: pd.DataFrame, contract: dict[str, Any]
) -> None:
    before = derive_features(feature_history, contract)
    changed = feature_history.copy()
    changed.loc[changed.year_month > "2020-01", "dengue_notifications_count"] = 99999
    changed.loc[changed.year_month > "2020-01", "zona_canal_t"] = "EXITO"
    changed.loc[changed.year_month > "2020-01", "rain_mm_month_sum"] = 99999
    after = derive_features(changed.sample(frac=1, random_state=5), contract)
    pd.testing.assert_frame_equal(
        before.loc[before.year_month <= "2020-01"], after.loc[after.year_month <= "2020-01"]
    )
    assert serialize_table(before) == serialize_table(derive_features(feature_history, contract))


def test_calendar_phase_january_and_december(
    feature_history: pd.DataFrame, contract: dict[str, Any]
) -> None:
    result = derive_features(feature_history, contract).set_index(KEYS)
    assert result.loc[("50001", "2020-01"), "mes_sin"] == 0
    assert result.loc[("50001", "2020-01"), "mes_cos"] == 1
    assert result.loc[("50001", "2019-12"), "mes_sin"] == pytest.approx(-0.5)
    assert result.loc[("50001", "2019-12"), "mes_cos"] == pytest.approx(3**0.5 / 2)


def test_reader_filters_reserved_rows_before_parsing(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    tmp_path: Path,
) -> None:
    reserved = panel.iloc[[0]].copy()
    reserved["year_month"] = "2025-01"
    reserved["dengue_notifications_count"] = "do-not-parse-reserved-values"
    path = tmp_path / "scoped.csv"
    pd.concat([panel, reserved]).to_csv(path, index=False)
    parsed = read_panel(path, contract, reference_end="2024-12")
    assert len(parsed) == len(panel)
    assert parsed.year_month.max() < "2025-01"


def test_eligibility_keeps_history_and_masks_reserved_targets(
    panel: pd.DataFrame,
    contract: dict[str, Any],
) -> None:
    # Use actual policy builder; no hard-coded sample counts in implementation.
    policy = policy_from_years(2007, 2025, "2025-01")
    data = panel.copy()
    data["y_evaluable_t1"] = True
    data["y_evaluable_t2"] = True
    controls, audit = build_controls(data, contract, policy)
    assert len(controls) == len(panel)
    assert audit["t1"]["rows"] == 6 and audit["t2"]["rows"] == 6
    assert not set(controls) & set(contract["roles"]["predictors"])
    data.loc[0, "target_period_t1"] = "2025-01"
    data.loc[0, "y_t1"] = 1
    data.loc[0, "p75_t1"] = 100
    controls, audit = build_controls(data, contract, policy)
    assert pd.isna(controls.loc[0, "y_t1"]) and pd.isna(controls.loc[0, "p75_t1"])
    assert not controls.loc[0, "eligible_t1"]
    assert controls.loc[0, "reserved_target_masked_t1"]
    assert audit["t1"]["rows"] == 5


def test_immutable_bundle_reuse_tamper_and_error_policy(tmp_path: Path) -> None:
    identity = "a" * 64
    payloads = {"features.csv": b"a\n1\n", "manifest.json": json_bytes({"id": identity})}
    bundle = publish_bundle(tmp_path, identity, payloads)
    assert publish_bundle(tmp_path, identity, payloads) == bundle
    with pytest.raises(PreparationError, match="already exists"):
        publish_bundle(tmp_path, identity, payloads, existing_policy="error")
    (bundle / "features.csv").write_bytes(b"corrupted")
    with pytest.raises(PreparationError, match="corrupted"):
        publish_bundle(tmp_path, identity, payloads)
    assert (bundle / "features.csv").read_bytes() == b"corrupted"  # never silently repaired
    assert not (tmp_path / ".publish.lock").exists()


def test_failed_staged_write_never_publishes_partial_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_rename(*args: Any) -> None:
        raise OSError("simulated publication failure")

    monkeypatch.setattr("scripts.training_preparation.persistence.os.rename", fail_rename)
    with pytest.raises(OSError, match="publication failure"):
        publish_bundle(tmp_path, "b" * 64, {"features.csv": b"a\n1\n"})
    assert list(tmp_path.iterdir()) == []


def test_data_config_code_changes_never_reuse_previous_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: dict[str, Any],
    panel: pd.DataFrame,
) -> None:
    contract_path = tmp_path / CONTRACT_PATH
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(json.dumps(contract))
    source = tmp_path / "source.csv"
    source.write_text("synthetic source identity")
    code = tmp_path / "code.py"
    code.write_text("first code identity")

    def prepared(config: PreparationConfig, **kwargs: Any) -> PreparationResult:
        return PreparationResult(
            panel,
            contract,
            {
                "input_fingerprints": {
                    str(CONTRACT_PATH): fingerprint(contract_path),
                    "source.csv": fingerprint(source),
                }
            },
        )

    monkeypatch.setattr(development_module, "prepare_inputs", prepared)
    monkeypatch.setattr(
        development_module,
        "notification_year_metadata",
        lambda path: {"min_year": 2007, "max_year": 2025},
    )
    monkeypatch.setattr(
        development_module, "code_fingerprints", lambda root: {"code.py": fingerprint(code)}
    )
    config = PreparationConfig(tmp_path)
    first = build_development(config)
    assert build_development(config, verify_only=True).bundle == first.bundle
    source.write_text("changed source identity")
    second = build_development(config)
    assert first.bundle != second.bundle
    contract["development_output"]["existing_policy"] = "error"
    contract_path.write_text(json.dumps(contract))
    third = build_development(config)
    assert third.bundle not in (first.bundle, second.bundle)
    code.write_text("changed code identity")
    fourth = build_development(config)
    assert len({first.bundle, second.bundle, third.bundle, fourth.bundle}) == 4
    assert first.manifest["files"] == fourth.manifest["files"]
    verify_bundle(first.bundle, {p.name: p.read_bytes() for p in first.bundle.iterdir()})


def test_reserved_target_outcome_changes_do_not_affect_controls(
    panel: pd.DataFrame,
    contract: dict[str, Any],
) -> None:
    policy = policy_from_years(2007, 2025, "2025-01")
    panel.loc[0, "target_period_t1"] = "2025-01"
    first, audit = build_controls(panel, contract, policy)
    panel.loc[0, "y_t1"] = 1
    panel.loc[0, "p75_t1"] = 999999
    second, changed_audit = build_controls(panel, contract, policy)
    pd.testing.assert_frame_equal(first, second)
    assert audit == changed_audit


@pytest.mark.parametrize("fault", ["duplicate", "future_lag"])
def test_feature_builder_rejects_unsafe_keys_or_lags(
    feature_history: pd.DataFrame,
    contract: dict[str, Any],
    fault: str,
) -> None:
    if fault == "duplicate":
        feature_history = pd.concat([feature_history, feature_history.iloc[[0]]])
    else:
        contract["derived_features"]["dengue_lag_1"]["months"] = -1
    with pytest.raises(PreparationError):
        derive_features(feature_history, contract)


def test_preparation_domain_has_no_framework_or_filesystem_imports() -> None:
    import ast

    for path in (ROOT / "src/sat_dengue/training_preparation").glob("*.py"):
        tree = ast.parse(path.read_text())
        imports = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        assert not any(
            n.split(".")[0] in {"pathlib", "os", "tempfile", "kedro", "mlflow"} for n in imports
        ), path


def test_preparation_pipeline_exposes_cutoffs_states_and_separate_outputs() -> None:
    from sat_dengue.pipelines.preparation.pipeline import create_pipeline

    pipeline = create_pipeline()
    names = {n.name for n in pipeline.nodes}
    assert {
        "preparation_features",
        "preparation_eligibility",
        "preparation_partitions",
        "preparation_replay",
        "preparation_publish",
    } <= names
    assert {
        "preparation_sources",
        "saved_preparers",
        "configuration_inputs",
        "parameters",
    } <= pipeline.inputs()
    assert "preparation_bundle" in pipeline.outputs()
    replay = next(n for n in pipeline.nodes if n.name == "preparation_replay")
    assert {"producer_cutoffs", "consumer_cutoffs", "saved_preparers"} <= set(replay.inputs)


@pytest.fixture
def synthetic_preparation_graph(contract: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    """Small deterministic full-calendar source; saved states fit solely on train."""
    from sat_dengue.datasets import ConfigurationInputsDataset
    from sat_dengue.training_preparation import workflow
    from sat_dengue.training_preparation.preprocessing import PreparerSpec

    rows = []
    for code in ("50001", "73001"):
        for period in pd.period_range("2006-06", "2024-12", freq="M"):
            row: dict[str, Any] = {
                f["name"]: None if f["nullable"] else 0 for f in contract["schema"]
            }
            row.update(municipality_code=code, year_month=str(period), zona_canal_t="ALERTA")
            for name in contract["roles"]["predictors"]:
                if name != "zona_canal_t":
                    row[name] = float(period.month)
            for h in (1, 2):
                target = str(period + h)
                row[f"target_period_t{h}"] = target
                row[f"y_evaluable_t{h}"] = "2012-01" <= target <= "2024-12"
                row[f"y_t{h}"] = period.month % 2 if row[f"y_evaluable_t{h}"] else pd.NA
            rows.append(row)
    panel = pd.DataFrame(rows)
    sources = {
        "panel": panel,
        "contract": contract,
        "policy": policy_from_years(2007, 2025, "2025-01"),
        "provenance": {},
    }
    inputs = ConfigurationInputsDataset().load()
    saved: dict[str, Any] = {"states": {}, "provenance": {}}
    resolved = workflow.resolve_preparation_configuration(
        inputs, {"profile": "preparation", "tracking": "disabled"}, sources, saved
    )
    keys, features = workflow.features(sources, resolved)
    controls, _ = workflow.eligibility(sources, resolved)
    producer, consumer = workflow.boundaries(resolved)
    windows = workflow.partitions(keys, features, controls, sources, resolved, producer, consumer)
    for window, entry in windows.items():
        saved["states"][window] = {}
        for profile, spec in contract["temporal_preparation"]["profiles"].items():
            train = entry["splits"]["train"]
            saved["states"][window][profile] = workflow.fit_training_partition(
                train["X"],
                train["controls"],
                PreparerSpec(**spec),
                list(train["X"]),
                int(window[-1]),
                producer[window],
                "train",
            )
    from sat_dengue.training_preparation.serialization import bytes_record, json_bytes

    saved["provenance"]["state_files"] = {
        f"{w}_{n}_preparer.json": bytes_record(json_bytes(state))
        for w, profiles in saved["states"].items()
        for n, state in profiles.items()
    }
    return inputs, sources, saved, windows


def test_preparation_synthetic_complete_kedro_graph(
    synthetic_preparation_graph: tuple[Any, ...],
) -> None:
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue.pipelines.preparation.pipeline import create_pipeline

    inputs, sources, saved, _ = synthetic_preparation_graph
    catalog = DataCatalog(
        {
            n: MemoryDataset(v)
            for n, v in {
                "configuration_inputs": inputs,
                "parameters": {"profile": "preparation", "tracking": "disabled"},
                "preparation_sources": sources,
                "saved_preparers": saved,
            }.items()
        }
    )
    output = SequentialRunner().run(create_pipeline(), catalog)["preparation_bundle"].load()
    assert len(output["payloads"]) == 117
    assert len([n for n in output["payloads"] if n.endswith("_preparer.json")]) == 16


@pytest.mark.parametrize(
    "fault", ["Y", "keys", "controls", "X", "window", "producer", "consumer", "state"]
)
def test_preparation_replay_rejects_misalignment_and_boundaries(
    synthetic_preparation_graph: tuple[Any, ...], fault: str
) -> None:
    from sat_dengue.training_preparation import workflow

    inputs, sources, saved, windows = copy.deepcopy(synthetic_preparation_graph)
    resolved = workflow.resolve_preparation_configuration(
        inputs, {"profile": "preparation", "tracking": "disabled"}, sources, saved
    )
    producer, consumer = workflow.boundaries(resolved)
    window = "2018-12_t1"
    split = windows[window]["splits"]["train"]
    if fault in ("Y", "keys", "controls", "X"):
        split[fault] = split[fault].iloc[::-1].reset_index(drop=True)
    elif fault == "window":
        windows["2025-01_t1"] = windows.pop(window)
    elif fault == "producer":
        producer[window] = "2025-01"
    elif fault == "consumer":
        consumer[window]["validation"] = "2025-01"
    else:
        saved["states"][window]["native"]["input_columns"] = list(
            reversed(saved["states"][window]["native"]["input_columns"])
        )
    with pytest.raises(PreparationError):
        workflow.replay(windows, saved, resolved, producer, consumer)


def test_preparation_atomic_persistence_and_identity_refusal(
    synthetic_preparation_graph: tuple[Any, ...],
    monkeypatch: pytest.MonkeyPatch,
    repo_tmp_path: Path,
) -> None:

    from kedro.io import DatasetError

    from sat_dengue.datasets import preparation as adapter
    from sat_dengue.training_preparation import workflow

    inputs, sources, saved, windows = synthetic_preparation_graph
    resolved = workflow.resolve_preparation_configuration(
        inputs, {"profile": "preparation", "tracking": "disabled"}, sources, saved
    )
    producer, consumer = workflow.boundaries(resolved)
    transformed = workflow.replay(windows, saved, resolved, producer, consumer)
    keys, features = workflow.features(sources, resolved)
    controls, audit = workflow.eligibility(sources, resolved)
    payload = adapter.bundle_payloads(
        keys, features, controls, audit, transformed, resolved, producer, consumer
    )
    monkeypatch.setattr(adapter, "NATIVE_PREPARATION", {})  # synthetic sources only
    directory = str(repo_tmp_path)
    dataset = adapter.PreparationBundleDataset(directory)
    with pytest.raises(DatasetError):
        dataset.load()
    dataset.save(payload)
    result = dataset.load()
    bundle = ROOT / result["path"]
    assert not list(Path(directory).glob(".staging-*"))
    with pytest.raises(DatasetError, match="already exists"):
        dataset.save(payload)
    path = bundle / "features.csv"
    path.chmod(0o600)
    path.write_bytes(path.read_bytes() + b"corrupt")
    with pytest.raises(DatasetError, match="payload identity"):
        dataset.load()


@pytest.mark.parametrize("fault", ["manifest", "payload", "membership"])
def test_preparation_native_bundle_rejects_identity_drift(fault: str, repo_tmp_path: Path) -> None:

    from kedro.io import DatasetError

    from sat_dengue.datasets import preparation as adapter
    from sat_dengue.training_preparation.serialization import bytes_record

    directory = str(repo_tmp_path)
    bundle = Path(directory) / "explicit-identity"
    bundle.mkdir()
    relative = str(bundle.relative_to(ROOT))
    (bundle / "state.json").write_bytes(b"{}")
    manifest = {"bundle_id": bundle.name, "files": {"state.json": bytes_record(b"{}")}}
    data = json_bytes(manifest)
    (bundle / "manifest.json").write_bytes(data)
    assert adapter.verified_native_bundle(relative, bytes_record(data)) == manifest
    if fault == "manifest":
        (bundle / "manifest.json").write_bytes(data + b" ")
    elif fault == "payload":
        (bundle / "state.json").write_bytes(b"changed")
    else:
        (bundle / "extra").write_bytes(b"extra")
    with pytest.raises(DatasetError):
        adapter.verified_native_bundle(relative, bytes_record(data))
