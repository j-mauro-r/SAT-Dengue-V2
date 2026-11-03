"""Protocol and source fences for the controlled EXP-DELTA02-R1 revision."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from sat_dengue.datasets.stage2 import identity
from scripts.audit_exp_delta02_feasibility import verified_bundle

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/product/experiments/EXP-DELTA02-R1"


def _json(name: str) -> dict[str, object]:
    return json.loads((DOCS / name).read_text())


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_protocol_freezes_single_authorized_intervention() -> None:
    protocol = _json("protocol.json")
    assert protocol["experiment_id"] == "EXP-DELTA02-R1"
    assert protocol["geography"] == {
        "source": "DANE MGN 2018",
        "vintage": 2018,
        "retrospective_fixed_approximation": True,
        "predicate": "shared boundary length > 0 in native CRS",
        "exclude_point_contacts": True,
        "exclude_self": True,
        "include_external_neighbors": True,
        "retain_nine_conflicting_relations_by_2018": True,
    }
    feature = protocol["feature"]
    assert isinstance(feature, dict)
    assert feature["name"] == "neighbor_dengue_mean_lag1"
    assert feature["lag_months"] == 1 and feature["alternatives"] == []
    model = protocol["model"]
    assert isinstance(model, dict)
    assert {k: model[k] for k in ("n_estimators", "max_depth", "learning_rate")} == {
        "n_estimators": 80,
        "max_depth": 2,
        "learning_rate": 0.05,
    }
    assert model["only_added_predictor"] == feature["name"]
    cohort = protocol["cohort"]
    assert isinstance(cohort, dict)
    assert (cohort["horizon"], cohort["target_municipalities"], cohort["rows"], cohort["onsets"]) == (
        1,
        76,
        2653,
        313,
    )
    assert protocol["comparators"] == ["CHANNEL", "PERSISTENCE", "R0", "G0_OFF"]
    assert protocol["dispositions"] == [
        "EXPLORATORY_IMPROVEMENT",
        "NOT_SUPPORTED",
        "NOT_EVALUABLE",
    ]


def test_source_spec_pins_authority_dependency_and_fit_preflight() -> None:
    spec = _json("sources.json")
    assert spec["fit_requires_verified_sources"] is True
    dependency = spec["dependency"]
    authority = spec["authority"]
    assert isinstance(dependency, dict) and isinstance(authority, dict)
    for path_key, sha_key in (
        ("original_provenance_path", "original_provenance_sha256"),
        ("original_source_spec_path", "original_source_spec_sha256"),
    ):
        path = ROOT / str(dependency[path_key])
        assert path.is_file() and _sha(path) == dependency[sha_key]
    for path_key, sha_key in (
        ("academic_contract_path", "academic_contract_sha256"),
        ("beta_protocol_path", "beta_protocol_sha256"),
        ("benchmark_protocol_path", "benchmark_protocol_sha256"),
    ):
        path = ROOT / str(authority[path_key])
        assert path.is_file() and _sha(path) == authority[sha_key]
    assert dependency["commit"] == "b3c982f16f938baae885b299544459db80445fbe"
    sources = spec["sources"]
    assert isinstance(sources, dict) and set(sources) == {
        "geography",
        "regional",
        "national",
        "benchmark",
        "g0_off",
    }
    assert all(isinstance(record, dict) and len(str(record["manifest_sha256"])) == 64 for record in sources.values())


def test_preflight_verifies_present_pinned_private_sources() -> None:
    spec = _json("sources.json")
    sources = spec["sources"]
    assert isinstance(sources, dict)
    missing = [name for name, record in sources.items() if not (ROOT / str(record["path"])).is_dir()]
    if missing:
        pytest.skip(f"private source bundles unavailable: {missing}")
    for record in sources.values():
        verified_bundle({"path": str(ROOT / str(record["path"])), "manifest_sha256": record["manifest_sha256"]})


def test_preflight_rejects_changed_manifest_or_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = Path("source")
    root.mkdir()
    payload = root / "payload.json"
    payload.write_text('{"fixed":true}')
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"files": {payload.name: identity(payload)}}))
    record = {"path": str(root), "manifest_sha256": identity(manifest)["sha256"]}
    verified_bundle(record)
    payload.write_text('{"fixed":false}')
    with pytest.raises(ValueError, match="changed"):
        verified_bundle(record)
