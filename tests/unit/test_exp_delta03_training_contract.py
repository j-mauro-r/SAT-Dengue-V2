"""Generated metadata checks; no real data rows are read."""

import copy

import pytest

from sat_dengue.experiments.exp_delta03_contract import derive_plan, digest, validate_freeze


def metadata():
    role = {
        "rows": 12,
        "onsets": 3,
        "key_sha256": "a" * 64,
        "key_label_sha256": "b" * 64,
        "X_sha256": "c" * 64,
    }
    views = []
    for variant in ["HISTORY", "FULL_COMMON", "FULL_MINUS_NDVI"]:
        views.append(
            {
                "id": "h1_y2020_" + variant,
                "horizon": 1,
                "year": 2020,
                "reference": "primary",
                "evidence_type": "consumed_retrospective",
                "status": "MATERIALIZABLE_RETROSPECTIVE",
                "columns": ["x"],
                "physical_columns": ["x"],
                "comparison_row_weight": 1,
                "roles": {
                    r: copy.deepcopy(role)
                    for r in ["train", "calibration", "selection", "evaluation"]
                },
                "variant": variant,
            }
        )
    return {
        "availability_regime": "RETROSPECTIVE_CONSOLIDATED",
        "operational_PIT": False,
        "feature_contract": [{"name": "x"}],
        "views": views,
    }


def test_plan_counts_and_matching_derive_from_descriptors():
    m = metadata()
    p = derive_plan(m, metadata_sha256=digest(m))
    assert p["counts"]["models"] == len(m["views"])
    assert p["counts"]["runs"] == p["counts"]["child_runs"] + 1
    assert len(p["pairs"]) == 2
    assert all(c["national_evaluation"].startswith("UNAVAILABLE") for c in p["cells"])
    m["views"].pop()
    assert derive_plan(m, metadata_sha256=digest(m))["counts"]["models"] == 2


@pytest.mark.parametrize("change", ["duplicate", "2025", "stress", "unpaired", "unknown_column"])
def test_metadata_drift_fails_closed(change):
    m = metadata()
    if change == "duplicate":
        m["views"].append(m["views"][0])
    if change == "2025":
        m["views"][0]["year"] = 2025
    if change == "stress":
        m["views"][0]["year"] = 2024
    if change == "unpaired":
        m["views"][0]["roles"]["selection"]["key_label_sha256"] = "d" * 64
    if change == "unknown_column":
        m["views"][0]["columns"] = ["truth"]
    with pytest.raises(ValueError):
        derive_plan(m, metadata_sha256=digest(m))


def test_unapproved_contract_cannot_be_real_authority():
    with pytest.raises(ValueError, match="human freeze"):
        validate_freeze(
            {
                "regime": "RETROSPECTIVE_CONSOLIDATED",
                "operational_PIT": False,
                "decision_status": "PENDING_HUMAN_FREEZE",
            },
            synthetic=False,
        )


def test_metadata_adapter_hashes_generated_csv_without_parsing(tmp_path, monkeypatch):
    import json
    from pathlib import Path

    from sat_dengue.datasets.exp_delta03 import canonical, identity, publish
    from sat_dengue.datasets.exp_delta03_training import read_metadata

    payloads = {
        "matrices.json": canonical(metadata()),
        "prepared_features.csv": b"generated,bytes\n",
    }
    receipt = publish(tmp_path, "tmp/exp-delta03-phase1/products", payloads)
    folder = tmp_path / receipt["path"]
    manifest = json.loads((folder / "manifest.json").read_text())
    source = tmp_path / "docs/product/experiments/EXP-DELTA03/phase1-contract.json"
    source.parent.mkdir(parents=True)
    source.write_text("{}")
    contract = {
        "matrix_bundle": {
            "path": receipt["path"],
            "manifest_sha256": receipt["manifest_sha256"],
            "files": manifest["files"],
            "matrices": manifest["files"]["matrices.json"],
        },
        "source_contract": {"path": str(source.relative_to(tmp_path)), **identity(source)},
    }
    assert read_metadata(tmp_path, contract)["real_table_rows_parsed"] == 0
    import sat_dengue.datasets.exp_delta03_training as adapter

    original = adapter.identity

    def replace_after_check(path):
        result = original(path)
        if path.name == "prepared_features.csv":
            (folder / "matrices.json").write_bytes(b"{}")
        return result

    monkeypatch.setattr(adapter, "identity", replace_after_check)
    with pytest.raises(ValueError, match="snapshot identity"):
        read_metadata(tmp_path, contract)
    monkeypatch.setattr(adapter, "identity", original)
    (folder / "matrices.json").write_bytes(payloads["matrices.json"])
    (folder / "prepared_features.csv").write_bytes(b"changed")
    with pytest.raises(ValueError, match="member changed"):
        read_metadata(tmp_path, contract)
    assert isinstance(folder, Path)
