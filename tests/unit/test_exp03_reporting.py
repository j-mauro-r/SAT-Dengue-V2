"""Generated-only delivery, evidence classes, native identity and privacy tests."""

from __future__ import annotations

import copy
import csv
import io
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from exp03_reporting_fixture import generated_delivery

from sat_dengue.experiments import exp03_reporting as reporting
from sat_dengue.experiments.exp03_reporting import (
    aggregate_projection,
    validate_bundle,
    write_bundle,
)


def test_substantive_delivery_and_adverse_undefined_evidence(repo_tmp_path: Path) -> None:
    result, provenance, design = generated_delivery()
    root = repo_tmp_path / "report"
    manifest = write_bundle(root, result, provenance, design)
    assert validate_bundle(root) == manifest
    text = (root / "report.md").read_text()
    assert "SYNTHETIC GENERATED-DATA" in text
    assert "-50" in text and "0.1" in text
    assert "G5: `NOT_APPROVED`" in text
    rows = list(csv.DictReader(io.StringIO((root / "secondary_contrasts.csv").read_text())))
    assert rows[0]["paired_sensitivity_difference"] == ""
    assert rows[0]["reason"] == "no_onsets"
    reliability = list(csv.DictReader(io.StringIO((root / "reliability_bins.csv").read_text())))
    assert {r["stage"] for r in reliability} == {"raw", "calibrated"}
    assert all(float(r["observed_fraction"]) == 1 for r in reliability)
    receipt = json.loads((root / "scope_execution_receipt.json").read_text())
    assert receipt["counts_by_phase"]["real_model_fits"] == 0
    assert receipt["counts_by_phase"]["calibrator_fits"] is None
    assert "freeze_timestamp" in receipt["missing_identities"]
    assert "-0.5" in (root / "primary_effects.svg").read_text()
    assert "N/A" in (root / "group_effects.svg").read_text()


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("empty", "substantive"),
        ("duplicate", "Duplicate"),
        ("contrast", "contrasts"),
        ("benchmark_count", "zero"),
        ("benchmark_label", "labelled"),
        ("unexplained", "Unexplained"),
    ],
)
def test_missing_or_corrupt_scientific_evidence_is_rejected(
    repo_tmp_path: Path, mutation: str, match: str
) -> None:
    result, provenance, design = generated_delivery()
    if mutation == "empty":
        result["error_types_and_delay"] = []
    elif mutation == "duplicate":
        result["oof_predictions"].append(copy.deepcopy(result["oof_predictions"][0]))
    elif mutation == "contrast":
        result["secondary_contrasts"] = [
            {"contrast_id": "unlisted", "status": "not_evaluable", "reason": "none"}
        ]
    elif mutation == "benchmark_count":
        result["transport_2024_2025"][0]["threshold_selections"] = None
    elif mutation == "benchmark_label":
        result["transport_2024_2025"][0]["evidence_type"] = "blind_validation"
    elif mutation == "unexplained":
        result["oof_predictions"] = [{"status": "not_evaluable"}]
    with pytest.raises(ValueError, match=match):
        write_bundle(repo_tmp_path / mutation, result, provenance, design)


def test_closed_projection_cannot_log_rows_profiles_or_municipalities() -> None:
    result, _, _ = generated_delivery()
    result["children"][0].update(municipality_code="secret", profile={"municipalities": ["secret"]})
    result["contrasts"][0]["support"] = {"municipalities": ["secret"]}
    projection = aggregate_projection(result)
    assert "synthetic_001" not in json.dumps(projection)
    assert "secret" not in json.dumps(projection)
    assert projection["counters"]["real_model_fits"] == 0
    assert projection["counters"]["calibrator_fits"] is None
    result["real_model_fits"] = True
    with pytest.raises(ValueError, match="counter"):
        aggregate_projection(result)


def test_payload_tamper_extra_files_and_rewrite_rejected(repo_tmp_path: Path) -> None:
    result, provenance, design = generated_delivery()
    root = repo_tmp_path / "report"
    write_bundle(root, result, provenance, design)
    with pytest.raises(FileExistsError):
        write_bundle(root, result, provenance, design)
    original = (root / "primary_contrasts.csv").read_bytes()
    (root / "primary_contrasts.csv").write_bytes(original + b"tamper")
    with pytest.raises(ValueError, match="Changed native"):
        validate_bundle(root)
    (root / "primary_contrasts.csv").write_bytes(original)
    (root / "unmanifested.csv").write_text("private\nrow\n")
    with pytest.raises(ValueError, match="unexpected"):
        validate_bundle(root)


