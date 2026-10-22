"""Pure configuration resolution; no framework, filesystem or scientific calculation."""

from __future__ import annotations

import hashlib
import json
from typing import Any

# Approved document identities; all scientific values are read from the JSON files.
AUTHORITIES: dict[str, dict[str, str]] = {
    "training_preparation_contract_v1": {
        "path": "docs/product/stage-3/training_preparation_contract_v1.json",
        "sha256": "4405e9c7fb209c287dc5f9a838ded027675bf21a2d0d8b933247eee44362892d",
    },
    "model_engineering_contract_v1": {
        "path": "docs/product/stage-4/model_engineering_contract_v1.json",
        "sha256": "70f2d1e8a5fe8dd950b3be9bd453fc953b07187f5a092e692c3dfe8918e21862",
    },
    "champion_decision_policy_v1": {
        "path": "docs/product/stage-5/champion_decision_policy_v1.json",
        "sha256": "29b5d6d7924c74d0c0b1f3cd2e588d1ab587a22c3f59b64d385469246f7a4ec8",
    },
    "model_evaluation_contract_v1": {
        "path": "docs/product/stage-5/model_evaluation_contract_v1.json",
        "sha256": "77222e8a2159f6bf68f32541c867e80b497a78fc2a8676950a923ebd91ed38a3",
    },
    "probability_calibration_thresholds_contract_v1": {
        "path": "docs/product/stage-5/probability_calibration_thresholds_contract_v1.json",
        "sha256": "9ec4be02eee61bf546ed3127755dbcc78ab5a0511342d88165dbee3018a41bb3",
    },
}


def canonical_bytes(value: Any) -> bytes:
    """Serialize a configuration deterministically, rejecting NaN and infinity."""
    return (
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def validate_parameters(value: dict[str, Any]) -> dict[str, Any]:
    """Reject scientific overrides, unknown keys and unimplemented execution profiles."""
    if set(value) != {"profile", "tracking"}:
        raise ValueError("Only operational profile and tracking parameters are allowed")
    if value["profile"] not in ("foundation", "data") or value["tracking"] != "disabled":
        raise ValueError(
            "Unknown profile or tracking mode; use foundation or data with disabled tracking"
        )
    return dict(value)


def resolve_configuration(inputs: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """Bind approved scientific documents to operational settings and run provenance."""
    operational = validate_parameters(parameters)
    if set(inputs) != {"authorities", "execution"} or set(inputs["authorities"]) != set(
        AUTHORITIES
    ):
        raise ValueError("Invalid configuration input schema")
    for name, expected in AUTHORITIES.items():
        entry = inputs["authorities"][name]
        if set(entry) != {"path", "sha256", "document"}:
            raise ValueError("Invalid authority envelope schema")
        if entry["path"] != expected["path"] or entry["sha256"] != expected["sha256"]:
            raise ValueError("Unapproved scientific authority identity")
        if not isinstance(entry["document"], dict) or "schema" not in entry["document"]:
            raise ValueError("Invalid scientific document schema")
    body = {"schema": "sat-dengue-resolved-configuration-v1", "operational": operational, **inputs}
    return {**body, "configuration_sha256": hashlib.sha256(canonical_bytes(body)).hexdigest()}
