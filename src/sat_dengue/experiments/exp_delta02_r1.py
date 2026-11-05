"""Fixed-MGN spatial feature and controlled EXP-DELTA02-R1 procedure."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from collections.abc import Iterable, Sequence
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.canonical.table import CLIMATE, PREDICTORS
from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.exp_beta01 import BetaSourcesDataset
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle, verify_bundle
from sat_dengue.datasets.stage2 import identity, local_path
from sat_dengue.experiments.academic_benchmark import aggregate
from sat_dengue.experiments.exp_beta01 import (
    fit_intercept,
    prepare,
    role_parts,
    shifted,
    thresholds,
)
from sat_dengue.experiments.exp_beta01_v2 import require_pair
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table

FEATURE = "neighbor_dengue_mean_lag1"
KEYS = ["municipality_code", "year_month"]
GRAPH_COLUMNS = ["target_code", "neighbor_code", "shared_length_native_degrees"]
OWNER = Path("docs/product/experiments/EXP-DELTA02-R1")
OUTPUT = Path("data/processed/exp_delta02_r1")
CANDIDATE = "R1_SPATIAL"
COMPARATORS = ["CHANNEL", "PERSISTENCE", "R0", "G0_OFF"]
STRATA = ["horizon", "year", "department"]

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


def _geometry_dependency(name: str) -> Any:
    """Keep geometry optional in base installs; the declared dev extra owns generated tests."""
    try:
        return import_module(name)
    except ModuleNotFoundError as error:
        if error.name and (error.name == "shapely" or error.name.startswith("shapely.")):
            raise RuntimeError(
                "Geometry operations require sat-dengue-v2[dev] (shapely)"
            ) from error
        raise


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

    tree_type = _geometry_dependency("shapely.strtree").STRtree
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
    shape = _geometry_dependency("shapely.geometry").shape
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
    geometry = _geometry_dependency("shapely.geometry")
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


def verified_publication(record: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    """Verify a pinned immutable publication and return its root and manifest."""
    root = local_path(str(record["path"]))
    manifest_path = root / "manifest.json"
    if identity(manifest_path)["sha256"] != record["manifest_sha256"]:
        raise ValueError(f"Pinned manifest changed: {record['path']}")
    manifest = json.loads(manifest_path.read_bytes())
    if set(path.name for path in root.iterdir()) != {*manifest["files"], "manifest.json"}:
        raise ValueError(f"Unexpected publication inventory: {record['path']}")
    for name, expected in manifest["files"].items():
        if Path(name).name != name or identity(root / name) != expected:
            raise ValueError(f"Publication payload changed: {record['path']}/{name}")
    return root, manifest


def _verify_file(path: str, expected_sha: str) -> dict[str, Any]:
    record = identity(local_path(path))
    if record["sha256"] != expected_sha:
        raise ValueError(f"Pinned file changed: {path}")
    return record


def verify_source_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Verify every R1 authority, dependency and private source before fitting."""
    records: dict[str, Any] = {}
    dependency = spec["dependency"]
    for prefix in ("original_provenance", "original_source_spec"):
        path = dependency[f"{prefix}_path"]
        records[path] = _verify_file(path, dependency[f"{prefix}_sha256"])
    original = {
        "path": dependency["original_result_path"],
        "manifest_sha256": dependency["original_result_manifest_sha256"],
    }
    verified_publication(original)
    records[f"{original['path']}/manifest.json"] = identity(
        local_path(f"{original['path']}/manifest.json")
    )
    for prefix in ("academic_contract", "beta_protocol", "benchmark_protocol"):
        path = spec["authority"][f"{prefix}_path"]
        records[path] = _verify_file(path, spec["authority"][f"{prefix}_sha256"])
    for source in spec["sources"].values():
        root, manifest = verified_publication(source)
        records[f"{source['path']}/manifest.json"] = identity(root / "manifest.json")
        records.update(
            {f"{source['path']}/{name}": expected for name, expected in manifest["files"].items()}
        )
    return records


