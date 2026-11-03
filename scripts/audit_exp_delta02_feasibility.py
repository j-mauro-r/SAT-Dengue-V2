"""Reproduce EXP-DELTA02's geography stop condition; never construct or fit a signal."""

from __future__ import annotations

import argparse
import json
import platform
from importlib import import_module
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle
from sat_dengue.datasets.stage2 import identity, local_path
from sat_dengue.training_preparation.serialization import bytes_record, json_bytes

OWNER = Path("docs/product/experiments/EXP-DELTA02")


def verified_bundle(record: dict[str, str]) -> tuple[Path, dict[str, Any]]:
    """Check the pinned manifest, exact payload inventory and every payload byte."""
    root = local_path(record["path"])
    manifest = root / "manifest.json"
    if identity(manifest)["sha256"] != record["manifest_sha256"]:
        raise ValueError("Pinned manifest changed")
    data = json.loads(manifest.read_bytes())
    if set(p.name for p in root.iterdir()) != {*data["files"], "manifest.json"}:
        raise ValueError("Unexpected publication inventory")
    for name, expected in data["files"].items():
        if Path(name).name != name or identity(local_path(str(root / name))) != expected:
            raise ValueError("Publication payload changed")
    return root, data


def boundary_relation(left: Any, right: Any) -> dict[str, Any]:
    """Use exact shared edges in the source CRS, without repair or tolerances."""
    if not left.is_valid or not right.is_valid or left.is_empty or right.is_empty:
        raise ValueError("Invalid geometry cannot define adjacency")
    boundary = left.boundary.intersection(right.boundary)
    return {
        "neighbor": boundary.length > 0,
        "point_only": not boundary.is_empty and boundary.length == 0,
        "shared_length_native_degrees": boundary.length,
        "intersection_area_native_degrees_squared": left.intersection(right).area,
    }


def topology(root: Path, year: int, targets: set[str]) -> tuple[dict[str, Any], pd.DataFrame]:
    """Audit all national polygons against all targets, including external neighbors."""
    shapefile = import_module("shapefile")
    shape = import_module("shapely.geometry").shape
    tree_type = import_module("shapely.strtree").STRtree

    reader = shapefile.Reader(str(root / f"mgn{year}.shp"))
    field = "MPIO_CDPMP" if year == 2021 else "MPIO_CCNCT"
    records = list(reader.iterShapeRecords())
    codes = [r.record.as_dict()[field] for r in records]
    if len(set(codes)) != len(codes) or any(
        not isinstance(c, str) or len(c) != 5 or not c.isdigit() for c in codes
    ):
        raise ValueError("Invalid or duplicate municipal code")
    if not targets <= set(codes):
        raise ValueError("Missing target municipality; no cohort reduction permitted")
    geometries = [shape(r.shape.__geo_interface__) for r in records]
    if any(g.is_empty or g.area <= 0 for g in geometries):
        raise ValueError("Empty or nonpositive-area polygon")
    tree = tree_type(geometries)
    rows = []
    invalid_relevant: set[str] = set()
    for i, code in enumerate(codes):
        if code not in targets:
            continue
        left = geometries[i]
        if not left.is_valid:
            invalid_relevant.add(code)
        for j in tree.query(left):
            other = codes[j]
            if code == other:
                continue
            right = geometries[j]
            if not right.is_valid:
                invalid_relevant.add(other)
            if not left.is_valid or not right.is_valid:
                continue
            relation = boundary_relation(left, right)
            if (
                relation["neighbor"]
                or relation["point_only"]
                or relation["intersection_area_native_degrees_squared"] > 0
            ):
                rows.append({"vintage": year, "target": code, "other": other, **relation})
    pairs = pd.DataFrame(rows).sort_values(["target", "other"]).reset_index(drop=True)
    edges = sorted({tuple(sorted((r.target, r.other))) for r in pairs.itertuples() if r.neighbor})
    return {
        "vintage": year,
        "territories": len(codes),
        "target_count": len(targets),
        "valid_geometries": sum(g.is_valid for g in geometries),
        "invalid_relevant": sorted(invalid_relevant),
        "edges": edges,
        "edge_pairs": len(edges),
        "external_neighbors": len({c for e in edges for c in e if c not in targets}),
        "point_only_pairs": len(
            {tuple(sorted((r.target, r.other))) for r in pairs.itertuples() if r.point_only}
        ),
        "positive_overlap_directed_pairs": int(
            pairs.intersection_area_native_degrees_squared.gt(0).sum()
        ),
        "maximum_overlap_native_degrees_squared": float(
            pairs.intersection_area_native_degrees_squared.max()
        ),
    }, pairs


