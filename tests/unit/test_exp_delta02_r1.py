"""Protocol and source fences for the controlled EXP-DELTA02-R1 revision."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.datasets.stage2 import identity
from sat_dengue.experiments.exp_delta02_r1 import (
    FEATURE,
    MGN2018_CONFLICT_RESOLUTION,
    feature_self_check,
    graph_from_geometries,
    load_mgn2018_graph,
    neighbor_feature,
)
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
    assert (
        cohort["horizon"],
        cohort["target_municipalities"],
        cohort["rows"],
        cohort["onsets"],
    ) == (
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
    assert all(
        isinstance(record, dict) and len(str(record["manifest_sha256"])) == 64
        for record in sources.values()
    )


def test_preflight_verifies_present_pinned_private_sources() -> None:
    spec = _json("sources.json")
    sources = spec["sources"]
    assert isinstance(sources, dict)
    missing = [
        name for name, record in sources.items() if not (ROOT / str(record["path"])).is_dir()
    ]
    if missing:
        pytest.skip(f"private source bundles unavailable: {missing}")
    for record in sources.values():
        verified_bundle(
            {"path": str(ROOT / str(record["path"])), "manifest_sha256": record["manifest_sha256"]}
        )


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


def test_graph_excludes_self_and_point_contacts_but_keeps_external_edge() -> None:
    geometry = pytest.importorskip("shapely.geometry")
    codes = ["50001", "50002", "05001", "50003"]
    shapes = [
        geometry.box(0, 0, 1, 1),
        geometry.box(1, 1, 2, 2),
        geometry.box(-1, 0, 0, 1),
        geometry.box(3, 0, 4, 1),
    ]
    graph = graph_from_geometries(codes, shapes, {"50001"})
    assert graph[["target_code", "neighbor_code"]].values.tolist() == [["50001", "05001"]]
    assert graph.shared_length_native_degrees.tolist() == [1.0]


def test_graph_real_mgn2018_resolves_all_nine_conflicts() -> None:
    pytest.importorskip("shapefile")
    pytest.importorskip("shapely")
    spec = _json("sources.json")
    sources = spec["sources"]
    assert isinstance(sources, dict)
    geography = sources["geography"]
    regional = sources["regional"]
    assert isinstance(geography, dict) and isinstance(regional, dict)
    geo_root = ROOT / str(geography["path"])
    regional_path = ROOT / str(regional["path"]) / "canonical_model_table_v1.csv"
    if not geo_root.is_dir() or not regional_path.is_file():
        pytest.skip("pinned private MGN/regional sources unavailable")
    targets = set(
        pd.read_csv(regional_path, usecols=["municipality_code"], dtype=str).municipality_code
    )
    graph = load_mgn2018_graph(geo_root, targets)
    pairs = {
        tuple(sorted(pair))
        for pair in graph[["target_code", "neighbor_code"]].itertuples(index=False, name=None)
    }
    assert len({tuple(sorted(pair)) for pair in pairs}) == 288
    assert len({code for pair in pairs for code in pair if code not in targets}) == 66
    for pair, expected in MGN2018_CONFLICT_RESOLUTION.items():
        assert (tuple(sorted(pair)) in pairs) is expected


def test_feature_uses_exact_lag_and_fixed_denominator() -> None:
    graph = pd.DataFrame(
        {
            "target_code": ["50001", "50001"],
            "neighbor_code": ["50002", "05001"],
            "shared_length_native_degrees": [1.0, 2.0],
        }
    )
    origins = pd.DataFrame({"municipality_code": ["50001"], "year_month": ["2020-02"]})
    national = pd.DataFrame(
        {
            "municipality_code": ["50002", "05001", "50002", "05001"],
            "year_month": ["2020-01", "2020-01", "2020-02", "2020-02"],
            "dengue_notifications_count": [2, 6, 200, 600],
            "in_epi_coverage": [True] * 4,
            "dengue_notifications_count_zero_from_absence": [False] * 4,
        }
    )
    result = neighbor_feature(origins, national, graph).iloc[0]
    assert result[FEATURE] == 4.0
    assert (
        result.neighbor_count,
        result.neighbor_values_available,
        result.neighbor_values_missing,
    ) == (
        2,
        2,
        0,
    )
    assert result.neighbor_feature_missing_reason is None


def test_feature_missing_or_absence_zero_never_changes_denominator() -> None:
    graph = pd.DataFrame(
        {
            "target_code": ["50001", "50001"],
            "neighbor_code": ["50002", "05001"],
            "shared_length_native_degrees": [1.0, 2.0],
        }
    )
    origins = pd.DataFrame({"municipality_code": ["50001"], "year_month": ["2020-02"]})
    national = pd.DataFrame(
        {
            "municipality_code": ["50002", "05001"],
            "year_month": ["2020-01", "2020-01"],
            "dengue_notifications_count": [2, 0],
            "in_epi_coverage": [True, True],
            "dengue_notifications_count_zero_from_absence": [False, True],
        }
    )
    result = neighbor_feature(origins, national, graph).iloc[0]
    assert result[FEATURE] != result[FEATURE]  # NaN: no partial-neighbor mean.
    assert result.neighbor_count == 2 and result.neighbor_values_available == 1
    assert result.neighbor_feature_missing_reason == "unknown_neighbor_count"
    missing = neighbor_feature(origins, national.iloc[:1], graph).iloc[0]
    assert missing.neighbor_count == 2 and missing.neighbor_values_available == 1
    assert missing.neighbor_feature_missing_reason == "missing_neighbor_row"


def test_feature_prefix_invariance_rejects_future_information() -> None:
    graph = pd.DataFrame(
        {
            "target_code": ["50001"],
            "neighbor_code": ["50002"],
            "shared_length_native_degrees": [1.0],
        }
    )
    origins = pd.DataFrame({"municipality_code": ["50001"], "year_month": ["2020-02"]})
    national = pd.DataFrame(
        {
            "municipality_code": ["50002", "50002", "50002"],
            "year_month": ["2020-01", "2020-02", "2020-03"],
            "dengue_notifications_count": [3, 4, 5],
            "in_epi_coverage": [True, True, True],
            "dengue_notifications_count_zero_from_absence": [False, False, False],
        }
    )
    first = neighbor_feature(origins, national, graph)
    changed = national.copy()
    changed.loc[changed.year_month.ge("2020-02"), "dengue_notifications_count"] = 99999
    second = neighbor_feature(origins, changed, graph)
    pd.testing.assert_frame_equal(first, second)
    feature_self_check()


def test_missing_geometry_dependency_fails_with_install_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sat_dengue.experiments import exp_delta02_r1 as module

    def absent(name: str) -> None:
        raise ModuleNotFoundError("missing optional geometry", name="shapely")

    monkeypatch.setattr(module, "import_module", absent)
    with pytest.raises(RuntimeError, match=r"sat-dengue-v2\[dev\]"):
        module._geometry_dependency("shapely.geometry")