def read_frozen_comparators(path: Path) -> pd.DataFrame:
    """Read exact T+1 comparator rows while allowing deterministic arms to lack scores."""
    frame = pd.read_csv(
        path,
        dtype={"municipality_code": str, "department_code": str, "alert": str},
        float_precision="round_trip",
    )
    frame = frame.loc[frame.horizon.eq(1) & frame.arm.isin(COMPARATORS)].copy()
    boolean = frame.alert.map({"True": True, "False": False, "true": True, "false": False})
    if boolean.isna().any() or not frame.truth.isin([0, 1]).all():
        raise ValueError("Invalid frozen comparator truth/alert tokens")
    frame["alert"] = boolean.astype(bool)
    models = frame.arm.isin(["R0", "G0_OFF"])
    if (
        frame.loc[models, "score"].isna().any()
        or not np.isfinite(frame.loc[models, "score"]).all()
        or not frame.loc[models, "score"].between(0, 1).all()
        or frame.loc[~models, "score"].notna().any()
    ):
        raise ValueError("Frozen comparator score semantics changed")
    pair_columns = [*KEYS, "target_month", "department_code", "truth", "target_excess"]
    reference: pd.DataFrame | None = None
    for arm in COMPARATORS:
        part = frame.loc[frame.arm.eq(arm)].sort_values(KEYS).reset_index(drop=True)
        if len(part) != 2653 or int(part.truth.sum()) != 313 or part.duplicated(KEYS).any():
            raise ValueError(f"Frozen T+1 comparator cohort changed: {arm}")
        if reference is None:
            reference = part
        else:
            require_pair(reference, part, pair_columns)
    return frame.sort_values(["arm", *KEYS]).reset_index(drop=True)


def load_preflight() -> dict[str, Any]:
    """Verify exact sources and construct the sole feature before any XGBoost fit."""
    spec = json.loads((OWNER / "sources.json").read_bytes())
    protocol = json.loads((OWNER / "protocol.json").read_bytes())
    if (
        spec["experiment_id"] != "EXP-DELTA02-R1"
        or protocol["experiment_id"] != "EXP-DELTA02-R1"
        or not spec["fit_requires_verified_sources"]
        or protocol["model"]["only_added_predictor"] != FEATURE
    ):
        raise ValueError("R1 protocol/source contract changed")
    records = verify_source_spec(spec)
    beta_sources = BetaSourcesDataset().load()
    prepared = prepare(beta_sources, {"profile": "exp_beta01", "tracking": "disabled"})
    beta_protocol = prepared["protocol"]
    for name in ("n_estimators", "max_depth", "learning_rate", "random_state"):
        if protocol["model"][name] != beta_protocol["model"][name]:
            raise ValueError(f"Inherited G0_OFF model contract changed: {name}")
    frame = prepared["cohorts"][1].copy()
    targets = set(frame.municipality_code.unique())
    if len(targets) != protocol["cohort"]["target_municipalities"]:
        raise ValueError("R1 target inventory changed")
    geography = spec["sources"]["geography"]
    graph = load_mgn2018_graph(local_path(geography["path"]), targets)
    national_record = spec["sources"]["national"]
    national_root = local_path(national_record["path"])
    national = pd.read_csv(
        national_root / "canonical_model_table_national_v1.csv",
        usecols=[
            "municipality_code",
            "year_month",
            "dengue_notifications_count",
            "in_epi_coverage",
            "dengue_notifications_count_zero_from_absence",
        ],
        dtype={"municipality_code": str, "year_month": str},
    )
    features = neighbor_feature(frame[KEYS], national, graph)
    frame = frame.merge(features, on=KEYS, how="left", validate="one_to_one")
    if len(frame) != len(prepared["cohorts"][1]) or frame[FEATURE].dtype.kind not in "fc":
        raise ValueError("Spatial feature merge changed the G0_OFF cohort")

    benchmark = spec["sources"]["benchmark"]
    frozen = read_frozen_comparators(local_path(benchmark["path"]) / "predictions.csv")
    evaluation = pd.concat(
        [
            role_parts(frame, year, beta_protocol)["parts"]["evaluation"]
            for year in protocol["cohort"]["evaluation_years"]
        ],
        ignore_index=True,
    ).rename(columns={"onset_target": "truth"})
    evaluation = evaluation.sort_values(KEYS).reset_index(drop=True)
    g0 = frozen.loc[frozen.arm.eq("G0_OFF")].sort_values(KEYS).reset_index(drop=True)
    require_pair(
        evaluation,
        g0,
        [*KEYS, "target_month", "department_code", "target_year", "truth"],
    )
    if (
        len(evaluation) != protocol["cohort"]["rows"]
        or int(evaluation.truth.sum()) != protocol["cohort"]["onsets"]
    ):
        raise ValueError("R1 evaluation cohort differs from the frozen contract")
    verify_source_spec(spec)
    return {
        "evidence_type": "exploratory_retrospective",
        "spec": spec,
        "protocol": protocol,
        "beta_protocol": beta_protocol,
        "frame": frame,
        "graph": graph,
        "frozen": frozen,
        "records": {**records, **beta_sources["provenance"]["sources"]},
    }


