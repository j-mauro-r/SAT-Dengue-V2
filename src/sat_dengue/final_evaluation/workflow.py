"""Pure frozen evaluation steps with explicit inputs and no fit/search/selection route."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import AUTHORITIES, canonical_bytes, resolve_configuration
from sat_dengue.model_evaluation.contract import _validate_window_role_calendar
from sat_dengue.model_evaluation.decision_policy import validate_decision_policy
from sat_dengue.model_training.candidate_families import restore_model
from sat_dengue.model_training.references import persistence_reference
from sat_dengue.training_preparation.serialization import bytes_record, json_bytes, serialize_table

from .cohorts import build_cohorts, validate_cohort
from .evaluation import evaluate_horizon, research_result
from .identities import FINAL, NATIVE, PROPOSAL_SHA
from .prediction import calibrate_probability, prediction_frame
from .synthetic import synthetic_sources

AUTHORITY_SEMANTIC_SHA = {
    "training_preparation_contract_v1": (
        "b44883fbe5f2f128168b3e9c5c8f770d1894303f364f4c6214170241a1ebb00f"
    ),
    "model_engineering_contract_v1": (
        "31a20af5c2130f7a2e43116f6a0a9b4e10bd0e150c08b9d3c848a48c9cc3b196"
    ),
    "champion_decision_policy_v1": (
        "0481efe08ff0fc9e75f9d42864356c67564c8753f8dd7d18c994810b198a0db5"
    ),
    "model_evaluation_contract_v1": (
        "63c964eb87805c91fac348446c668d277c8c5f3bb2dcf2a10352f0ea7530c292"
    ),
    "probability_calibration_thresholds_contract_v1": (
        "a3c49880035917f84b27e8742f110488f7dd6bb5e3241bc3982994e226be7793"
    ),
}

FAMILIES = ("xgboost", "lightgbm", "gam")


def evaluation_contract(resolved: dict[str, Any], mode: str) -> None:
    body = {k: v for k, v in resolved.items() if k != "configuration_sha256"}
    if hashlib.sha256(canonical_bytes(body)).hexdigest() != resolved[
        "configuration_sha256"
    ] or resolved["operational"] != {"profile": "evaluation_" + mode, "tracking": "disabled"}:
        raise ValueError("Unapproved frozen evaluation configuration/profile")
    for name, entry in resolved["authorities"].items():
        if (
            hashlib.sha256(canonical_bytes(entry["document"])).hexdigest()
            != AUTHORITY_SEMANTIC_SHA[name]
        ):
            raise ValueError("Scientific values cannot be overwritten")
    contract = resolved["authorities"]["probability_calibration_thresholds_contract_v1"]["document"]
    _validate_window_role_calendar(contract, contract["reserved_final_block_start"])


def resolve_replay_configuration(
    inputs: dict[str, Any], parameters: dict[str, Any], sources: dict[str, Any]
) -> dict[str, Any]:
    resolved = resolve_configuration(inputs, parameters)
    resolved["evaluation"] = {"mode": "replay", "source_provenance": sources["provenance"]}
    body = {k: v for k, v in resolved.items() if k != "configuration_sha256"}
    resolved["configuration_sha256"] = hashlib.sha256(canonical_bytes(body)).hexdigest()
    evaluation_contract(resolved, "replay")
    return resolved


def resolve_synthetic_configuration(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    resolved = resolve_configuration(inputs, parameters)
    evaluation_contract(resolved, "synthetic")
    return resolved


def generate_synthetic_sources(resolved: dict[str, Any]) -> dict[str, Any]:
    evaluation_contract(resolved, "synthetic")
    return synthetic_sources(resolved["authorities"])


def validate_sources(sources: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    mode = sources["mode"]
    evaluation_contract(resolved, mode)
    if mode not in ("replay", "synthetic"):
        raise ValueError("Only frozen replay or the internal synthetic fixture is allowed")
    if mode == "synthetic":
        expected = generate_synthetic_sources(resolved)
        for n, value in expected.items():
            same = (
                value.equals(sources[n]) if isinstance(value, pd.DataFrame) else value == sources[n]
            )
            if not same:
                raise ValueError("Foreign/changed synthetic evaluation fixture")
    else:
        if (
            resolved["evaluation"]["source_provenance"] != sources["provenance"]
            or bytes_record(json_bytes(sources["proposal"]))["sha256"] != PROPOSAL_SHA
        ):
            raise ValueError("Frozen proposal/source identity changed")
        provenance = sources["provenance"]
        if provenance["panel_fingerprint"] != bytes_record(serialize_table(sources["panel"])):
            raise ValueError("Frozen source panel changed")
        for path, expected in NATIVE.items():
            document = provenance["native_manifest_documents"][path]
            if (
                bytes_record(json_bytes(document)) != expected
                or provenance["native_payloads"][path] != document["files"]
            ):
                raise ValueError("Frozen source/component manifest identity changed")
        if (
            provenance["source_inputs"]
            != provenance["native_manifest_documents"][FINAL]["identity"]["inputs"]
        ):
            raise ValueError("Frozen source identity changed")
        expected_components = {
            f"{p['candidate']}_t{p['horizon']}" for p in sources["proposal"]["procedures"]
        }
        if set(sources["components"]) != expected_components:
            raise ValueError("Missing frozen components")
        files = provenance["native_payloads"][FINAL]
        for key, component in sources["components"].items():
            if (
                bytes_record(component["model"]) != files[key + "_model.json"]
                or bytes_record(json_bytes(component["preparer"])) != files[key + "_preparer.json"]
            ):
                raise ValueError("Frozen component identity changed")
        if any(
            sources["provenance"][n] != 0
            for n in (
                "real_model_fits",
                "real_preparer_refits",
                "calibrator_fits",
                "threshold_selection",
                "hyperparameter_search",
            )
        ):
            raise ValueError("Fitting/tuning/selection on consumed evidence is forbidden")
    proposal = sources["proposal"]
    if len(proposal["procedures"]) != 6 or {
        (p["candidate"], p["horizon"]) for p in proposal["procedures"]
    } != {(f, h) for f in FAMILIES for h in (1, 2)}:
        raise ValueError("Exactly six frozen procedures required")
    return sources


def construct_cohorts(sources: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    validate_sources(sources, resolved)
    cohorts = build_cohorts(sources["panel"], sources["preparation_contract"], sources["proposal"])
    audits = []
    for c in cohorts.values():
        audit = validate_cohort(c, sources["proposal"])
        if any(
            audit[n] for n in ("missing_labels", "missing_predictor_rows", "unknown_event_rows")
        ):
            raise ValueError("Frozen evaluation requires complete cohorts, labels and context")
        if c.index.target_period.min() != "2025-01" or c.index.target_period.max() != "2025-12":
            raise ValueError("Consumed cohort cannot be repurposed for selection")
        audits.append(audit)
    return {"cohorts": cohorts, "audits": audits}


def replay_raw_probabilities(
    sources: dict[str, Any], cohort_data: dict[str, Any], resolved: dict[str, Any]
) -> dict[str, pd.Series]:
    validate_sources(sources, resolved)
    raw = {}
    for p in sources["proposal"]["procedures"]:
        h = p["horizon"]
        key = f"{p['candidate']}_t{h}"
        c = cohort_data["cohorts"][h]
        if sources["mode"] == "synthetic":
            values = pd.Series(
                0.15 + 0.7 * (np.arange(len(c.X)) % 3 == 0), index=c.X.index, dtype="Float64"
            )
        else:
            component = sources["components"][key]
            model = restore_model(p["candidate"], component["model"], component["preparer"])
            training = component["training"]
            if (
                any(
                    training[n] != bytes_record(serialize_table(f))
                    for n, f in (
                        ("X", c.train_X),
                        ("keys", c.train_index),
                        ("y", c.train_y.to_frame("y")),
                    )
                )
                or model.preparer["fit_X_fingerprint"] != training["X"]
                or training["target_max"] != str(c.train_index.target_period.max())
            ):
                raise ValueError("Saved component training provenance changed")
            values = model.predict(c.X).astype("Float64")
            roundtrip = restore_model(p["candidate"], model.model_bytes(), model.preparer)
            np.testing.assert_array_equal(values, roundtrip.predict(c.X))
        if len(values) != len(c.index) or values.isna().any() or not values.between(0, 1).all():
            raise ValueError("Missing or invalid frozen predictions")
        raw[key] = values
    return raw


def apply_calibration(raw: dict[str, pd.Series], sources: dict[str, Any]) -> dict[str, pd.Series]:
    expected = {f"{p['candidate']}_t{p['horizon']}" for p in sources["proposal"]["procedures"]}
    if set(raw) != expected or any(
        v.isna().any() or not v.between(0, 1).all() for v in raw.values()
    ):
        raise ValueError("Complete frozen prediction coverage required")
    return {
        f"{p['candidate']}_t{p['horizon']}": calibrate_probability(
            raw[f"{p['candidate']}_t{p['horizon']}"], p
        )
        for p in sources["proposal"]["procedures"]
    }


def emit_alerts(
    raw: dict[str, pd.Series],
    calibrated: dict[str, pd.Series],
    sources: dict[str, Any],
    cohort_data: dict[str, Any],
) -> dict[int, dict[str, pd.DataFrame]]:
    if set(raw) != set(calibrated) or any(v.isna().any() for v in calibrated.values()):
        raise ValueError("Missing frozen calibrated predictions")
    result = {
        h: {"persistence": persistence_reference(c.X, horizon=h)}
        for h, c in cohort_data["cohorts"].items()
    }
    for p in sources["proposal"]["procedures"]:
        key = f"{p['candidate']}_t{p['horizon']}"
        result[p["horizon"]][p["candidate"]] = prediction_frame(raw[key], calibrated[key], p)
    return result


def compute_final_metrics(
    predictions: dict[int, dict[str, pd.DataFrame]],
    cohort_data: dict[str, Any],
    sources: dict[str, Any],
    resolved: dict[str, Any],
) -> dict[str, Any]:
    # Path is only provenance metadata; policy validation performs no file access.
    from pathlib import Path

    policy = validate_decision_policy(
        resolved["authorities"]["champion_decision_policy_v1"]["document"],
        Path(AUTHORITIES["champion_decision_policy_v1"]["path"]),
    )
    settings = sources["proposal"]["rules"]["proposed_final"]["uncertainty"]
    frames: dict[str, list[pd.DataFrame]] = {
        "predictions.csv": [],
        "comparison.csv": [],
        "metrics.csv": [],
        "uncertainty.csv": [],
    }
    extra = {}
    for h in (1, 2):
        c = cohort_data["cohorts"][h]
        comparison, metrics, intervals, draws = evaluate_horizon(
            c, predictions[h], settings, policy
        )
        for n, f in [
            ("comparison.csv", comparison),
            ("metrics.csv", metrics),
            ("uncertainty.csv", intervals),
        ]:
            frames[n].append(f)
        for family, prediction in predictions[h].items():
            frames["predictions.csv"].append(
                pd.concat([c.index, prediction], axis=1).assign(
                    candidate=family, horizon=h, y_true=c.y
                )
            )
        extra[f"t{h}_evaluation_index.csv"] = c.index
        extra[f"t{h}_evaluation_context.csv"] = c.context
        extra[f"t{h}_resampled_month_indices.csv"] = pd.DataFrame(
            draws, columns=[str(i) for i in range(draws.shape[1])]
        )
    return {
        "tables": {**{n: pd.concat(f, ignore_index=True) for n, f in frames.items()}, **extra},
        "cohort_audits": cohort_data["audits"],
    }


def apply_decision_policy(
    result: dict[str, Any], resolved: dict[str, Any], sources: dict[str, Any]
) -> dict[str, Any]:
    comparison = result["tables"]["comparison.csv"]
    from pathlib import Path

    policy_document = resolved["authorities"]["champion_decision_policy_v1"]["document"]
    policy = validate_decision_policy(
        policy_document, Path(AUTHORITIES["champion_decision_policy_v1"]["path"])
    )
    detailed = result["tables"]["metrics.csv"]
    for row in comparison[comparison.candidate.ne("persistence")].itertuples():
        annual = detailed[
            detailed.scope.eq("annual")
            & detailed.candidate.eq(row.candidate)
            & detailed.horizon.eq(row.horizon)
        ].set_index("metric")
        required = ["average_precision", "brier", "onset_sensitivity", "false_alarm_ratio"]
        for metric in required:
            if metric not in annual.index or not (
                (pd.isna(annual.loc[metric, "value"]) and pd.isna(getattr(row, metric)))
                or annual.loc[metric, "value"] == getattr(row, metric)
            ):
                raise ValueError("Decision/metrics/policy inconsistency")
        complete = bool(
            annual.loc[required, "evaluable"].all()
            and row.predictions_available == row.examples
            and row.labels_available == row.examples
            and row.unknown_event_rows == 0
        )
        classification = research_result(
            complete,
            row.difference_onset_sensitivity_vs_persistence,
            row.difference_false_alarm_ratio_vs_persistence,
            row.lower_difference_onset_sensitivity,
            row.upper_difference_false_alarm_ratio,
            policy,
        )
        if row.result != classification:
            raise ValueError("Decision/metrics/policy inconsistency")
    decisions = comparison[comparison.candidate.ne("persistence")][
        ["candidate", "horizon", "result"]
    ]
    if len(decisions) != 6 or (
        sources["mode"] == "replay" and set(decisions.result) != {"does_not_meet"}
    ):
        raise ValueError("Frozen decisions disagree with the consumed six-procedure result")
    policy = resolved["authorities"]["champion_decision_policy_v1"]["document"]
    # Read governance disposition. No winner-ranking or selection operation exists here.
    return {
        **result,
        "decisions": decisions.to_dict("records"),
        "G5": policy["human_disposition"]["G5"],
        "champion": policy["human_disposition"]["champion"],
        "mode": sources["mode"],
        "real_model_fits": 0,
        "real_preparer_refits": 0,
        "calibrator_fits": 0,
        "threshold_selection": 0,
        "hyperparameter_search": 0,
    }


def compute_development_metrics(
    sources: dict[str, Any], resolved: dict[str, Any]
) -> dict[str, Any]:
    """Replay development evidence and its full assessment separately from consumed 2025."""
    if sources["mode"] == "synthetic":
        return {
            "tables": {},
            "models_replayed": 0,
            "prediction_rows_replayed": 0,
            "internal_prediction_rows": 0,
        }
    from pathlib import Path

    from sat_dengue.model_assessment.comparison import summarize
    from sat_dengue.model_assessment.workflow import assess_development
    from sat_dengue.model_evaluation.replay import replay_development

    from .identities import STAGE5
    from .parity import assert_table_parity

    development = sources["development"]
    replay = replay_development(
        development,
        resolved["authorities"]["probability_calibration_thresholds_contract_v1"]["document"],
    )
    overall, breakdown, linked = assess_development(
        development["windows"],
        development["contexts"],
        replay["tables"]["posterior_predictions.csv"],
        STAGE5,
    )
    policy = validate_decision_policy(
        resolved["authorities"]["champion_decision_policy_v1"]["document"],
        Path(AUTHORITIES["champion_decision_policy_v1"]["path"]),
    )
    comparison, utility, uncertainty = summarize(overall, policy)
    frames: dict[str, list[pd.DataFrame]] = {
        "window_metrics.csv": overall,
        "breakdown_metrics.csv": breakdown,
        "linked_development_predictions.csv": linked,
        "comparison.csv": comparison,
        "utility.csv": utility,
        "descriptive_uncertainty.csv": uncertainty,
    }
    for name, frame in frames.items():
        assert_table_parity(development["assessment"][name], frame)
    return {**replay, "tables": {**replay["tables"], **frames}}