def test_protected_native_destination_and_model_traversal(repo_tmp_path: Path) -> None:
    result, provenance, design = generated_delivery()
    with pytest.raises(ValueError, match="protected"):
        write_bundle(repo_tmp_path.parents[1] / "unsafe-report", result, provenance, design)
    result["model_artifacts"] = {"../../escape": b"test"}
    with pytest.raises(ValueError, match="Unsafe model"):
        write_bundle(repo_tmp_path / "models", result, provenance, design)


def test_native_selection_reconstructs_optimal_ties_and_counts(repo_tmp_path: Path) -> None:
    result, provenance, design = generated_delivery()
    result["thresholds"][0]["detected_onsets"] += 1
    with pytest.raises(ValueError, match="reconstruct threshold detected_onsets"):
        write_bundle(repo_tmp_path / "tampered-count", result, provenance, design)
    result, provenance, design = generated_delivery()
    result["thresholds"][0]["threshold"] = 0.99
    with pytest.raises(ValueError, match="reconstruct threshold threshold"):
        write_bundle(repo_tmp_path / "tampered-policy", result, provenance, design)


def test_joint_year_department_profile_matrix_retains_sparse_support(repo_tmp_path: Path) -> None:
    result, provenance, design = generated_delivery()
    result["exposure_by_cluster"] = [
        {
            "municipality_code": "synthetic_001",
            "target_year": year,
            "window": f"development_{year}",
            "horizon": 1,
            "role": "evaluation",
            "transmission_profile": "history_insufficient",
            "monitored_exposure": 1,
            "eligible_exposure": 0.5,
            "common_exposure": 0.25,
        }
        for year in (2020, 2021, 2022)
    ]
    root = repo_tmp_path / "matrix"
    write_bundle(root, result, provenance, design)
    rows = list(csv.DictReader(io.StringIO((root / "group_effects.csv").read_text())))
    assert {r["year"] for r in rows} == {"2020", "2021", "2022"}
    assert {r["dimension"] for r in rows} == {"department", "transmission_profile"}
    assert all(r["sensitivity_difference"] == "-1.0" for r in rows)
    assert all(r["false_alert_rate_difference"] == "0.0" for r in rows)
    assert all(r["onsets"] == "1" and r["support"] == "unknown_single_year" for r in rows)
    assert "n=1" in (root / "group_effects.svg").read_text()


def test_native_metrics_reconstruction_and_symlink_no_write(repo_tmp_path: Path) -> None:
    from sat_dengue.experiments.exp03_evaluation import metrics

    result, provenance, design = generated_delivery()
    result["exposure_by_cluster"][0].update(window="development_2020", horizon=1)
    rows = [
        r
        for r in result["oof_predictions"]
        if r["variant"] == "V00" and r["window"] == "development_2020"
    ]
    frame = pd.DataFrame(rows)
    summary = metrics(frame, frame.alert, 1, 0.5, frame.score)
    result["children"][0]["summaries"] = {"micro": summary}
    write_bundle(repo_tmp_path / "metric-valid", result, provenance, design)
    summary["false_alerts"] += 1
    with pytest.raises(ValueError, match="reconstruct metric false_alerts"):
        write_bundle(repo_tmp_path / "metric-invalid", result, provenance, design)
    target, root = repo_tmp_path / "outside", repo_tmp_path / "symlink"
    target.mkdir()
    root.mkdir()
    (root / "model_artifacts").symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink descendant"):
        write_bundle(root, result, provenance, design)
    assert not list(target.iterdir())


def test_native_feature_provenance_roundtrip_and_aggregate_privacy(repo_tmp_path: Path) -> None:
    result, provenance, design = generated_delivery()
    result["feature_provenance"] = [
        {
            "municipality_code": "synthetic_source_identity",
            "year_month": "2020-01",
            "target_month": "2020-02",
            "horizon": 1,
            "window": "development_2020",
            "role": "evaluation",
            "source_months": {"lag1": "2019-12"},
            "source_event_months": {"lag1": ["2019-12"]},
            "publication_assumption": "publication_unverified",
        }
    ]
    root = repo_tmp_path / "source-dates"
    manifest = write_bundle(root, result, provenance, design)
    assert "feature_provenance.csv" in manifest["files"]
    assert validate_bundle(root) == manifest
    rows = list(csv.DictReader(io.StringIO((root / "feature_provenance.csv").read_text())))
    assert json.loads(rows[0]["source_event_months"]) == {"lag1": ["2019-12"]}
    aggregate = json.dumps(aggregate_projection(result))
    assert "synthetic_source_identity" not in aggregate
    assert "2019-12" not in aggregate
    assert "source_event_months" not in aggregate
    result["feature_provenance"][0]["source_event_months"]["lag1"] = ["2020-03"]
    with pytest.raises(ValueError, match="Future source event"):
        write_bundle(repo_tmp_path / "future-source", result, provenance, design)


