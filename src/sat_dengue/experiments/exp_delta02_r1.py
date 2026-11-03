"""Fixed-MGN spatial feature and controlled EXP-DELTA02-R1 procedure."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

FEATURE = "neighbor_dengue_mean_lag1"
KEYS = ["municipality_code", "year_month"]
GRAPH_COLUMNS = ["target_code", "neighbor_code", "shared_length_native_degrees"]

# Each cross-vintage conflict is resolved solely by its MGN 2018 topology.
MGN2018_CONFLICT_RESOLUTION: dict[tuple[str, str], bool] = {
    ("41001", "73067"): False,
    ("41357", "73555"): False,
    ("25372", "50686"): True,
    ("25488", "73352"): True,
    ("41016", "73555"): True,
    ("41524", "73555"): True,
    ("41801", "73555"): True,
    ("73168", "76834"): True,
    ("41799", "50370"): False,
}


def _municipal_code(value: Any) -> str:
    code = str(value)
    if len(code) != 5 or not code.isdigit():
        raise ValueError(f"Invalid municipal code: {value!r}")
    return code


def graph_from_geometries(
    codes: Sequence[str], geometries: Sequence[Any], targets: set[str]
) -> pd.DataFrame:
    """Return directed target-neighbor edges using positive shared boundaries only."""
    normalized = [_municipal_code(code) for code in codes]
    if len(normalized) != len(set(normalized)) or len(normalized) != len(geometries):
        raise ValueError("Geometry codes must be unique and aligned")
    if not targets or not targets <= set(normalized):
        raise ValueError("Missing target municipality; cohort reduction is forbidden")
    if any(
        geometry.is_empty or not geometry.is_valid or geometry.area <= 0 for geometry in geometries
    ):
        raise ValueError("MGN 2018 polygons must be nonempty, valid and positive-area")

    tree_type = import_module("shapely.strtree").STRtree
    tree = tree_type(geometries)
    rows: list[dict[str, Any]] = []
    for index, target_code in enumerate(normalized):
        if target_code not in targets:
            continue
        target = geometries[index]
        for candidate_index in tree.query(target):
            neighbor_code = normalized[int(candidate_index)]
            if neighbor_code == target_code:
                continue
            shared = target.boundary.intersection(geometries[int(candidate_index)].boundary)
            if shared.length > 0:
                rows.append(
                    {
                        "target_code": target_code,
                        "neighbor_code": neighbor_code,
                        "shared_length_native_degrees": float(shared.length),
                    }
                )
    graph = pd.DataFrame(rows, columns=GRAPH_COLUMNS).sort_values(
        ["target_code", "neighbor_code"], ignore_index=True
    )
    if graph.duplicated(["target_code", "neighbor_code"]).any():
        raise ValueError("Duplicate directed neighbor relation")
    missing = targets - set(graph.target_code)
    if missing:
        raise ValueError(f"Target municipalities without MGN 2018 neighbors: {sorted(missing)}")
    return graph


def load_mgn2018_graph(root: Path, targets: set[str]) -> pd.DataFrame:
    """Read only the pinned MGN 2018 municipal shapefile and verify fixed decisions."""
    if len(targets) != 76:
        raise ValueError("EXP-DELTA02-R1 requires exactly 76 target municipalities")
    shapefile = import_module("shapefile")
    shape = import_module("shapely.geometry").shape
    reader = shapefile.Reader(str(root / "mgn2018.shp"))
    records = list(reader.iterShapeRecords())
    codes = [_municipal_code(record.record.as_dict()["MPIO_CCNCT"]) for record in records]
    geometries = [shape(record.shape.__geo_interface__) for record in records]
    graph = graph_from_geometries(codes, geometries, targets)
    relations = {tuple(sorted((row.target_code, row.neighbor_code))) for row in graph.itertuples()}
    for pair, expected in MGN2018_CONFLICT_RESOLUTION.items():
        if (tuple(sorted(pair)) in relations) is not expected:
            raise ValueError(f"MGN 2018 conflict resolution changed for {pair[0]}-{pair[1]}")
    return graph


def _previous_month(values: Iterable[str]) -> pd.Series:
    periods = pd.PeriodIndex(list(values), freq="M")
    return pd.Series((periods - 1).astype(str), dtype="string")


def neighbor_feature(
    origins: pd.DataFrame, national: pd.DataFrame, graph: pd.DataFrame
) -> pd.DataFrame:
    """Compute the fixed-denominator neighbor mean at exact T-1 with honest missingness."""
    required_origin = {*KEYS}
    required_national = {
        *KEYS,
        "dengue_notifications_count",
        "in_epi_coverage",
        "dengue_notifications_count_zero_from_absence",
    }
    if not required_origin <= set(origins) or not required_national <= set(national):
        raise ValueError("Missing required feature inputs")
    if list(graph.columns) != GRAPH_COLUMNS or graph.empty:
        raise ValueError("Invalid fixed neighbor graph")
    if origins.duplicated(KEYS).any() or national.duplicated(KEYS).any():
        raise ValueError("Duplicate municipality-month key")
    if graph.duplicated(["target_code", "neighbor_code"]).any():
        raise ValueError("Duplicate graph edge would drift the denominator")
    if graph.target_code.eq(graph.neighbor_code).any():
        raise ValueError("Self-neighbors are forbidden")

    base = origins[KEYS].copy()
    base["municipality_code"] = base.municipality_code.map(_municipal_code)
    base["neighbor_month"] = _previous_month(base.year_month)
    expanded = base.merge(
        graph,
        left_on="municipality_code",
        right_on="target_code",
        how="left",
        validate="many_to_many",
    )
    if expanded.neighbor_code.isna().any():
        missing = sorted(expanded.loc[expanded.neighbor_code.isna(), "municipality_code"].unique())
        raise ValueError(f"Target municipalities without fixed neighbors: {missing}")

    values = national[
        [
            "municipality_code",
            "year_month",
            "dengue_notifications_count",
            "in_epi_coverage",
            "dengue_notifications_count_zero_from_absence",
        ]
    ].rename(
        columns={
            "municipality_code": "neighbor_code",
            "year_month": "neighbor_month",
        }
    )
    expanded = expanded.merge(
        values,
        on=["neighbor_code", "neighbor_month"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    observed = (
        expanded["_merge"].eq("both")
        & expanded.in_epi_coverage.fillna(False).astype(bool)
        & expanded.dengue_notifications_count.notna()
        & ~expanded.dengue_notifications_count_zero_from_absence.fillna(True).astype(bool)
    )
    expanded["observed_neighbor_value"] = observed
    expanded["admitted_count"] = expanded.dengue_notifications_count.where(observed)

    rows: list[dict[str, Any]] = []
    for (code, month), group in expanded.groupby(KEYS, sort=True, dropna=False):
        total = len(group)
        available = int(group.observed_neighbor_value.sum())
        missing_rows = int(group["_merge"].ne("both").sum())
        unknown = total - available
        if available == total:
            value = float(group.admitted_count.mean())
            reason: str | None = None
        else:
            value = np.nan
            reason = "missing_neighbor_row" if missing_rows else "unknown_neighbor_count"
        rows.append(
            {
                "municipality_code": str(code),
                "year_month": str(month),
                FEATURE: value,
                "neighbor_count": total,
                "neighbor_values_available": available,
                "neighbor_values_missing": unknown,
                "neighbor_feature_missing_reason": reason,
            }
        )
    output = pd.DataFrame(rows).sort_values(KEYS, ignore_index=True)
    if len(output) != len(origins) or output.duplicated(KEYS).any():
        raise ValueError("Feature output must preserve every origin key exactly once")
    return output


def feature_self_check() -> None:
    """Exercise edge, point, self-exclusion, exact-lag and missing-zero semantics."""
    geometry = import_module("shapely.geometry")
    graph = graph_from_geometries(
        ["50001", "50002", "05001"],
        [geometry.box(0, 0, 1, 1), geometry.box(1, 0, 2, 1), geometry.box(1, 1, 2, 2)],
        {"50001"},
    )
    assert graph.neighbor_code.tolist() == ["50002"]
    origins = pd.DataFrame({"municipality_code": ["50001"], "year_month": ["2020-02"]})
    national = pd.DataFrame(
        {
            "municipality_code": ["50002"],
            "year_month": ["2020-01"],
            "dengue_notifications_count": [4],
            "in_epi_coverage": [True],
            "dengue_notifications_count_zero_from_absence": [False],
        }
    )
    assert neighbor_feature(origins, national, graph)[FEATURE].tolist() == [4.0]
