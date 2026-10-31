"""EXP04 historical raw scores, using the frozen M00 recipes and native state format.

No source reader or tracking backend lives here. Callers supply the existing
paired M00 cohort and verified replay cells. Historical predictors are new EXP04
objects; neither their scores nor their state overwrite the reference.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp03 import load_protocol
from sat_dengue.experiments.exp03_1_reporting import _restore_frame
from sat_dengue.experiments.exp03_persistence import NativePredictor, fit_native
from sat_dengue.experiments.exp03_preflight import safe_path
from sat_dengue.experiments.exp04_baseline import KEYS, validate_scores
from sat_dengue.experiments.exp04_contract import ROOT, digest, protocol


def configuration() -> dict[str, Any]:
    manifest = json.loads((ROOT / "BASELINE_MANIFEST.json").read_text())
    design = load_protocol()["design"]
    if (
        manifest["baseline_id"] != "M00-REPLAY-v1"
        or manifest["status"] != "VERIFIED_OBSERVABLE_REPLAY"
        or manifest["ordered_predictors"] != design["variants"]["V09"]
        or manifest["family_parameters"] != design["families"]
        or manifest["seed"] != design["seed"]
        or json.loads((ROOT / "protocol.json").read_text()) != protocol()
        or hashlib.sha256((ROOT / "DESING.md").read_bytes()).hexdigest()
        != protocol()["design_sha256"]
    ):
        raise ValueError("EXP04 frozen M00 configuration or authority changed")
    return manifest


def calendar(*, windows: tuple[int, ...] = (12, 24, 36)) -> dict[str, Any]:
    """Deduplicate refits across overlapping windows AND cuts before fitting."""
    if windows != (12, 24, 36):
        raise ValueError("EXP04 admits 12/24/36 only; expanding is NOT_EVALUABLE")
    cfg = configuration()
    training_starts = {role["train"][0] for role in cfg["reference_temporal_roles"]}
    if len(training_starts) != 1:
        raise ValueError("M00 training boundary differs across cuts; refits cannot be shared")
    training_start = next(iter(training_starts))
    jobs: dict[str, Any] = {}
    groups = []
    for original in cfg["oof_history_assessment"]["cell_groups"]:
        cut, horizon, objective = (original[k] for k in ("cut", "horizon", "objective"))
        year = int(cut[-4:])
        if year not in (2020, 2021, 2022, 2024) or (horizon, objective) not in (
            (1, "onset"),
            (2, "onset"),
            (2, "excess_control"),
        ):
            raise ValueError("EXP04 rejects 2025 or an unauthorized objective/cut")
        last = pd.Period(f"{year - 1}-05", freq="M")
        authorized = original["authorized_EXP04_roles"]
        expected_calibration = {str(n): [str(last - (n - 1)), str(last)] for n in windows}
        expected_selection = [f"{year - 1}-{6 + horizon:02}", f"{year - 1}-11"]
        expected_evaluation = [f"{year}-{horizon:02}", f"{year}-12"]
        if (
            authorized["calibration"] != expected_calibration
            or authorized["selection"] != expected_selection
            or authorized["evaluation"] != expected_evaluation
        ):
            raise ValueError(
                "EXP04 configured roles differ from the authorized May/November calendar"
            )
        retained_start = pd.Period(original["roles"]["calibration"][0], freq="M")
        old_cutoff = original["roles"]["train"][1]
        for family in protocol()["families"]:
            roles = {
                "calibration": authorized["calibration"]["36"],
                "selection": authorized["selection"],
                "evaluation": authorized["evaluation"],
            }
            group = {
                "cut": cut,
                "horizon": horizon,
                "objective": objective,
                "family": family,
                "reference_cell_id": original["cells"][family],
                "roles": roles,
                "calibration_cutoff": f"{year - 1}-05-31",
                "decision_date": f"{year - 1}-11-30",
                "jobs": [],
                "generate_or_replace_by_window": {},
            }
            for month in pd.period_range(last - 35, last, freq="M"):
                issue = str(month - horizon)
                reuse = month >= retained_start and old_cutoff < issue
                origin = {
                    "family": family,
                    "horizon": horizon,
                    "objective": objective,
                    "target_month": str(month),
                    "origin_month": issue,
                    "training_start": training_start,
                    "source": "retained" if reuse else "historical_refit",
                }
                # Retained predictors differ across cuts. Historical refits share
                # the same start, strict cutoff, cohort and frozen configuration.
                if reuse:
                    origin["reference_cell_id"] = original["cells"][family]
                job_id = digest(origin)
                membership = [n for n in windows if month >= last - (n - 1)]
                use = {"cut": cut, "windows": membership, "role": "calibration"}
                jobs.setdefault(job_id, {**origin, "job_id": job_id, "uses": []})
                jobs[job_id]["uses"].append(use)
                group["jobs"].append(job_id)
            for size in windows:
                group["generate_or_replace_by_window"][str(size)] = sum(
                    jobs[j]["source"] == "historical_refit"
                    and size in next(u for u in jobs[j]["uses"] if u["cut"] == cut)["windows"]
                    for j in group["jobs"]
                )
            expected = {str(n): n - (4 if horizon == 1 else 3) for n in windows}
            if group["generate_or_replace_by_window"] != expected:
                raise ValueError("EXP04 authorized OOF inventory differs from calendar")
            declared = original["pending_OOF"]["generate_or_replace_months"]
            if any(declared[f"{n}_months"] != expected[str(n)] for n in windows):
                raise ValueError("EXP04 manifest OOF inventory differs from generated calendar")
            groups.append(group)
    result = {
        "schema": "exp04-oof-calendar-v1",
        "baseline_id": cfg["baseline_id"],
        "configuration_id": digest(
            {
                "predictors": cfg["ordered_predictors"],
                "families": cfg["family_parameters"],
                "seed": cfg["seed"],
                "target": protocol()["target"],
            }
        ),
        "groups": groups,
        "jobs": list(jobs.values()),
        "counts": {
            "groups": len(groups),
            "historical_refits": sum(j["source"] == "historical_refit" for j in jobs.values()),
            "retained_origin_jobs": sum(j["source"] == "retained" for j in jobs.values()),
            "group_month_uses": sum(len(g["jobs"]) for g in groups),
            "A1_A2_A3_cells": len(groups) * len(windows),
            "prediction_rows": None,
            "prediction_rows_rule": "sum_of_actual_eligible_month_rows_per_unique_job",
        },
        "expanding": "NOT_EVALUABLE",
        "2025": "NOT_EVALUABLE",
    }
    result["calendar_id"] = digest(result)
    return result


def _key(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.sort_values(KEYS)[KEYS].to_dict(orient="records")


def retained_scores(job: dict[str, Any], expected: pd.DataFrame, cell: Any) -> pd.DataFrame:
    """Require exact keys, labels, features, identity and a strictly earlier fit."""
    spec = cell.metadata["scientific_cell"]
    cfg = configuration()
    frame = _restore_frame(cell.metadata["roles"]["calibration"]["frame"])
    frame = frame.loc[frame.target_month.eq(job["target_month"])].copy()
    cutoff = cell.metadata["window"]["train"][1]
    if (
        spec["variant"] != "M00"
        or spec["cell_id"] != job.get("reference_cell_id")
        or any(spec[k] != job[k] for k in ("family", "horizon", "objective"))
        or spec["predictors"] != cfg["ordered_predictors"]
        or cutoff >= job["origin_month"]
        or _key(frame) != _key(expected)
    ):
        raise ValueError("Retained M00 identity, paired support or strict training cutoff differs")
    columns = cfg["ordered_predictors"]
    names = [
        *KEYS,
        "onset_target",
        *(["excess_target"] if job["objective"] != "onset" else []),
        *columns,
    ]
    a, b = (f.sort_values(KEYS).reset_index(drop=True) for f in (frame, expected))
    if any(a[n].astype("string").tolist() != b[n].astype("string").tolist() for n in names):
        raise ValueError("Retained M00 truth or frozen predictor inputs differ")
    raw = cell.predictor.predict(frame[columns])
    if not np.array_equal(np.asarray(raw, dtype=float), frame.raw_score.to_numpy(dtype=float)):
        raise ValueError("Retained raw scores lost full precision or predictor identity")
    return frame


def support(
    prepared: dict[tuple[int, str], pd.DataFrame], plan: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Check ALL jobs before any refit. No synthetic or fixed municipality count."""
    cfg = configuration()
    result = {}
    for job in plan["jobs"]:
        source = prepared[job["horizon"], job["objective"]]
        if source.duplicated(KEYS).any() or source.target_month.ge("2025-01").any():
            raise ValueError("Duplicate keys or 2025 in EXP04 prepared cohort")
        if not (
            pd.PeriodIndex(source.target_month, freq="M")
            == pd.PeriodIndex(source.year_month, freq="M") + job["horizon"]
        ).all():
            raise ValueError("EXP04 origin/target horizon drift")
        score = source.loc[source.target_month.eq(job["target_month"])].copy()
        train = source.loc[
            source.target_month.ge(job["training_start"])
            & source.target_month.lt(job["origin_month"])
            & source.year_month.lt(job["origin_month"])
        ].copy()
        target = "onset_target" if job["objective"] == "onset" else "excess_target"
        if (
            score.empty
            or train.empty
            or set(train[target]) != {0, 1}
            or score[cfg["ordered_predictors"]].isna().any().any()
            or train[cfg["ordered_predictors"]].isna().any().any()
        ):
            raise ValueError("EXP04 missing historical training/score/class support")
        # Retain indices, not hundreds of copies of overlapping training tables.
        result[job["job_id"]] = {
            "train_index": train.index,
            "score_index": score.index,
            "target": target,
        }
    return result


