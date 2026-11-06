"""EXP-DELTA03 Phase2 adapters; metadata admission never parses private table rows."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from kedro.io import AbstractDataset, DatasetError

from sat_dengue.datasets.exp_delta03 import ROOT, canonical, identity, safe_path
from sat_dengue.experiments.exp_delta03_contract import derive_plan

TRAINING_CONTRACT = "docs/product/experiments/EXP-DELTA03/training-contract.json"


def read_metadata(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    """Bind all immutable input bytes but read only JSON descriptors, not real rows."""
    spec = contract["matrix_bundle"]
    folder = safe_path(root, spec["path"], "tmp/exp-delta03-phase1/products")
    manifest_path = safe_path(
        root, spec["path"] + "/manifest.json", "tmp/exp-delta03-phase1/products"
    )
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != spec["manifest_sha256"]:
        raise ValueError("Phase1 manifest identity changed")
    manifest = json.loads(manifest_bytes)
    if hashlib.sha256(canonical(manifest["files"])).hexdigest() != folder.name or spec[
        "matrices"
    ] != manifest["files"].get("matrices.json"):
        raise ValueError("Prepared content identity changed")
    if manifest["files"] != spec["files"]:
        raise ValueError("Declared prepared artifacts changed")
    for name, record in manifest["files"].items():
        if Path(name).name != name:
            raise ValueError("Unsafe prepared member")
        path = safe_path(root, spec["path"] + "/" + name, "tmp/exp-delta03-phase1/products")
        if identity(path) != record:
            raise ValueError("Prepared matrix member changed")
    source = contract["source_contract"]
    if identity(safe_path(root, source["path"], "docs/product/experiments/EXP-DELTA03")) != {
        "sha256": source["sha256"],
        "bytes": source["bytes"],
    }:
        raise ValueError("Preparation source contract changed")
    metadata_path = safe_path(
        root, spec["path"] + "/matrices.json", "tmp/exp-delta03-phase1/products"
    )
    metadata_bytes = metadata_path.read_bytes()
    if {"sha256": hashlib.sha256(metadata_bytes).hexdigest(), "bytes": len(metadata_bytes)} != spec[
        "matrices"
    ]:
        raise ValueError("Parsed metadata snapshot identity changed")
    metadata = json.loads(metadata_bytes)
    return {
        "metadata": metadata,
        "plan": derive_plan(metadata, metadata_sha256=spec["matrices"]["sha256"]),
        "contract": contract,
        "real_table_rows_parsed": 0,
    }


class Delta03TrainingMetadataDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def load(self) -> dict[str, Any]:
        path = safe_path(ROOT, TRAINING_CONTRACT, "docs/product/experiments/EXP-DELTA03")
        raw = path.read_bytes()
        return {
            **read_metadata(ROOT, json.loads(raw)),
            "training_contract_sha256": hashlib.sha256(raw).hexdigest(),
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Read-only training metadata")

    def _describe(self) -> dict[str, Any]:
        return {"contract": TRAINING_CONTRACT, "real_rows": "never loaded by metadata adapter"}


# Synthetic execution always uses a separate ignored namespace, never the environment's store.
SYNTHETIC_ROOT = "tmp/exp-delta03-phase2/synthetic"


def _public_contract() -> tuple[dict[str, Any], str]:
    raw = safe_path(ROOT, TRAINING_CONTRACT, "docs/product/experiments/EXP-DELTA03").read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def resolve_evaluation_annex(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    """Resolve pinned metadata only for explicit preflight or authorization admission."""
    annex = contract.get("evaluation_annex")
    if not annex or "path" not in annex:
        return contract
    path = safe_path(root, annex["path"], "data/processed/exp_delta03-inputs")
    captured = path.read_bytes()
    if {"sha256": hashlib.sha256(captured).hexdigest(), "bytes": len(captured)} != {
        "sha256": annex["sha256"],
        "bytes": annex["bytes"],
    }:
        raise ValueError("Executable evaluation annex descriptor changed")
    return {**contract, "evaluation_annex": json.loads(captured)}


def _validate_artifacts(payloads: dict[str, bytes]) -> None:
    from sat_dengue.experiments.exp_delta03_artifacts import validate_payloads

    catalogue = json.loads(
        (ROOT / "docs/product/experiments/EXP-DELTA03/artifact-schemas.json").read_bytes()
    )
    validate_payloads(payloads, catalogue)


def _frame_hash(frame) -> str:
    from sat_dengue.experiments.exp_delta03_contract import digest

    columns = list(frame)
    ordered = frame.sort_values(
        [k for k in ["divipola_municipio", "periodo_mes", "horizon"] if k in frame]
    )
    clean = ordered.astype(object).where(ordered.notna(), None)
    return digest({"columns": columns, "records": clean.to_dict("records")})


def training_source(parameters: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.configuration import validate_parameters

    params = validate_parameters(parameters)
    if params["profile"] not in {"exp_delta03", "exp_delta03_synthetic"}:
        raise ValueError("Training graph requires its exact operational profile")
    contract, sha = _public_contract()
    spec = contract["source_contract"]
    if identity(ROOT / spec["path"]) != {"sha256": spec["sha256"], "bytes": spec["bytes"]}:
        raise ValueError("Public preparation schema changed from frozen matrix source")
    return {
        "contract": contract,
        "training_contract_sha256": sha,
        "parameters": params,
        "synthetic": params["profile"] == "exp_delta03_synthetic",
    }


def _generated_context(context: dict[str, Any]) -> dict[str, Any]:
    import copy

    from sat_dengue.data.exp_delta03_retrospective import (
        prepare_retrospective,
        row_hash,
        values_hash,
    )
    from sat_dengue.experiments.exp_delta03_contract import derive_plan, digest
    from sat_dengue.experiments.exp_delta03_inputs import (
        generated_national_annex,
        generated_outcomes,
        role_inputs,
    )
    from sat_dengue.experiments.exp_delta03_synthetic import generated_preparation

    preparation = json.loads(
        (ROOT / "docs/product/experiments/EXP-DELTA03/phase1-contract.json").read_bytes()
    )
    ledger = json.loads((ROOT / preparation["retrospective_source_ledger"]["path"]).read_bytes())
    sources = generated_preparation(preparation, ledger)
    result = prepare_retrospective(sources)
    metadata = {
        "availability_regime": result["availability_regime"],
        "operational_PIT": False,
        "feature_contract": result["feature_manifest"],
        "views": result["views"],
    }
    prepared = {**result, "metadata": metadata}
    plan = derive_plan(metadata, metadata_sha256=digest(metadata))
    outcomes, history = generated_outcomes(sources)
    parts = role_inputs(prepared, plan, outcomes)
    annex = generated_national_annex(sources, prepared, plan, outcomes, history)
    contract = copy.deepcopy(context["contract"])
    contract.update(evidence_type="generated_only", decision_status="SYNTHETIC_FIXTURE_ONLY")
    contract["uncertainty"]["draws"] = (
        20  # Technical fixture resource limit, never a scientific freeze.
    )
    inputs = {
        "metadata_sha256": digest(metadata),
        "outcomes_sha256": _frame_hash(outcomes),
        "annex": {
            key: {"rows_sha256": _frame_hash(value["rows"]), "X_sha256": values_hash(value["X"])}
            for key, value in annex.items()
        },
    }
    contract["matrix_bundle"] = {"manifest_sha256": digest(inputs)}
    calendar = outcomes.loc[outcomes.origin_excess.notna() & outcomes.target_excess.notna()].copy()
    calendar["divipola_departamento"] = calendar.divipola_municipio.str[:2]
    calendar["target_month"] = (
        pd.PeriodIndex(calendar.periodo_mes, freq="M") + calendar.horizon.to_numpy()
    ).astype(str)
    from sat_dengue.data.exp_delta03_retrospective import static_features

    ordinary, manifest = static_features(sources["frame"], history, preparation)
    rain = [
        f["name"]
        for f in manifest
        if f["block"] == "ERA5_PRECIPITATION"
        or str(f["source"]).startswith(("precipitacion_chirps", "racha_seca_chirps"))
    ]
    coverage = ordinary[["divipola_municipio", "periodo_mes"]].copy()
    coverage["coverage_water"] = ordinary.fraccion_agua_superficial_pct_area_observada__lag1.notna()
    coverage["coverage_era5"] = ordinary[rain].notna().all(axis=1)
    calendar = calendar.merge(
        coverage, on=["divipola_municipio", "periodo_mes"], how="left", validate="many_to_one"
    )
    return {
        **context,
        "contract": contract,
        "metadata": metadata,
        "plan": plan,
        "parts": parts,
        "national_annex": annex,
        "national_expected": {
            key: {
                "rows": len(value["rows"]),
                "key_label_sha256": row_hash(
                    value["rows"], ["divipola_municipio", "periodo_mes", "truth"]
                ),
                "X_sha256": values_hash(value["X"]),
            }
            for key, value in annex.items()
        },
        "comparators": {
            cell["id"]: {
                name: _generated_comparator(parts[cell["id"]]["evaluation"]["rows"], index)
                for index, name in enumerate(["R0", "G0_OFF", "G0_ON", "G1"])
            }
            for cell in plan["cells"]
        },
        "calendar": calendar,
        "input_source": "generated_only",
        "input_manifest": inputs,
        "permission": None,
        "roots": {
            "publication": SYNTHETIC_ROOT + "/native",
            "tracking": SYNTHETIC_ROOT + "/mlflow",
        },
    }


def _generated_comparator(rows, index):
    """Arbitrary generated controls test joins; they do not reproduce frozen V2 results."""
    result = rows.copy()
    result["score"] = ((result.origin_count + index) % 7) / 7
    result["alert"] = result.score.ge(0.5).astype(int)
    return result


def authorize_and_load(context: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.datasets.exp_delta03_execution import authorize, fingerprint
    from sat_dengue.experiments.exp_delta03_contract import validate_freeze

    if context["synthetic"]:
        return _generated_context(context)
    contract = context["contract"]
    authorization = contract["outputs"]["future_authorization"]
    if not safe_path(ROOT, authorization, "tmp/exp-delta03-phase3").is_file():
        raise PermissionError(
            "Separate manual Phase3 authorization required before private row loading"
        )
    contract = resolve_evaluation_annex(ROOT, contract)
    context["contract"] = contract
    validate_freeze(contract, synthetic=False)
    context.update(read_metadata(ROOT, contract))
    if contract["national_evaluation"]["status"] != "APPROVED_ADDITIVE_ANNEX":
        raise PermissionError("National evaluation needs an explicitly frozen additive annex")
    # This branch must be supplied only by the separately approved annex contract.
    annex = contract.get("evaluation_annex")
    if not annex:
        raise PermissionError("Pinned excess/comparator/exposure/national annex is required")
    context.update(
        input_source="pinned_private",
        roots={
            "publication": contract["outputs"]["future_protected_root"],
            "tracking": contract["outputs"]["future_tracking_root"],
        },
    )
    context["limits"] = {
        "max_models": context["plan"]["counts"]["models"],
        "max_calibrators": context["plan"]["counts"]["calibrators"],
        "threads_per_model": 1,
        "wall_seconds": contract["resources"]["wall_seconds"],
    }
    current = fingerprint(ROOT, context, context["roots"])
    context["permission"] = authorize(ROOT, context, current, authorization_relative=authorization)
    return load_authorized_inputs(context)


def load_authorized_inputs(context: dict[str, Any]) -> dict[str, Any]:
    """Load captured, hash-bound tables only after the separate scientific authorization."""
    from sat_dengue.experiments.exp_delta03_inputs import role_inputs

    if context.get("permission") is None or context["synthetic"]:
        raise PermissionError("Real input loading requires an admitted Phase3 grant")
    contract = context["contract"]
    annex = contract["evaluation_annex"]
    if annex.get("schema") != "exp-delta03-evaluation-annex-v1":
        raise ValueError("Unsupported evaluation annex schema")

    def captured(spec, prefix):
        path = safe_path(ROOT, spec["path"], prefix)
        raw = path.read_bytes()
        if {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)} != {
            "sha256": spec["sha256"],
            "bytes": spec["bytes"],
        }:
            raise ValueError("Pinned input table identity changed")
        return _read_table(raw)

    bundle = contract["matrix_bundle"]
    prepared = {"metadata": context["metadata"]}
    for key, name in [
        ("base", "prepared_features.csv"),
        ("memberships", "cohort_membership.csv"),
        ("labels", "labels.csv"),
    ]:
        prepared[key] = captured(
            {"path": bundle["path"] + "/" + name, **bundle["files"][name]},
            "tmp/exp-delta03-phase1/products",
        )
    prefix = "data/processed/exp_delta03-inputs"
    outcomes = captured(annex["outcomes"], prefix)
    context["parts"] = role_inputs(prepared, context["plan"], outcomes)
    context["calendar"] = captured(annex["calendar"], prefix)
    context["national_annex"] = {}
    context["national_expected"] = {}
    expected = {c["id"] for c in context["plan"]["cells"] if c["reference"] != "transfer"}
    if set(annex["national_cells"]) != expected:
        raise ValueError("National evaluation annex cell inventory differs")
    for ident, descriptors in annex["national_cells"].items():
        context["national_expected"][ident] = descriptors["cohort"]
        context["national_annex"][ident] = {
            "rows": captured(descriptors["rows"], prefix),
            "X": captured(descriptors["X"], prefix),
        }
    context["comparators"] = {}
    for ident, descriptors in annex["comparators"].items():
        context["comparators"][ident] = {
            name: captured(spec, prefix) for name, spec in descriptors.items()
        }
    if set(context["comparators"]) != {c["id"] for c in context["plan"]["cells"]} or any(
        set(values) != {"R0", "G0_OFF", "G0_ON", "G1"} for values in context["comparators"].values()
    ):
        raise ValueError("Frozen comparator inventory differs")
    context["input_manifest"] = annex
    return context


def _checked_node(function):
    from functools import wraps

    @wraps(function)
    def wrapped(context):
        try:
            return function(context)
        except BaseException:
            store = context.get("store")
            if store is not None and store.fd is not None:
                store.__exit__(None, None, None)
            raise

    return wrapped


def _assert_identity(context: dict[str, Any]) -> None:
    from sat_dengue.datasets.exp_delta03_execution import fingerprint

    context["store"].check_deadline()
    if fingerprint(ROOT, context, context["roots"]) != context["identity"]:
        raise ValueError("Code/configuration/runtime changed after execution admission")


def validate_training_inputs(context: dict[str, Any]) -> dict[str, Any]:
    """Shared read-only admission for preflight and scientific graph; never reserves or fits."""
    from sat_dengue.experiments.exp_delta03_contract import validate_freeze
    from sat_dengue.experiments.exp_delta03_learning import validate_parts

    validate_freeze(context["contract"], synthetic=context["synthetic"])
    plan = context["plan"]
    from sat_dengue.experiments.exp_delta03_evaluation import paired
    from sat_dengue.experiments.exp_delta03_inputs import validate_bound_outcomes, validate_calendar
    from sat_dengue.experiments.exp_delta03_learning import probabilities

    validate_calendar(context["calendar"])
    for cell in plan["cells"]:
        parts = context["parts"][cell["id"]]
        validate_parts(cell, parts, context["contract"]["calibration"]["minimum_per_class"])
        for part in parts.values():
            validate_bound_outcomes(part["rows"])
        for control in context["comparators"][cell["id"]].values():
            paired(parts["evaluation"]["rows"], control)
            probabilities(control.score, control.truth)
            if not control.alert.isin([0, 1]).all():
                raise ValueError("Frozen comparator has nonbinary alert")
        extra = context["national_annex"].get(cell["id"])
        if extra is not None:
            from sat_dengue.experiments.exp_delta03_inputs import validate_national_annex

            validate_national_annex(
                cell, extra, context["national_expected"][cell["id"]], parts["evaluation"]["rows"]
            )
    context["limits"] = {
        "max_models": plan["counts"]["models"],
        "max_calibrators": plan["counts"]["calibrators"],
        "threads_per_model": 1,
        "wall_seconds": 600
        if context["synthetic"]
        else context["contract"]["resources"]["wall_seconds"],
    }
    return context


@_checked_node
def build_training_plan(context: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.datasets.exp_delta03_execution import (
        ExecutionStore,
        fingerprint,
        verify_publication,
    )

    validate_training_inputs(context)
    current = fingerprint(ROOT, context, context["roots"])
    context["identity"] = current
    store = ExecutionStore(
        ROOT,
        context["roots"]["publication"],
        current,
        synthetic=context["synthetic"],
        resume=context["synthetic"] or context["permission"]["allow_resume"],
        permission=context["permission"],
    )
    context["store"] = store.__enter__()
    context["invocation"] = {"model_fits": 0, "calibrator_fits": 0, "threshold_selections": 0}
    context.update(models={}, calibrators={}, policies={}, predictions={}, evaluations={})
    if store.state["status"] == "COMPLETE":
        context["publication"] = store.state["publication"]
        context["cached_payloads"] = verify_publication(
            ROOT, context["publication"], synthetic=context["synthetic"]
        )
        _validate_artifacts(context["cached_payloads"])
        context["result"] = json.loads(context["cached_payloads"]["result.json"])
    return context


@_checked_node
def train_models(context: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp_delta03_contract import canonical, digest
    from sat_dengue.model_training.exp_delta03_adapter import fit_native, reload_native

    if "cached_payloads" in context:
        return context
    for cell in context["plan"]["cells"]:
        _assert_identity(context)
        from sat_dengue.experiments.exp_delta03_learning import validate_parts

        validate_parts(
            cell,
            context["parts"][cell["id"]],
            context["contract"]["calibration"]["minimum_per_class"],
        )
        store, ident = context["store"], cell["id"]
        saved = store.read_stage(ident, "trained")
        part = context["parts"][ident]["train"]
        expected = cell["roles"]["train"]
        if saved is None:
            store.reserve_adjustment(ident, "model")
            context["invocation"]["model_fits"] += 1
            fitted = fit_native(
                part["X"],
                part["rows"].truth,
                context["contract"]["model"],
                cohort_sha256=expected["key_label_sha256"],
            )
            saved = {"model.ubj": fitted.serialize(), "model.json": canonical(fitted.metadata)}
            store.save_stage(ident, "trained", saved)
        fitted = reload_native(saved["model.ubj"], json.loads(saved["model.json"]))
        if (
            fitted.metadata["cohort_sha256"] != expected["key_label_sha256"]
            or fitted.metadata["training_X_sha256"] != expected["X_sha256"]
            or fitted.metadata["columns"] != cell["columns"]
            or fitted.metadata["parameters_sha256"] != digest(context["contract"]["model"])
        ):
            raise ValueError("Cached model/cohort/column/parameter identity differs")
        context["models"][ident] = fitted
    return context


@_checked_node
def fit_calibrators(context: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp_delta03_contract import canonical, digest
    from sat_dengue.experiments.exp_delta03_learning import calibrate

    if "cached_payloads" in context:
        return context
    for cell in context["plan"]["cells"]:
        _assert_identity(context)
        from sat_dengue.experiments.exp_delta03_learning import validate_parts

        validate_parts(
            cell,
            context["parts"][cell["id"]],
            context["contract"]["calibration"]["minimum_per_class"],
        )
        store, ident = context["store"], cell["id"]
        part = context["parts"][ident]["calibration"]
        model = context["models"][ident]
        raw = model.predict(part["X"])
        saved = store.read_stage(ident, "calibrated")
        if saved is None:
            store.reserve_adjustment(ident, "calibrator")
            context["invocation"]["calibrator_fits"] += 1
            cal = calibrate(
                raw,
                part["rows"].truth,
                role="calibration",
                model_sha256=model.metadata["model_sha256"],
                cohort_sha256=cell["roles"]["calibration"]["key_label_sha256"],
                specification=context["contract"]["calibration"],
            )
            saved = {"calibrator.json": canonical(cal)}
            store.save_stage(ident, "calibrated", saved)
        cal = json.loads(saved["calibrator.json"])
        if (
            cal["model_sha256"] != model.metadata["model_sha256"]
            or cal["cohort_sha256"] != cell["roles"]["calibration"]["key_label_sha256"]
            or cal["score_sha256"] != digest(raw.tolist())
            or cal["penalty"] != context["contract"]["calibration"]["penalty"]
        ):
            raise ValueError("Cached calibrator identity differs")
        context["calibrators"][ident] = cal
    return context


@_checked_node
def select_thresholds(context: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp_delta03_contract import canonical, digest
    from sat_dengue.experiments.exp_delta03_learning import calibrated, select_policy

    if "cached_payloads" in context:
        return context
    for cell in context["plan"]["cells"]:
        _assert_identity(context)
        from sat_dengue.experiments.exp_delta03_learning import validate_parts

        validate_parts(
            cell,
            context["parts"][cell["id"]],
            context["contract"]["calibration"]["minimum_per_class"],
        )
        store, ident = context["store"], cell["id"]
        part = context["parts"][ident]["selection"]
        model, cal = context["models"][ident], context["calibrators"][ident]
        score = calibrated(
            model.predict(part["X"]), cal, model_sha256=model.metadata["model_sha256"]
        )
        saved = store.read_stage(ident, "selected")
        if saved is None:
            context["invocation"]["threshold_selections"] += 1
            policy = select_policy(
                score,
                part["rows"].truth,
                role="selection",
                cohort_sha256=cell["roles"]["selection"]["key_label_sha256"],
                calibrator_sha256=digest(cal),
                specification=context["contract"]["policy"],
            )
            saved = {"policy.json": canonical(policy)}
            store.save_stage(ident, "selected", saved)
        policy = json.loads(saved["policy.json"])
        if (
            policy["cohort_sha256"] != cell["roles"]["selection"]["key_label_sha256"]
            or policy["calibrator_sha256"] != digest(cal)
            or policy["budget"] != context["contract"]["policy"]["B"]
        ):
            raise ValueError("Cached policy identity differs")
        context["policies"][ident] = policy
    return context


def _table_bytes(frame) -> bytes:
    return frame.to_csv(index=False, na_rep="", float_format="%.17g", lineterminator="\n").encode()


def _read_table(raw: bytes):
    import io

    return pd.read_csv(
        io.BytesIO(raw),
        dtype={
            "divipola_municipio": str,
            "divipola_departamento": str,
            "periodo_mes": str,
            "target_month": str,
            "episode_id": str,
        },
        float_precision="round_trip",
    )


@_checked_node
def generate_predictions(context: dict[str, Any]) -> dict[str, Any]:
    import numpy as np

    from sat_dengue.experiments.exp_delta03_contract import ROLES, digest
    from sat_dengue.experiments.exp_delta03_learning import apply_policy, calibrated
    from sat_dengue.model_training.exp_delta03_adapter import reload_native

    replay = "cached_payloads" in context
    for cell in context["plan"]["cells"]:
        _assert_identity(context)
        ident = cell["id"]
        if replay:
            native = context["cached_payloads"]
            model = reload_native(
                native[ident + ".model.ubj"], json.loads(native[ident + ".model.json"])
            )
            cal = json.loads(native[ident + ".calibrator.json"])
            policy = json.loads(native[ident + ".policy.json"])
            saved = {"predictions.csv": native[ident + ".predictions.csv"]}
        else:
            model, cal, policy = (
                context["models"][ident],
                context["calibrators"][ident],
                context["policies"][ident],
            )
            saved = context["store"].read_stage(ident, "predicted")
        if policy["status"].startswith("NO_EVALUABLE"):
            raise ValueError("Required policy has no selection support; no fake evaluation")
        parts = dict(context["parts"][ident])
        if ident in context["national_annex"]:
            from sat_dengue.experiments.exp_delta03_inputs import validate_national_annex

            validate_national_annex(
                cell,
                context["national_annex"][ident],
                context["national_expected"][ident],
                context["parts"][ident]["evaluation"]["rows"],
            )
            parts["evaluation_national"] = context["national_annex"][ident]
        frames = []
        for role in [*ROLES, "evaluation_national"]:
            if role not in parts:
                continue
            part = parts[role]
            rows = part["rows"].copy()
            raw = model.predict(part["X"])
            score = calibrated(raw, cal, model_sha256=model.metadata["model_sha256"])
            rows["raw_score"] = raw
            rows["score"] = score
            rows["alert"] = apply_policy(score, policy, calibrator_sha256=digest(cal)).astype(int)
            rows["role"] = role
            rows["horizon"] = cell["horizon"]
            rows["year"] = cell["year"]
            columns = [
                "divipola_municipio",
                "divipola_departamento",
                "periodo_mes",
                "horizon",
                "target_month",
                "year",
                "role",
                "truth",
                "target_excess",
                "episode_id",
                "raw_score",
                "score",
                "alert",
                "origin_count",
                "origin_excess",
                "target_p75",
            ]
            frames.append(rows[columns])
        generated = pd.concat(frames, ignore_index=True)
        if saved is None:
            saved = {"predictions.csv": _table_bytes(generated)}
            context["store"].save_stage(ident, "predicted", saved)
        reopened = _read_table(saved["predictions.csv"])
        if not np.array_equal(
            generated.score.to_numpy(), reopened.score.to_numpy()
        ) or not np.array_equal(generated.alert.to_numpy(), reopened.alert.to_numpy()):
            raise ValueError("Native replay probabilities/alerts changed")
        # Full key/label/outcome values must survive the actual protected CSV round trip.
        identity_columns = [
            "divipola_municipio",
            "divipola_departamento",
            "periodo_mes",
            "horizon",
            "target_month",
            "year",
            "role",
            "truth",
            "target_excess",
            "episode_id",
            "alert",
            "origin_count",
            "origin_excess",
            "target_p75",
        ]
        left, right = generated[identity_columns].copy(), reopened[identity_columns].copy()
        for name in ["truth", "target_excess", "origin_excess", "horizon", "year", "alert"]:
            left[name] = left[name].astype("Int64")
            right[name] = right[name].astype("Int64")
        for name in ["origin_count", "target_p75"]:
            left[name] = left[name].astype(float)
            right[name] = right[name].astype(float)
        if _frame_hash(left) != _frame_hash(right) or not np.array_equal(
            generated.raw_score.to_numpy(), reopened.raw_score.to_numpy()
        ):
            raise ValueError("Prediction/cohort key-label correspondence changed")
        context["predictions"][ident] = reopened
    return context


def _monitored(
    context: dict[str, Any], cell: dict[str, Any], role: str, scope: str | None = None
) -> float:
    from sat_dengue.data.exp_delta03 import temporal_roles

    rows = context["calendar"].loc[context["calendar"].horizon.eq(cell["horizon"])].copy()
    assignment = temporal_roles(rows, cell["year"], cell["horizon"])
    selected = assignment.eq("evaluation" if role == "evaluation_national" else role)
    target = rows.divipola_departamento.isin(["50", "73"])
    if role != "evaluation_national":
        if cell["reference"] == "transfer" and role != "evaluation":
            selected &= ~target
        elif role != "train":
            selected &= target
    if scope in {"Meta", "Tolima"}:
        selected &= rows.divipola_departamento.eq("50" if scope == "Meta" else "73")
    elif scope == "Meta_Tolima":
        selected &= target
    if cell["reference"] == "water":
        selected &= rows.coverage_water.fillna(False)
    elif cell["reference"] == "era5":
        selected &= rows.coverage_era5.fillna(False)
    return int(selected.sum()) / 12


@_checked_node
def evaluate(context: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp_delta03_contract import canonical
    from sat_dengue.experiments.exp_delta03_evaluation import metrics

    if "cached_payloads" in context:
        return context
    for cell in context["plan"]["cells"]:
        _assert_identity(context)
        ident = cell["id"]
        store = context["store"]
        saved = store.read_stage(ident, "evaluated")
        if saved is None:
            frame = context["predictions"][ident]
            roles = {}
            for role in ("train", "calibration", "selection", "evaluation"):
                rows = frame.loc[frame.role.eq(role)]
                roles[role] = metrics(
                    rows,
                    monitored_exposure=_monitored(context, cell, role),
                    expected_rows=len(context["parts"][ident][role]["rows"]),
                )
                roles[role]["interpretation"] = {
                    "train": "in_sample_training",
                    "calibration": "calibration_diagnostic",
                    "selection": "selection_development",
                    "evaluation": cell["evidence_type"],
                }[role]
                if role == "calibration":
                    raw = rows.copy()
                    raw["score"] = raw.raw_score
                    before = metrics(raw)
                    roles[role].update(
                        brier_before=before["brier"],
                        brier_after=roles[role]["brier"],
                        ece_before=before["calibration"]["expected_calibration_error"],
                        ece_after=roles[role]["calibration"]["expected_calibration_error"],
                    )
            national = frame.loc[frame.role.eq("evaluation_national")]
            regional = frame.loc[frame.role.eq("evaluation")]
            scopes = {"Meta_Tolima": roles["evaluation"]}
            for scope, code in [("Meta", "50"), ("Tolima", "73")]:
                rows = regional.loc[regional.divipola_departamento.eq(code)]
                scopes[scope] = metrics(
                    rows,
                    monitored_exposure=_monitored(context, cell, "evaluation", scope),
                    expected_rows=len(rows),
                )
            scopes["national"] = (
                metrics(
                    national,
                    monitored_exposure=_monitored(context, cell, "evaluation_national"),
                    expected_rows=len(national),
                )
                if len(national)
                else {"status": "NO_EVALUABLE_NO_NATIONAL_EVALUATION_ANNEX", "rows": 0}
            )
            comparator_metrics = {}
            # Deterministic rules have distinct excess inputs and no probabilities.
            for name in ["CHANNEL", "PERSISTENCE"]:
                control = regional.copy()
                control["alert"] = (
                    control.origin_count.gt(control.target_p75)
                    if name == "CHANNEL"
                    else control.origin_excess.eq(1)
                ).astype(int)
                comparator_metrics[name] = metrics(
                    control,
                    monitored_exposure=_monitored(context, cell, "evaluation"),
                    probabilities_available=False,
                )
            for name in ["R0", "G0_OFF", "G0_ON", "G1"]:
                from sat_dengue.experiments.exp_delta03_evaluation import paired

                control = context["comparators"][ident][name]
                _, control = paired(regional, control)
                comparator_metrics[name] = metrics(
                    control,
                    monitored_exposure=_monitored(context, cell, "evaluation"),
                    expected_rows=len(regional),
                )
            value = {
                "schema": "exp-delta03-metrics-v1",
                "cell_id": ident,
                "roles": roles,
                "scopes": scopes,
                "comparators": comparator_metrics,
                "transmission_profiles": {"status": "NO_EVALUABLE_PROFILE_MAPPING_NOT_BOUND"},
                "outcome_definition": "distinct_H5_onset_and_target_excess",
                "regime": "RETROSPECTIVE_CONSOLIDATED",
                "operational_PIT": False,
            }
            saved = {"metrics.json": canonical(value)}
            store.save_stage(ident, "evaluated", saved)
        context["evaluations"][ident] = json.loads(saved["metrics.json"])
    return context


@_checked_node
def compare_ablations(context: dict[str, Any]) -> dict[str, Any]:

    from sat_dengue.experiments.exp_delta03_evaluation import difference, paired, uncertainty

    if "cached_payloads" in context:
        return context
    points = []
    groups: dict[Any, Any] = {}
    lookup = {c["id"]: c for c in context["plan"]["cells"]}
    for pair in context["plan"]["pairs"]:
        _assert_identity(context)
        left, right = pair["left"], pair["right"]
        a = context["predictions"][left]
        a = a.loc[a.role.eq("evaluation")]
        b = context["predictions"][right]
        b = b.loc[b.role.eq("evaluation")]
        a, b = paired(a, b)
        positive = a.truth.eq(1)
        cell = lookup[left]
        points.append(
            {
                **pair,
                "horizon": cell["horizon"],
                "year": cell["year"],
                "budget": context["contract"]["policy"]["B"],
                "calibration_method": context["contract"]["calibration"]["method"],
                "left_model_sha256": context["models"][left].metadata["model_sha256"],
                "right_model_sha256": context["models"][right].metadata["model_sha256"],
                "cohort_sha256": cell["roles"]["evaluation"]["key_label_sha256"],
                "paired_onsets": {
                    "gained_left": int((positive & a.alert.eq(1) & b.alert.eq(0)).sum()),
                    "lost_left": int((positive & a.alert.eq(0) & b.alert.eq(1)).sum()),
                    "shared_detected": int((positive & a.alert.eq(1) & b.alert.eq(1)).sum()),
                    "shared_missed": int((positive & a.alert.eq(0) & b.alert.eq(0)).sum()),
                },
                "difference": difference(
                    context["evaluations"][left]["roles"]["evaluation"],
                    context["evaluations"][right]["roles"]["evaluation"],
                ),
            }
        )
        group = (
            cell["variant"],
            cell["horizon"],
            "stress2024" if cell["year"] == 2024 else "development",
        )
        groups.setdefault(group, []).append((a, b, cell))
    intervals = []
    for (variant, horizon, kind), pieces in groups.items():
        a = pd.concat([p[0] for p in pieces], ignore_index=True)
        b = pd.concat([p[1] for p in pieces], ignore_index=True)
        ledgers = []
        for _, _, cell in pieces:
            calendar = context["calendar"].loc[context["calendar"].horizon.eq(horizon)].copy()
            from sat_dengue.data.exp_delta03 import temporal_roles

            mask = temporal_roles(calendar, cell["year"], horizon).eq(
                "evaluation"
            ) & calendar.divipola_departamento.isin(["50", "73"])
            if cell["reference"] == "water":
                mask &= calendar.coverage_water.fillna(False)
            if cell["reference"] == "era5":
                mask &= calendar.coverage_era5.fillna(False)
            grid = calendar.loc[mask, ["divipola_municipio", "target_month"]].copy()
            grid["year"] = pd.PeriodIndex(grid.target_month, freq="M").year
            ledger = (
                grid.groupby(["divipola_municipio", "year"]).size().rename("months").reset_index()
            )
            ledger["monitored_exposure"] = ledger.months / 12
            ledgers.append(ledger.drop(columns="months"))
        value = uncertainty(
            a, b, pd.concat(ledgers, ignore_index=True), context["contract"]["uncertainty"]
        )
        intervals.append({"variant": variant, "horizon": horizon, "stratum": kind, **value})
    pooled = []
    from sat_dengue.experiments.exp_delta03_evaluation import metrics

    for (variant, horizon, kind), entries in groups.items():
        _assert_identity(context)
        a = pd.concat([e[0] for e in entries], ignore_index=True)
        b = pd.concat([e[1] for e in entries], ignore_index=True)
        exposure = sum(_monitored(context, e[2], "evaluation") for e in entries)
        pooled.append(
            {
                "variant": variant,
                "horizon": horizon,
                "stratum": kind,
                "left": metrics(a, monitored_exposure=exposure),
                "right": metrics(b, monitored_exposure=exposure),
            }
        )
    context["comparisons"] = {
        "schema": "exp-delta03-comparisons-v1",
        "pairs": points,
        "uncertainty": intervals,
        "pooled_horizon_metrics": pooled,
        "causal_claim": False,
        "tracking_link_owner": "post-publication verified tracking receipt",
    }
    return context


@_checked_node
def publish_bundle(context: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp_delta03_contract import canonical, digest

    _assert_identity(context)
    if "cached_payloads" in context:
        return context
    cells = []
    payloads = {}
    for cell in context["plan"]["cells"]:
        ident = cell["id"]
        for phase in ("trained", "calibrated", "selected", "predicted", "evaluated"):
            saved = context["store"].read_stage(ident, phase)
            if saved is None:
                raise ValueError("Missing final native scientific stage")
            for name, raw in saved.items():
                payloads[ident + "." + name] = raw
        payloads[ident + ".cohort.csv"] = _table_bytes(
            context["predictions"][ident][
                ["divipola_municipio", "periodo_mes", "horizon", "target_month", "role", "truth"]
            ]
        )
        model = context["models"][ident]
        cal = context["calibrators"][ident]
        policy = context["policies"][ident]
        cells.append(
            {
                "id": ident,
                "variant": cell["variant"],
                "horizon": cell["horizon"],
                "year": cell["year"],
                "training_scope": cell["training_scope"],
                "evaluation_scope": "national_with_frozen_Meta_Tolima_primary"
                if ident in context["national_annex"]
                else "Meta_Tolima",
                "status": "EVALUABLE",
                "metrics": context["evaluations"][ident],
                "model_sha256": model.metadata["model_sha256"],
                "calibrator_sha256": digest(cal),
                "policy_sha256": digest(policy),
                "cohort_sha256": cell["roles"]["evaluation"]["key_label_sha256"],
                "parameters_sha256": digest(context["contract"]["model"]),
                "predictors_sha256": digest(cell["columns"]),
                "parameters": context["contract"]["model"],
            }
        )
    counts = context["plan"]["counts"]
    synthetic = context["synthetic"]
    # Native counters are a pre-tracking snapshot; delivery incorporates the mirror receipt.
    activity = {
        "real_model_fits": 0 if synthetic else len(cells),
        "real_calibrations": 0 if synthetic else len(cells),
        "synthetic_model_fits": len(cells) if synthetic else 0,
        "synthetic_calibrations": len(cells) if synthetic else 0,
        "hyperparameter_searches": 0,
        "permanent_mlflow_writes": 0,
    }
    result = {
        "schema": "exp-delta03-results-v1",
        "identity": context["identity"],
        "identity_sha256": digest(context["identity"]),
        "regime": "RETROSPECTIVE_CONSOLIDATED",
        "operational_PIT": False,
        "cells": cells,
        "comparisons": context["plan"]["pairs"],
        "activity_counters": activity,
        "counts": counts,
        "unsupported": context["plan"]["unsupported"],
    }
    payloads.update(
        {
            "result.json": canonical(result),
            "execution-plan.json": canonical(context["plan"]),
            "comparisons.json": canonical(context["comparisons"]),
            "columns.json": canonical(
                {
                    "schema": "exp-delta03-columns-v1",
                    "cells": {c["id"]: c["columns"] for c in context["plan"]["cells"]},
                    "numeric_only": True,
                    "identifiers_in_X": False,
                }
            ),
            "provenance.json": canonical(
                {
                    "schema": "exp-delta03-provenance-v1",
                    "identity": context["identity"],
                    "identity_sha256": digest(context["identity"]),
                    "execution_plan": digest(context["plan"]),
                    "input_source": context["input_source"],
                    "activity_counters": activity,
                }
            ),
        }
    )
    _assert_identity(context)
    _validate_artifacts(payloads)
    context["publication"] = context["store"].publish(payloads)
    context["result"] = result
    return context


@_checked_node
def track_results(context: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp_delta03_contract import digest
    from sat_dengue.tracking.exp_delta03 import mirror

    _assert_identity(context)
    tracking = mirror(
        ROOT,
        context["publication"],
        context["roots"]["tracking"],
        synthetic=context["synthetic"],
        permission=context["permission"],
    )
    _assert_identity(context)
    receipt = {
        "schema": "exp-delta03-delivery-receipt-v1",
        "native_publication": context["publication"],
        "tracking": tracking,
        "execution_identity_sha256": digest(context["identity"]),
        "activity_counters": {
            **context["result"]["activity_counters"],
            "permanent_mlflow_writes": tracking["permanent_writes"],
        },
        "invocation": context["invocation"],
        "status": "GENERATED_E2E_COMPLETE"
        if context["synthetic"]
        else "AUTHORIZED_RETROSPECTIVE_COMPLETE",
        "operational_PIT": False,
        "phase3_authorized": False if context["synthetic"] else True,
    }
    context["store"].__exit__(None, None, None)
    return receipt


def verify_executable_annex(
    root: Path, annex: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    """Structural admission hashes every pinned input without reading private table rows."""
    if annex.get("schema") != "exp-delta03-evaluation-annex-v1":
        raise ValueError("Unsupported executable annex")
    expected = {c["id"] for c in plan["cells"]}
    national = {c["id"] for c in plan["cells"] if c["reference"] != "transfer"}
    if set(annex["national_cells"]) != national or set(annex["comparators"]) != expected:
        raise ValueError("Executable annex cell inventory differs")
    descriptors = [annex["outcomes"], annex["calendar"]]
    if "exposure" not in annex:
        raise ValueError("Explicit municipality-year exposure ledger required")
    descriptors.append(annex["exposure"])
    for record in annex["national_cells"].values():
        descriptors.extend([record["rows"], record["X"]])
        if record["cohort"]["rows"] < 1:
            raise ValueError("Empty national cohort")
    for arms in annex["comparators"].values():
        if set(arms) != {"R0", "G0_OFF", "G0_ON", "G1"}:
            raise ValueError("Frozen comparator inventory differs")
        descriptors.extend(arms.values())
    for descriptor in descriptors:
        path = safe_path(root, descriptor["path"], "data/processed/exp_delta03-inputs")
        if identity(path) != {k: descriptor[k] for k in ["sha256", "bytes"]}:
            raise ValueError("Executable input payload changed")
    return {
        "tables": len(descriptors),
        "national_cells": len(national),
        "regional_comparator_cells": len(expected),
        "rows_parsed": 0,
    }


def phase2_preflight(parameters: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.configuration import validate_parameters

    if validate_parameters(parameters) != {
        "profile": "exp_delta03_preflight",
        "tracking": "disabled",
    }:
        raise ValueError("Metadata preflight requires its exact disabled-tracking profile")
    contract, sha = _public_contract()
    contract = resolve_evaluation_annex(ROOT, contract)
    context = read_metadata(ROOT, contract)
    executable = None
    if contract.get("evaluation_annex"):
        executable = verify_executable_annex(ROOT, contract["evaluation_annex"], context["plan"])
    return {
        "schema": "exp-delta03-training-preflight-v1",
        "executable_annex": executable,
        "training_contract_sha256": sha,
        "matrix_manifest_sha256": contract["matrix_bundle"]["manifest_sha256"],
        "counts": context["plan"]["counts"],
        "real_rows_parsed": 0,
        "real_model_fits": 0,
        "real_calibrations": 0,
        "permanent_mlflow_writes": 0,
        "reservations": 0,
        "decision_status": contract["decision_status"],
        "phase3_authorized": False,
        "national_evaluation": contract["national_evaluation"]["status"],
    }


class Delta03Phase2ReceiptDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        path = Path(filepath)
        self.relative = str(path.relative_to(ROOT)) if path.is_absolute() else filepath
        safe_path(ROOT, self.relative, "tmp/exp-delta03-phase2")

    def load(self) -> dict[str, Any]:
        raise DatasetError("Use an explicit immutable Phase2 receipt identity")

    def save(self, data: dict[str, Any]) -> None:
        import os
        import tempfile

        from sat_dengue.experiments.exp_delta03_contract import canonical

        raw = canonical(data)
        sha = hashlib.sha256(raw).hexdigest()
        folder = safe_path(ROOT, self.relative, "tmp/exp-delta03-phase2")
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        final = safe_path(ROOT, self.relative + "/" + sha + ".json", "tmp/exp-delta03-phase2")
        if final.exists():
            if final.read_bytes() != raw:
                raise ValueError("Existing receipt changed")
            return
        fd, name = tempfile.mkstemp(prefix=".receipt-", dir=folder)
        staging = Path(name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(staging, final)
        finally:
            staging.unlink(missing_ok=True)

    def _describe(self) -> dict[str, Any]:
        return {"root": self.relative, "mode": "immutable_metadata_or_generated_delivery_receipt"}


def verify_annex_preparation(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    """Verify preparation bytes/metadata only; never admit missing scientific inputs."""
    descriptor = contract["annex_preparation"]
    report_path = safe_path(root, descriptor["path"], "docs/product/experiments/EXP-DELTA03")
    raw = report_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != descriptor["sha256"]:
        raise ValueError("Annex preparation inventory changed")
    report = json.loads(raw)
    if (
        report["schema"] != "exp-delta03-annex-preparation-v1"
        or report["status"] != "PREPARED_WITH_EXPLICIT_PENDING_INPUTS"
        or report["execution_ready"] is not False
        or not report["pending_inputs"]
        or report["phase1_manifest_sha256"] != contract["matrix_bundle"]["manifest_sha256"]
        or report["activity_counters"]
        != {
            k: 0
            for k in [
                "real_model_fits",
                "real_calibrations",
                "real_predictions",
                "permanent_mlflow_writes",
            ]
        }
    ):
        raise ValueError("Invalid bounded annex preparation")
    prefix = "data/processed/exp_delta03-inputs"
    publication = report["protected_preparation"]
    folder = safe_path(root, publication["path"], prefix)
    manifest_path = safe_path(root, publication["path"] + "/manifest.json", prefix)
    manifest_raw = manifest_path.read_bytes()
    if hashlib.sha256(manifest_raw).hexdigest() != publication["manifest_sha256"]:
        raise ValueError("Annex preparation manifest changed")
    manifest = json.loads(manifest_raw)
    if (
        manifest["files"] != report["files"]
        or hashlib.sha256(canonical(manifest["files"])).hexdigest() != folder.name
        or manifest["bundle_id"] != folder.name
        or publication["bundle_id"] != folder.name
        or {p.name for p in folder.iterdir()} != {*manifest["files"], "manifest.json"}
    ):
        raise ValueError("Annex preparation content identity changed")
    for name, expected in manifest["files"].items():
        if Path(name).name != name:
            raise ValueError("Unsafe annex member")
        path = safe_path(root, publication["path"] + "/" + name, prefix)
        if identity(path) != expected:
            raise ValueError("Annex preparation member changed")
    payload = json.loads((folder / "preparation.json").read_bytes())
    if payload != {k: v for k, v in report.items() if k not in {"files", "protected_preparation"}}:
        raise ValueError("Public/protected annex correspondence changed")
    return report
