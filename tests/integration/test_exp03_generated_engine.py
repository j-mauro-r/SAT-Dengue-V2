"""Generated native-estimator integration; source-free and isolated."""

from __future__ import annotations

from sat_dengue.experiments import exp01, exp03


def test_probe_counts_pairing_freeze_and_controls(exp03_generated_result: dict) -> None:
    r = exp03_generated_result
    assert len(r["children"]) == r["synthetic_interface_fits"] == 408
    assert all(r[k] == 0 for k in ("real_model_fits", "real_preparer_refits", "calibrator_fits"))
    assert len({c["cell_id"] for c in r["children"]}) == 408
    assert r["terminal_manifest"]["terminal_cell_count"] == 102
    assert r["terminal_manifest"]["evaluation_outputs_opened"] is False
    assert len(r["terminal_manifest"]["reload_verification"]) == 102
    assert len(r["contrasts"]) == 204
    phases = r["execution_counters"]
    assert phases["development_oof"]["model_fits"] == 306
    assert phases["terminal_stress_2024"]["model_fits"] == 102
    assert phases["consumed_2025_benchmark"]["model_fits"] == 0
    assert all(v["searches"] == 0 for v in phases.values())
    assert not any(c["objective"] == "excess" and c["horizon"] == 1 for c in r["children"])
    for family in exp03.load_protocol()["design"]["families"]:
        for h in (1, 2):
            for window in exp03.load_protocol()["design"]["windows"]:
                cells = [
                    c
                    for c in r["children"]
                    if c["family"] == family and c["horizon"] == h and c["window"] == window["id"]
                ]
                assert len({c["cohort_sha256"] for c in cells}) == 1
                assert len({exp01.digest(c["role_sha256"]) for c in cells}) == 1
    for row in r["contrasts"]:
        assert row["decision"]["automatic_selection"] is False
        if row["tier"] == "objective_control":
            assert row["decision"]["calibration"] == "unknown"
        if row["window"] == "pooled_development":
            assert row["source_cuts"] == [
                "development_2020",
                "development_2021",
                "development_2022",
            ]