def generate(
    prepared: dict[tuple[int, str], pd.DataFrame],
    references: dict[str, Any],
    plan: dict[str, Any],
    *,
    fit: Callable[..., Any] = fit_native,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compute each unique raw forecast once; preserve every cut/window membership."""
    cfg = configuration()
    admitted = support(prepared, plan)
    # Reject an invalid retained artifact before fitting any new predictor.
    reused = {
        j["job_id"]: retained_scores(
            j,
            prepared[j["horizon"], j["objective"]].loc[admitted[j["job_id"]]["score_index"]],
            references[j["reference_cell_id"]],
        )
        for j in plan["jobs"]
        if j["source"] == "retained"
    }
    rows: list[dict[str, Any]] = []
    models: dict[str, Any] = {}
    job_records: list[dict[str, Any]] = []
    for job in plan["jobs"]:
        inputs = admitted[job["job_id"]]
        source = prepared[job["horizon"], job["objective"]]
        train, score = source.loc[inputs["train_index"]], source.loc[inputs["score_index"]]
        target = inputs["target"]
        if job["source"] == "retained":
            cell = references[job["reference_cell_id"]]
            predictor = cell.predictor
            scored = reused[job["job_id"]]
            raw = scored.raw_score
            cutoff = cell.metadata["window"]["train"][1]
        else:
            predictor = fit(
                job["family"],
                train[cfg["ordered_predictors"]],
                train[target].astype(int),
                cfg["family_parameters"][job["family"]],
                cfg["seed"],
            )
            scored, raw, cutoff = (
                score,
                predictor.predict(score[cfg["ordered_predictors"]]),
                str(train.target_month.max()),
            )
        if cutoff >= job["origin_month"]:
            raise ValueError("OOF training cutoff is not strictly before issue")
        state = {
            "family": predictor.family,
            "columns": predictor.columns,
            "envelope_columns": predictor.envelope_columns,
            "support": predictor.support,
            "preparer": predictor.model.preparer,
        }
        native = predictor.model.model_bytes()
        predictor_id = hashlib.sha256(canonical_bytes(state) + native).hexdigest()
        models.setdefault(predictor_id, {"state": state, "native": native})
        record = {
            **job,
            "predictor_id": predictor_id,
            "preparer_id": digest(state["preparer"]),
            "training_target_cutoff": cutoff,
            "training_keys_sha256": digest(_key(train))
            if job["source"] != "retained"
            else digest(_key(_restore_frame(cell.metadata["roles"]["train"]["frame"]))),
            "score_keys_sha256": digest(_key(scored)),
            "score_rows": len(scored),
            "positives": int(scored[target].sum()),
            "negatives": int(len(scored) - scored[target].sum()),
        }
        job_records.append(record)
        for (_, row), value in zip(scored.iterrows(), raw, strict=True):
            prediction = {
                "municipality_code": str(row.municipality_code),
                "origin_month": job["origin_month"],
                "target_month": job["target_month"],
                "forecast_issue_date": job["origin_month"] + "-01",
                "target_date": job["target_month"] + "-01",
                "label_available_date": str(
                    pd.Period(job["target_month"], freq="M").end_time.date()
                ),
                "label_date_assumption": (
                    "retrospective_consolidated_target_month_end_not_notification"
                ),
                "training_cutoff": str(pd.Period(cutoff, freq="M").end_time.date()),
                "training_target_cutoff": cutoff,
                "family": job["family"],
                "horizon": job["horizon"],
                "objective": job["objective"],
                "raw_score": float(value),
                "truth": int(row[target]),
                "error_class": str(row.error_type),
                "role": "calibration",
                "uses": job["uses"],
                "predictor_id": predictor_id,
                "preparer_id": record["preparer_id"],
                "configuration_id": plan["configuration_id"],
                "baseline_id": "M00-REPLAY-v1",
                "source": job["source"],
                "job_id": job["job_id"],
            }
            prediction["score_id"] = digest(prediction)
            rows.append(prediction)
    result = {
        "schema": "exp04-oof-bundle-v1",
        "experiment_id": "EXP04",
        "calendar": plan,
        "jobs": job_records,
        "scores": rows,
        "counts": {
            **plan["counts"],
            "prediction_rows": len(rows),
            "generated_rows": sum(r["source"] == "historical_refit" for r in rows),
            "retained_rows": sum(r["source"] == "retained" for r in rows),
        },
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "scientific_hypotheses": "NOT_EVALUATED",
        "mlflow_writes": 0,
    }
    return result, models


def history(result: dict[str, Any], group: dict[str, Any], months: int) -> pd.DataFrame:
    if months not in (12, 24, 36) or int(group["cut"][-4:]) not in (2020, 2021, 2022, 2024):
        raise ValueError("EXP04 rejects expanding and 2025")
    rows = [
        dict(row, cut=group["cut"])
        for row in result["scores"]
        if row["job_id"] in group["jobs"]
        and any(u["cut"] == group["cut"] and months in u["windows"] for u in row["uses"])
    ]
    frame = pd.DataFrame(rows)
    validate_scores(frame)
    if frame.target_month.nunique() != months:
        raise ValueError("Incomplete EXP04 window support")
    return frame


def publish(result: dict[str, Any], models: dict[str, Any], destination: Path) -> None:
    """Use the existing result.json boundary and native/JSON/checksum convention."""
    from sat_dengue.experiments.exp04_runner import write_result

    body = {**result, "bundle_id": digest(result)}
    write_result(body, destination)
    folder = safe_path(str(destination))
    files = {"result.json": hashlib.sha256((folder / "result.json").read_bytes()).hexdigest()}
    for identity, model in models.items():
        root = folder / "models" / identity
        root.mkdir(parents=True, exist_ok=False)
        for name, raw in (
            ("model.native", model["native"]),
            ("state.json", canonical_bytes(model["state"])),
        ):
            (root / name).write_bytes(raw)
            files[(root / name).relative_to(folder).as_posix()] = hashlib.sha256(raw).hexdigest()
    (folder / "manifest.json").write_bytes(
        canonical_bytes(
            {
                "schema": "exp04-oof-manifest-v1",
                "bundle_id": body["bundle_id"],
                "files": files,
            }
        )
    )


def reload_bundle(destination: Path, expected_bundle_id: str | None = None) -> dict[str, Any]:
    """Validate the native inventory, score hashes and strict dates without fitting."""
    root = safe_path(str(destination))
    if not root.is_relative_to(Path.cwd().resolve() / "tmp"):
        raise ValueError("EXP04 bundles require repository-local tmp")
    inventory = json.loads(safe_path(str(root / "manifest.json")).read_text())
    if inventory.get("schema") != "exp04-oof-manifest-v1":
        raise ValueError("Unknown EXP04 manifest")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != {"manifest.json", *inventory["files"]}:
        raise ValueError("EXP04 bundle file membership differs")
    for name, expected in inventory["files"].items():
        path = safe_path(str(root / name))
        if (
            not path.is_relative_to(root)
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise ValueError("EXP04 integrity failure: " + name)
    result = json.loads((root / "result.json").read_text())
    if expected_bundle_id is not None and expected_bundle_id != inventory["bundle_id"]:
        raise ValueError("EXP04 bundle differs from expected identity")
    if (
        result["bundle_id"] != inventory["bundle_id"]
        or digest({k: v for k, v in result.items() if k != "bundle_id"}) != result["bundle_id"]
    ):
        raise ValueError("EXP04 bundle identity differs")
    plan = result["calendar"]
    if plan["calendar_id"] != digest({k: v for k, v in plan.items() if k != "calendar_id"}):
        raise ValueError("EXP04 calendar identity differs")
    jobs = {job["job_id"]: job for job in result["jobs"]}
    if len(jobs) != len(result["jobs"]) or set(jobs) != {j["job_id"] for j in plan["jobs"]}:
        raise ValueError("EXP04 job inventory differs")
    seen = set()
    counts: dict[str, int] = {}
    verified_models: set[str] = set()
    for row in result["scores"]:
        if row["score_id"] != digest({k: v for k, v in row.items() if k != "score_id"}):
            raise ValueError("EXP04 score integrity failure")
        key = (row["job_id"], row["municipality_code"], row["target_month"])
        if (
            key in seen
            or row["training_target_cutoff"] >= row["origin_month"]
            or pd.Period(row["target_month"], freq="M")
            != (pd.Period(row["origin_month"], freq="M") + row["horizon"])
            or row["target_month"] >= "2025-01"
            or row["configuration_id"] != plan["configuration_id"]
            or row["baseline_id"] != "M00-REPLAY-v1"
            or pd.Timestamp(row["training_cutoff"]) >= pd.Timestamp(row["forecast_issue_date"])
        ):
            raise ValueError("Duplicate OOF score or temporal leakage")
        seen.add(key)
        job = jobs[row["job_id"]]
        for name in (
            "family",
            "horizon",
            "objective",
            "target_month",
            "origin_month",
            "source",
            "uses",
            "predictor_id",
            "preparer_id",
            "training_target_cutoff",
        ):
            if row[name] != job[name]:
                raise ValueError("EXP04 score/job provenance differs")
        counts[row["job_id"]] = counts.get(row["job_id"], 0) + 1
        if row["predictor_id"] in verified_models:
            continue
        model = root / "models" / row["predictor_id"]
        state, native = (model / "state.json").read_bytes(), (model / "model.native").read_bytes()
        if hashlib.sha256(state + native).hexdigest() != row["predictor_id"]:
            raise ValueError("EXP04 predictor identity differs")
        if digest(json.loads(state)["preparer"]) != row["preparer_id"]:
            raise ValueError("EXP04 preparer identity differs")
        verified_models.add(row["predictor_id"])
    if any(counts.get(identity, 0) != job["score_rows"] for identity, job in jobs.items()):
        raise ValueError("EXP04 score count differs from support inventory")
    if result["counts"]["prediction_rows"] != len(result["scores"]):
        raise ValueError("EXP04 prediction row count differs")
    for group in result["calendar"]["groups"]:
        for size in (12, 24, 36):
            history(result, group, size)
    return result


def restore_predictor(root: Path, identity: str) -> NativePredictor:
    from sat_dengue.model_training.candidate_families import restore_model

    directory = safe_path(str(root / "models" / identity))
    state = json.loads((directory / "state.json").read_text())
    native = (directory / "model.native").read_bytes()
    if hashlib.sha256(canonical_bytes(state) + native).hexdigest() != identity:
        raise ValueError("EXP04 native predictor identity differs")
    return NativePredictor(
        state["family"],
        restore_model(state["family"], native, state["preparer"]),
        state["columns"],
        state["envelope_columns"],
        state["support"],
    )