def self_check() -> None:
    """Exercise exact edges, point contacts, disjointness and invalid polygons."""
    geometry = import_module("shapely.geometry")
    box, polygon = geometry.box, geometry.Polygon

    left = box(0, 0, 1, 1)
    assert boundary_relation(left, box(1, 0, 2, 1))["neighbor"]
    point = boundary_relation(left, box(1, 1, 2, 2))
    assert point["point_only"] and not point["neighbor"]
    assert not boundary_relation(left, box(2, 0, 3, 1))["neighbor"]
    try:
        boundary_relation(left, polygon([(0, 0), (1, 1), (0, 1), (1, 0), (0, 0)]))
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid geometry accepted")


def execute() -> dict[str, bytes]:
    """Verify sources and reproduce the observed, unresolved historical graph differences."""
    shapefile = import_module("shapefile")
    shapely = import_module("shapely")

    spec = json.loads((OWNER / "sources.json").read_bytes())
    sources = {k: verified_bundle(v) for k, v in spec["sources"].items()}
    geo, _ = verified_bundle(spec["geography"])
    national_root = sources["national"][0]
    table = pd.read_csv(
        national_root / "canonical_model_table_national_v1.csv",
        usecols=[
            "municipality_code",
            "year_month",
            "historical_territory_applicability",
            "dengue_notifications_count",
            "dengue_notifications_count_zero_from_absence",
        ],
        dtype={"municipality_code": str, "year_month": str},
    )
    keys = ["municipality_code", "year_month"]
    if table.duplicated(keys).any():
        raise ValueError("Duplicate national municipality-month")
    expected_months = set(pd.period_range("2011-06", "2024-12", freq="M").astype(str))
    if set(table.year_month) != expected_months or not (
        table.groupby("municipality_code").size().eq(len(expected_months)).all()
    ):
        raise ValueError("National calendar differs from the complete pinned monthly grid")
    targets = set(table.loc[table.municipality_code.str[:2].isin(["50", "73"]), keys[0]])
    regional = pd.read_csv(
        sources["regional"][0] / "canonical_model_table_v1.csv",
        usecols=["municipality_code"],
        dtype=str,
    )
    if len(targets) != 76 or targets != set(regional.municipality_code):
        raise ValueError("Target inventory differs from frozen regional population")
    audits, frames = [], []
    for year in (2005, 2018, 2021):
        audit, frame = topology(geo, year, targets)
        audits.append(audit)
        frames.append(frame)
    changes = []
    for left, right in zip(audits[:-1], audits[1:], strict=True):
        old, new = set(map(tuple, left["edges"])), set(map(tuple, right["edges"]))
        for pair in sorted(old ^ new):
            changes.append(
                {
                    "from_vintage": left["vintage"],
                    "to_vintage": right["vintage"],
                    "code_a": pair[0],
                    "code_b": pair[1],
                    "change": "added" if pair in new else "removed",
                }
            )
    # This bounded audit establishes a stop, not a general admission framework.
    # No legal or canonical valid-time crosswalk resolving these differences exists
    # among the pinned inputs. An unchanged graph alone would not certify history.
    if not changes:
        raise ValueError("Recorded stop condition did not reproduce; review historical admission")
    external = {c for a in audits for e in a["edges"] for c in e if c not in targets}
    if not external <= set(table.municipality_code):
        raise ValueError("Potential external neighbor missing from national inventory")
    count = table.dengue_notifications_count
    if count.isna().any() or count.lt(0).any() or count.mod(1).ne(0).any():
        raise ValueError("Invalid national notification counts")
    coverage = []
    for name, codes in (
        ("national", set(table.municipality_code)),
        ("targets", targets),
        ("potential_external_neighbors_unadmitted_union", external),
    ):
        part = table[table.municipality_code.isin(codes)]
        if len(part) != len(codes) * 163:
            raise ValueError("Incomplete pinned national calendar")
        coverage.append(
            {
                "population": name,
                "territories": len(codes),
                "rows": len(part),
                "from_month": part.year_month.min(),
                "through_month": part.year_month.max(),
                "null_counts": int(part.dengue_notifications_count.isna().sum()),
                "zero_counts": int(part.dengue_notifications_count.eq(0).sum()),
                "zero_from_absence": int(part.dengue_notifications_count_zero_from_absence.sum()),
                "historical_applicability": sorted(
                    part.historical_territory_applicability.unique().tolist()
                ),
            }
        )
    metrics = pd.read_csv(sources["benchmark"][0] / "metrics.csv", dtype=str)
    baselines = metrics[
        metrics.horizon.eq("1") & metrics.arm.isin(["CHANNEL", "PERSISTENCE", "R0", "G0_OFF"])
    ].copy()
    if len(baselines) != 60:
        raise ValueError("Frozen T+1 comparator strata differ")
    pooled = baselines[baselines.year.eq("all") & baselines.department.eq("all")]
    for arm, detected, false_alerts in [("CHANNEL", 94, 85), ("G0_OFF", 146, 179)]:
        row = pooled[pooled.arm.eq(arm)].iloc[0]
        if (int(row.rows), int(row.onsets), int(row.detected), int(row.false_alerts_excess)) != (
            2653,
            313,
            detected,
            false_alerts,
        ):
            raise ValueError("Historical reconciliation control differs")
    summary = {
        "execution": "COMPLETED_WITH_LIMITATIONS",
        "scientific_disposition": "NOT_EVALUABLE",
        "feasibility": "NOT_EVALUABLE",
        "reason": "Unresolved cross-vintage positive-boundary membership changes",
        "topology": [{k: v for k, v in a.items() if k != "edges"} for a in audits],
        "changed_relations": len(changes),
        "affected_targets": sorted(
            {c for r in changes for c in (r["code_a"], r["code_b"]) if c in targets}
        ),
        "coverage": coverage,
        "candidate_fits": 0,
        "spatial_features_constructed": 0,
        "candidate_metrics": None,
        "matched_candidate_cohort": None,
        "abc_candidate": None,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    # Repeat integrity checks after reads, without touching a source publication.
    for record in [*spec["sources"].values(), spec["geography"]]:
        verified_bundle(record)
    return {
        "summary.json": json_bytes(summary),
        "relations.csv": pd.concat(frames).to_csv(index=False, float_format="%.17g").encode(),
        "graph_changes.csv": pd.DataFrame(changes).to_csv(index=False).encode(),
        "baseline_t1.csv": baselines.to_csv(index=False).encode(),
        "provenance.json": json_bytes(
            {
                "source_spec": spec,
                "code": identity(Path(__file__)),
                "protocol": identity(OWNER / "PROTOCOL.md"),
                "source_spec_identity": identity(OWNER / "sources.json"),
                "python": platform.python_version(),
                "packages": {
                    "shapely": shapely.__version__,
                    "geos": shapely.geos_version_string,
                    "pyshp": shapefile.__version__,
                    "pandas": pd.__version__,
                },
            }
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    self_check()
    if args.self_check:
        print("PASS: edge, point, disjoint and invalid-geometry checks")
        return
    payloads = execute()
    if args.publish:
        from hashlib import sha256

        files = {name: bytes_record(data) for name, data in sorted(payloads.items())}
        bundle_id = sha256(json_bytes(files)).hexdigest()
        payloads["manifest.json"] = json_bytes({"bundle_id": bundle_id, "files": files})
        output = publish_bundle(Path("data/processed/exp_delta02"), bundle_id, payloads)
        print(output)
    else:
        print(json.dumps(json.loads(payloads["summary.json"]), indent=2))


if __name__ == "__main__":
    main()