def test_native_reconstruction_distinguishes_covered_eligible_and_common(
    repo_tmp_path: Path,
) -> None:
    from sat_dengue.experiments.exp03_evaluation import metrics

    result, provenance, design = generated_delivery()
    result["exposure_by_cluster"][0].update(
        window="development_2020",
        horizon=1,
        known_covered_onsets=5,
        known_eligible_onsets=3,
    )
    rows = [
        r
        for r in result["oof_predictions"]
        if r["variant"] == "V00" and r["window"] == "development_2020"
    ]
    frame = pd.DataFrame(rows)
    frame.attrs.update(covered_onsets=5, eligible_onsets=3)
    summary = metrics(frame, frame.alert, 1, 0.5, frame.score)
    assert summary["covered_onsets"] == 5
    assert summary["eligible_onsets"] == 3
    assert summary["common_onsets"] == 1
    assert summary["coverage_adjusted_sensitivity"] == pytest.approx(1 / 3)
    result["children"][0]["summaries"] = {"micro": summary}
    root = repo_tmp_path / "distinct-denominators"
    write_bundle(root, result, provenance, design)
    validate_bundle(root)
    summary["covered_onsets"] = 3
    with pytest.raises(ValueError, match="reconstruct metric covered_onsets"):
        write_bundle(repo_tmp_path / "conflated-denominators", result, provenance, design)


def test_coverage_view_uses_evaluation_ledger_once_without_horizon_mixing() -> None:
    import xml.etree.ElementTree as ET

    from sat_dengue.experiments.exp03_reporting import _coverage_summary, _coverage_svg

    ledger = []
    for horizon in (1, 2):
        for year in (2020, 2021, 2022, 2024):
            for municipality in ("50001", "73001"):
                row = {
                    "horizon": horizon,
                    "window": f"cut_{year}",
                    "municipality_code": municipality,
                    "target_year": year,
                    "role": "evaluation",
                    "monitored_exposure": horizon,
                    "eligible_exposure": 0.5,
                    "common_exposure": 0.25,
                    "known_covered_onsets": 4,
                    "known_eligible_onsets": 2,
                    "excluded_onsets": 1,
                }
                ledger.extend(
                    [
                        row,
                        {**row, "variant": "V09"},
                        {**row, "family": "gam"},
                        {**row, "role": "train", "monitored_exposure": 500},
                    ]
                )
    summary = _coverage_summary(ledger)
    assert len(summary) == 8
    for row in summary:
        assert row["monitored_months"] == 24 * row["horizon"]
        assert row["eligible_months"] == 12
        assert row["common_months"] == 6
        assert row["known_covered_onsets"] == 8
        assert row["known_eligible_onsets"] == 4
        assert row["excluded_known_eligible_onsets"] == 2
        assert row["ledger_clusters"] == 2
    graphic = ET.fromstring(_coverage_svg(summary, True))
    assert int(graphic.attrib["height"]) <= 1200
    assert int(graphic.attrib["width"]) == 1120
    ledger.append({**ledger[0], "common_exposure": 0})
    with pytest.raises(ValueError, match="Conflicting duplicated"):
        _coverage_summary(ledger)


