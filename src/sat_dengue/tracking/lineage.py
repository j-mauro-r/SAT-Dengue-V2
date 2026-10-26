"""Verify published engineering bundles and project only approved aggregate lineage."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.stage2 import identity

COUNTERS = (
    "real_model_fits",
    "real_preparer_refits",
    "calibrator_fits",
    "hyperparameter_search",
    "threshold_selection",
)
AGGREGATES = {
    "examples",
    "average_precision",
    "auroc",
    "brier",
    "false_alarm_ratio",
    "onset_sensitivity",
    "detected_onsets",
    "real_onsets",
    "false_alerts",
    "emitted_alerts",
    "onset_precision",
    "missed_episodes",
    "detected_episodes",
    "false_alerts_per_municipality_year",
    "useful_lead_months",
    "calibration_error",
    "evaluable_rows",
    "unavailable_outcomes",
}


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def verified_lineage(record: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Independently rehash complete publication before exposing a safe projection."""
    relative = record["path"]
    if (
        not isinstance(relative, str)
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
    ):
        raise ValueError("Tracking requires a safe relative publication pointer")
    folder = Path(relative)
    if (
        not relative.startswith("tmp/")
        or any(p.is_symlink() for p in (folder, *folder.parents))
        or not folder.resolve().is_relative_to(Path.cwd().resolve() / "tmp")
    ):
        raise ValueError("Tracking publication must remain under ignored local tmp")
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest != record["manifest"]:
        raise ValueError("Publication manifest identity changed")
    if set(p.name for p in folder.iterdir()) != {*manifest["files"], "manifest.json"}:
        raise ValueError("Publication membership changed")
    body = {k: v for k, v in manifest.items() if k != "bundle_id"}
    if digest(body) != manifest["bundle_id"]:
        raise ValueError("Publication bundle identity changed")
    for name, expected in manifest["files"].items():
        if Path(name).name != name or identity(folder / name) != expected:
            raise ValueError("Publication payload identity changed")
    resolved = json.loads((folder / "provenance.json").read_text())
    if (
        digest({k: v for k, v in resolved.items() if k != "configuration_sha256"})
        != manifest["configuration_sha256"]
    ):
        raise ValueError("Publication configuration changed")
    audit = json.loads((folder / "audit.json").read_text())
    if (
        audit["G5"] != "NOT_APPROVED"
        or audit["champion"] != "not_selected"
        or any(audit.get(k, 0) != 0 for k in COUNTERS)
    ):
        raise ValueError("Tracking cannot certify changed scientific boundaries")
    mode = manifest["mode"]
    if mode not in ("replay", "synthetic"):
        raise ValueError("Unapproved execution kind")
    execution = resolved["execution"]
    policy = resolved["authorities"]["champion_decision_policy_v1"]["document"]
    params = {
        "git_revision": execution["git_revision"],
        "git_dirty": str(execution["git_dirty"]).lower(),
        "python_version": execution["python"].split()[0],
        "kedro_version": execution["packages"]["kedro"],
        "mlflow_version": execution["packages"]["mlflow"] or "absent",
        "environment_sha256": digest(execution["environment"]),
        "code_sha256": digest(execution["code"]),
        "input_sha256": digest(resolved.get("evaluation", resolved.get("training", {}))),
        "configuration_sha256": manifest["configuration_sha256"],
        "bundle_id": manifest["bundle_id"],
        "manifest_sha256": identity(folder / "manifest.json")["sha256"],
        "profile": resolved["operational"]["profile"],
        "kind": mode,
        "metric_definition_sha256": execution["code"]["src/sat_dengue/metrics.py"],
        "seed": str(policy["utility"]["seed"]),
        "cohort": "consumed_2025" if mode == "replay" else "synthetic_only",
        "window": "2025-01..2025-12",
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    if "e2e" in execution:
        params["pipeline_identity_sha256"] = execution["e2e"]["identity"]
    for key, value in resolved["authorities"].items():
        params["contract_" + key] = value["sha256"]
        params["version_" + key] = value["document"].get("version", value["document"]["schema"])
    # Pointers have a closed generated shape, never local usernames/source paths.
    if re.fullmatch(r"tmp/[A-Za-z0-9_./-]+/[0-9a-f]{64}", relative) is None:
        raise ValueError("Publication pointer is not an engineering identity")
    params["native_pointer"] = relative
    children: list[dict[str, Any]] = []
    if (folder / "comparison.csv").is_file():
        for row in csv.DictReader((folder / "comparison.csv").open()):
            if row["candidate"] == "persistence":
                continue
            if (
                row["candidate"] not in {"xgboost", "lightgbm", "gam"}
                or row["horizon"] not in {"1", "2"}
                or (mode == "replay" and row["result"] != "does_not_meet")
                or row["result"]
                not in {"does_not_meet", "insufficient_evidence", "meets_research_criteria"}
            ):
                raise ValueError("Frozen decisions changed")
            children.append(
                {
                    "family": row["candidate"],
                    "horizon": row["horizon"],
                    "decision": row["result"],
                    "window": "2025-01..2025-12",
                    "metrics": {k: float(row[k]) for k in AGGREGATES if row.get(k)},
                }
            )
        if [
            {"candidate": c["family"], "horizon": int(c["horizon"]), "result": c["decision"]}
            for c in children
        ] != audit["decisions"]:
            raise ValueError("Published decision and aggregate lineage disagree")
        if len(children) != 6 or len({(c["family"], c["horizon"]) for c in children}) != 6:
            raise ValueError("Incomplete candidate/horizon lineage")
    elif (folder / "development_metrics.csv").is_file():
        grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
        for row in csv.DictReader((folder / "development_metrics.csv").open()):
            key = (row["reference"], row["horizon"], row["window_id"])
            if key[0] not in {"xgboost", "lightgbm", "gam"} or key[1] not in {"1", "2"}:
                raise ValueError("Unknown training lineage")
            child = grouped.setdefault(
                key,
                {
                    "family": key[0],
                    "horizon": key[1],
                    "window": key[2],
                    "decision": "not_applicable",
                    "metrics": {},
                },
            )
            if row["metric"] in AGGREGATES and row["evaluable"] == "True" and row["value"]:
                child["metrics"][row["metric"]] = float(row["value"])
        children = list(grouped.values())
    else:
        for family in ("xgboost", "lightgbm", "gam"):
            if family + "_predictions.csv" not in manifest["files"]:
                raise ValueError("Incomplete synthetic training lineage")
            children.append(
                {
                    "family": family,
                    "horizon": "1",
                    "window": "synthetic",
                    "decision": "not_applicable",
                    "metrics": {},
                }
            )
    return params, children