def candidate_predictors() -> list[str]:
    """Return G0_OFF's ordered non-climate predictors plus the sole R1 feature."""
    return [name for name in PREDICTORS if name not in CLIMATE] + [FEATURE]


def fit_candidate(frame: pd.DataFrame, beta_protocol: dict[str, Any]) -> dict[str, Any]:
    """Fit one pooled G0_OFF-plus-spatial candidate per fixed evaluation year."""
    from xgboost import XGBClassifier

    columns = candidate_predictors()
    cells: list[dict[str, Any]] = []
    predictions: list[pd.DataFrame] = []
    budget = beta_protocol["policy"]["budget_false_alerts_per_municipality_year"]
    for year in beta_protocol["evaluation_years"]:
        partition = role_parts(frame, year, beta_protocol)
        parts = partition["parts"]
        model = XGBClassifier(
            **{key: value for key, value in beta_protocol["model"].items() if key != "family"}
        )
        model.fit(parts["train"][columns].astype(float), parts["train"].onset_target.astype(int))
        raw_scores = {
            role: model.predict_proba(parts[role][columns].astype(float))[:, 1].astype(float)
            for role in ("calibration", "selection", "evaluation")
        }
        offset = fit_intercept(
            raw_scores["calibration"],
            parts["calibration"].onset_target.astype(int),
            beta_protocol["calibration"]["penalty"],
        )
        selected_scores = shifted(raw_scores["selection"], offset)
        policy = thresholds(
            parts["selection"].onset_target,
            selected_scores,
            len(parts["selection"]) / 12.0,
            budget,
        )
        evaluation = parts["evaluation"]
        scores = shifted(raw_scores["evaluation"], offset)
        output = evaluation[
            [
                *KEYS,
                "target_month",
                "department_code",
                "target_year",
                FEATURE,
                "neighbor_count",
                "neighbor_values_available",
                "neighbor_values_missing",
                "neighbor_feature_missing_reason",
            ]
        ].copy()
        output["truth"] = evaluation.onset_target.astype(int)
        output["target_excess"] = output.truth
        output["score"] = scores
        output["alert"] = (
            False if policy["threshold"] is None else output.score.ge(policy["threshold"])
        )
        output["arm"] = CANDIDATE
        output["horizon"] = 1
        output["year"] = year
        predictions.append(output)
        cells.append(
            {
                "year": year,
                "horizon": 1,
                "predictors": columns,
                "role_audit": partition["audit"],
                "gap_role": "adaptation (Y-2) intentionally unused by G0 candidate",
                "global_offset": offset,
                "policy": policy,
                "model_bytes": bytes(model.get_booster().save_raw(raw_format="ubj")),
            }
        )
    return {
        "predictions": pd.concat(predictions, ignore_index=True),
        "cells": cells,
        "model_fits": len(cells),
        "calibrations": len(cells),
        "policy_selections": len(cells),
    }


def _stratum_frames(frame: pd.DataFrame) -> Iterable[tuple[str, str, pd.DataFrame]]:
    years = sorted(int(year) for year in frame.year.unique())
    for year in ["all", *years]:
        for department in ["all", "50", "73"]:
            selected = frame
            if year != "all":
                selected = selected.loc[selected.year.eq(year)]
            if department != "all":
                selected = selected.loc[selected.department_code.eq(department)]
            if selected.empty:
                raise ValueError(f"Missing required stratum: {year}/{department}")
            yield str(year), department, selected