def test_all_annual_transport_cells_flatten_metrics_and_fit_bounded_facets() -> None:
    import xml.etree.ElementTree as ET

    from sat_dengue.experiments.exp03_reporting import _transport_summary, _transport_svg

    native: list[dict[str, Any]] = []
    for family in ("gam", "lightgbm", "xgboost"):
        for horizon, objective, variants in (
            (1, "onset", range(16)),
            (2, "onset", range(16)),
            (2, "excess", (0, 9)),
        ):
            for variant in variants:
                for year in (2024, 2025):
                    native.append(
                        {
                            "cell_id": f"{family}-{horizon}-{objective}-{variant}",
                            "family": family,
                            "horizon": horizon,
                            "objective": objective,
                            "variant": f"V{variant:02}",
                            "target_year": year,
                            "view": "annual",
                            "metrics": {
                                "onset_sensitivity": 0.25 if year == 2024 else 0.5,
                                "false_alerts_per_monitored_municipality_year": 1
                                if year == 2024
                                else 2,
                            },
                        }
                    )
    native[-1]["metrics"] = {
        "onset_sensitivity": None,
        "false_alerts_per_monitored_municipality_year": None,
    }
    native += [
        {**native[0], "view": "common_month_sensitivity"},
        {**native[0], "view": "pooled_descriptive", "target_year": "2024-2025"},
    ]
    summary = _transport_summary(native)
    assert len(summary) == 204
    assert len({r["cell_id"] for r in summary}) == 102
    assert {r["target_year"] for r in summary} == {2024, 2025}
    assert summary[0]["onset_sensitivity"] == 0.25
    assert summary[1]["onset_sensitivity"] == 0.5
    assert summary[-1]["onset_sensitivity"] is None
    svg = _transport_svg(summary, True)
    graphic = ET.fromstring(svg)
    assert int(graphic.attrib["height"]) <= 2000
    assert len(graphic.findall(".//{http://www.w3.org/2000/svg}circle")) == 406
    assert svg.decode().count(">N/A</text>") == 2
    assert "V15" in svg.decode() and "excess" in svg.decode()


def test_decision_overview_keeps_all_primary_development_and_unknown_states() -> None:
    from sat_dengue.experiments.exp03_reporting import _report, _svg

    result, _, _ = generated_delivery()
    rows = []
    for contrast in ("P1", "P2", "P3", "P4"):
        for family in ("gam", "lightgbm", "xgboost"):
            for horizon in (1, 2):
                for window in ("pooled_development", "stress_2024"):
                    rows.append(
                        {
                            **result["primary_contrasts"][0],
                            "contrast_id": contrast,
                            "family": family,
                            "horizon": horizon,
                            "window": window,
                            "objective": "onset",
                            "decision": {
                                "recommendation": "inconclusive",
                                "support": "unknown",
                                "evidence_level": "retrospective_development"
                                if window == "pooled_development"
                                else "retrospective_stress",
                            },
                            "paired_interval": {
                                "sensitivity_difference": {"lower": -0.8, "upper": 0.1},
                                "false_alert_rate_difference": {"lower": None, "upper": None},
                            },
                        }
                    )
    tables = {"primary_contrasts": rows}
    report = _report(tables, True).decode()
    decisions = [line for line in report.splitlines() if line.startswith("| P")]
    assert len(decisions) == 24
    assert all("retrospective_development" in row and "unknown" in row for row in decisions)
    assert "[-80, 10]" in report and "-50" in report and "0.1 [N/A]" in report
    assert "All stress comparisons remain separate" in report
    plot = _svg("all rows", rows, ("paired_sensitivity_difference",), "primary_contrasts.csv")
    assert "pooled_development" in plot.decode() and "stress_2024" in plot.decode()
    assert "onset" in plot.decode()


def test_decision_table_percentage_points_and_separate_subgroup_unknowns() -> None:
    from sat_dengue.experiments.exp03_reporting import _report

    result, _, _ = generated_delivery()
    row = result["primary_contrasts"][0]
    row.update(
        paired_sensitivity_difference=0.1053,
        paired_burden_difference=0.1667,
        left_metrics={"real_onsets": 19},
        decision={
            "support": "pass",
            "department_guardrail": "unknown",
            "profile_guardrail": "unknown",
            "recommendation": "inconclusive",
            "evidence_level": "retrospective_development",
        },
        paired_interval={
            "sensitivity_difference": {"lower": -0.04, "upper": 0.4444},
            "false_alert_rate_difference": {"lower": -1.333, "upper": 1.667},
        },
    )
    unchanged = copy.deepcopy(row)
    text = _report({"primary_contrasts": [row]}, True).decode()
    assert "Detection Δ pp [95% CI]" in text
    assert "Burden Δ FP/monitored municipality-year [95% CI]" in text
    assert "10.53 [-4, 44.4]" in text
    assert "0.1667 [-1.33, 1.67]" in text
    assert "Onsets / aggregate support" in text and "Dept / profile guardrail" in text
    assert "19 / pass | unknown / unknown | inconclusive" in text
    assert "[native row 2](primary_contrasts.csv)" in text
    assert row == unchanged