def metric_tables(details: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute pooled, year, department and year-department academic metrics."""
    rows: list[dict[str, Any]] = []
    for arm, frame in details.groupby("arm", sort=True):
        for year, department, selected in _stratum_frames(frame):
            rows.append(
                {
                    "horizon": 1,
                    "arm": arm,
                    "year": year,
                    "department": department,
                    **aggregate(selected),
                }
            )
    metrics = pd.DataFrame(rows)
    comparisons: list[dict[str, Any]] = []
    for keys, group in metrics.groupby(STRATA, sort=False):
        lookup = group.set_index("arm").to_dict("index")
        candidate = lookup[CANDIDATE]
        channel, persistence = lookup["CHANNEL"], lookup["PERSISTENCE"]
        condition_a = candidate["detected"] > channel["detected"]
        condition_b = candidate["detected"] > persistence["detected"]
        far_defined = pd.notna(candidate["far_excess"]) and pd.notna(channel["far_excess"])
        condition_c = (
            20
            * (
                candidate["false_alerts_excess"] * channel["alerts"]
                - channel["false_alerts_excess"] * candidate["alerts"]
            )
            <= candidate["alerts"] * channel["alerts"]
            if far_defined
            else None
        )
        status = (
            "NOT_EVALUABLE"
            if not far_defined
            else "MEETS"
            if condition_a and condition_b and condition_c
            else "DOES_NOT_MEET"
        )
        for reference in COMPARATORS:
            other = lookup[reference]
            row: dict[str, Any] = {
                **dict(zip(STRATA, keys, strict=True)),
                "arm": CANDIDATE,
                "reference": reference,
                "rows": candidate["rows"],
                "onsets": candidate["onsets"],
                "condition_A": condition_a,
                "condition_B": condition_b,
                "condition_C": condition_c,
                "academic_status": status,
            }
            for name in (
                "sensitivity",
                "detected",
                "false_alerts",
                "false_alerts_excess",
                "far_excess",
                "false_alerts_per_municipality_year",
                "average_precision",
                "brier",
            ):
                left, right = candidate[name], other[name]
                row[f"{name}_difference"] = (
                    None if pd.isna(left) or pd.isna(right) else left - right
                )
            comparisons.append(row)
    return metrics, pd.DataFrame(comparisons)


def paired_g0_changes(details: pd.DataFrame) -> pd.DataFrame:
    """Count decision gains and losses against frozen G0_OFF on identical keys."""
    candidate = details.loc[details.arm.eq(CANDIDATE)].copy()
    g0 = details.loc[details.arm.eq("G0_OFF")].copy()
    require_pair(
        candidate,
        g0,
        [*KEYS, "target_month", "department_code", "truth", "target_excess"],
    )
    paired = candidate.merge(
        g0[[*KEYS, "alert"]].rename(columns={"alert": "g0_alert"}),
        on=KEYS,
        how="left",
        validate="one_to_one",
    )
    rows = []
    for year, department, frame in _stratum_frames(paired):
        added = frame.alert & ~frame.g0_alert
        removed = ~frame.alert & frame.g0_alert
        rows.append(
            {
                "horizon": 1,
                "year": year,
                "department": department,
                "rows": len(frame),
                "gained_onsets": int((added & frame.truth.eq(1)).sum()),
                "lost_onsets": int((removed & frame.truth.eq(1)).sum()),
                "additional_false_alerts_excess": int((added & frame.target_excess.eq(0)).sum()),
                "removed_false_alerts_excess": int((removed & frame.target_excess.eq(0)).sum()),
                "additional_false_alerts_onset": int((added & frame.truth.eq(0)).sum()),
                "removed_false_alerts_onset": int((removed & frame.truth.eq(0)).sum()),
            }
        )
    return pd.DataFrame(rows)


def evaluate_candidate(preflight: dict[str, Any], fitted: dict[str, Any]) -> dict[str, Any]:
    """Pair the sole candidate with frozen comparators and derive all declared outputs."""
    candidate = fitted["predictions"].copy()
    frozen = preflight["frozen"].copy()
    common = [
        *KEYS,
        "target_month",
        "department_code",
        "target_year",
        "truth",
        "target_excess",
        "arm",
        "score",
        "alert",
        "horizon",
        "year",
    ]
    require_pair(candidate, frozen.loc[frozen.arm.eq("G0_OFF")], common[:6])
    details = pd.concat([candidate, frozen[common]], ignore_index=True, sort=False)
    details = details.sort_values(["arm", *KEYS]).reset_index(drop=True)
    metrics, comparisons = metric_tables(details)
    paired = paired_g0_changes(details)
    coverage = []
    for year, department, frame in _stratum_frames(candidate):
        coverage.append(
            {
                "year": year,
                "department": department,
                "rows": len(frame),
                "feature_available": int(frame[FEATURE].notna().sum()),
                "feature_missing": int(frame[FEATURE].isna().sum()),
                "neighbors_min": int(frame.neighbor_count.min()),
                "neighbors_max": int(frame.neighbor_count.max()),
            }
        )
    pooled = comparisons.loc[
        comparisons.year.eq("all")
        & comparisons.department.eq("all")
        & comparisons.reference.eq("CHANNEL")
    ].iloc[0]
    disposition = (
        "NOT_EVALUABLE"
        if pooled.academic_status == "NOT_EVALUABLE"
        else "EXPLORATORY_IMPROVEMENT"
        if pooled.academic_status == "MEETS"
        else "NOT_SUPPORTED"
    )
    return {
        **fitted,
        "details": details,
        "metrics": metrics,
        "comparisons": comparisons,
        "paired_g0": paired,
        "coverage": pd.DataFrame(coverage),
        "disposition": disposition,
    }


def execution_artifacts(preflight: dict[str, Any], result: dict[str, Any]) -> dict[str, bytes]:
    """Serialize deterministic private evidence for immutable publication."""
    cells = []
    payloads: dict[str, bytes] = {}
    for cell in result["cells"]:
        model_name = f"model-h1-{cell['year']}-OFF-spatial.ubj"
        payloads[model_name] = cell["model_bytes"]
        public_cell = {key: value for key, value in cell.items() if key != "model_bytes"}
        cells.append(public_cell | {"model_file": model_name})
    code_paths = [
        "src/sat_dengue/experiments/exp_delta02_r1.py",
        "scripts/run_exp_delta02_r1.py",
        "src/sat_dengue/experiments/exp_beta01.py",
        "src/sat_dengue/experiments/academic_benchmark.py",
        "src/sat_dengue/canonical/table.py",
    ]
    provenance = {
        "sources": preflight["records"],
        "execution": {
            "code": {path: identity(local_path(path)) for path in code_paths},
            "packages": {
                name: importlib.metadata.version(name)
                for name in ("numpy", "pandas", "scikit-learn", "xgboost")
            },
        },
    }
    pooled = (
        result["comparisons"]
        .loc[
            result["comparisons"].year.eq("all")
            & result["comparisons"].department.eq("all")
            & result["comparisons"].reference.eq("CHANNEL")
        ]
        .iloc[0]
    )
    conclusions = {
        "scientific_disposition": result["disposition"],
        "academic_status": pooled.academic_status,
        "condition_A": bool(pooled.condition_A),
        "condition_B": bool(pooled.condition_B),
        "condition_C": None if pd.isna(pooled.condition_C) else bool(pooled.condition_C),
        "evidence": "exploratory_retrospective",
        "statistical_superiority": "NOT_ESTABLISHED",
        "independent_validation": "UNAVAILABLE",
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    payloads.update(
        {
            "predictions.csv": serialize_table(result["details"]),
            "metrics.csv": serialize_table(result["metrics"]),
            "comparisons.csv": serialize_table(result["comparisons"]),
            "paired_g0_off.csv": serialize_table(result["paired_g0"]),
            "feature_coverage.csv": serialize_table(result["coverage"]),
            "cells.json": canonical_bytes({"cells": cells}),
            "conclusions.json": canonical_bytes(conclusions),
            "protocol.json": (OWNER / "protocol.json").read_bytes(),
            "sources.json": (OWNER / "sources.json").read_bytes(),
            "provenance.json": canonical_bytes(provenance),
        }
    )
    body = {
        "schema": "exp-delta02-r1-publication-v1",
        "experiment_id": "EXP-DELTA02-R1",
        "evidence_type": "exploratory_retrospective",
        "feature": FEATURE,
        "candidate": CANDIDATE,
        "files": {name: bytes_record(payload) for name, payload in sorted(payloads.items())},
        "sources": preflight["records"],
        "real_model_fits": result["model_fits"],
        "global_calibrations": result["calibrations"],
        "policy_selections": result["policy_selections"],
        "alternative_candidates": 0,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    bundle_id = hashlib.sha256(canonical_bytes(body)).hexdigest()
    payloads["manifest.json"] = canonical_bytes({**body, "bundle_id": bundle_id})
    return payloads


def execute_real() -> tuple[dict[str, Any], dict[str, bytes]]:
    """Execute the one fixed procedure and bracket it with source-preservation checks."""
    preflight = load_preflight()
    fitted = fit_candidate(preflight["frame"], preflight["beta_protocol"])
    result = evaluate_candidate(preflight, fitted)
    payloads = execution_artifacts(preflight, result)
    verify_source_spec(preflight["spec"])
    return result, payloads


def publish_real(payloads: dict[str, bytes]) -> Path:
    """Atomically publish or reuse only identical R1 bytes."""
    manifest = json.loads(payloads["manifest.json"])
    return publish_bundle(
        OUTPUT,
        manifest["bundle_id"],
        payloads,
        existing_policy="reuse_identical",
    )


def reproduce_real(payloads: dict[str, bytes]) -> Path:
    """Verify that the recomputed identity already exists with exactly identical bytes."""
    manifest = json.loads(payloads["manifest.json"])
    target = OUTPUT / manifest["bundle_id"]
    verify_bundle(target, payloads)
    return target
