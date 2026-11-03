"""Authorized frozen G0_OFF score recovery; no DELTA policy implementation.

Run from the repository root using the original modeling environment:
    .venv/bin/python scripts/recover_exp_delta01_selection.py
Only the content-addressed recovery destination and tmp receipts are written.
"""

from __future__ import annotations

import importlib.metadata
import json
import platform
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.canonical.table import CLIMATE, PREDICTORS
from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle, verify_bundle
from sat_dengue.datasets.legacy_preparation.pipeline import parse_fields
from sat_dengue.experiments import exp_beta01 as beta
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table

DESIGN = Path("docs/product/experiments/EXP-DELTA01/protocol.json")
DESIGN_SHA = "c182fbe062faed58100548a43c70cc2a95df05aa86df4532344addb956a3003b"
OUTPUT = Path("data/processed/exp_delta01/recovered_selection")
WORK = Path("tmp/exp-delta01-score-recovery")
EXPECTED = {
    1: {2020: 376, 2021: 661, 2022: 846, 2024: 410},
    2: {2020: 355, 2021: 588, 2022: 779, 2024: 371},
}
ACCEPTANCE = {
    "schema": "exp-delta01-score-recovery-acceptance-v1",
    "authority": "Mauricio: controlled frozen G0_OFF inference request, 2026-11-03",
    "initial_protocol_sha256": DESIGN_SHA,
    "absolute_tolerance": 1e-15,
    "relative_tolerance": 0.0,
    "justification": "Original CSV uses %.17g (binary64 round-trip precision); read with "
    "float_precision=round_trip. Exact equality is expected. The absolute ceiling is "
    "less than five binary64 machine epsilons and admits only tiny floating-point "
    "arithmetic variation, not float32-scale prediction differences or score rounding.",
    "nonfinite": "reject",
    "cohort_keys_labels_and_frozen_alerts": "exact equality required",
    "selection": "infer only after all eight evaluation cells pass; never fit or select policies",
    "expected_selection_rows": EXPECTED,
}
LIMITATIONS = [
    "Reconstructed probabilities are not independently persisted original selection arrays; "
    "no original selection digest exists for direct historical byte equality.",
    "Frozen-model evaluation equivalence and byte-identical repeated reconstruction are "
    "consistency evidence, not independent attestation of historical fit membership.",
    "Common cohort, H5 labels, consolidated-source retrospective availability and original "
    "chronological roles remain unchanged; 2024 is consumed stress and 2025 is excluded.",
    "This recovery establishes no P1 feasibility, policy benefit, independent confirmation, "
    "G5 approval or champion selection. Protocol revision and later DELTA authorization "
    "are pending.",
]


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def fingerprint(path: Path) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"Unsafe/missing file: {path}")
    return bytes_record(path.read_bytes())


def checked(path: Path, expected: dict[str, Any], snapshots: dict[str, Any]) -> None:
    require(fingerprint(path) == expected, f"Identity mismatch: {path}")
    snapshots[str(path)] = expected


def read_bundle(spec: dict[str, Any], snapshots: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    root = Path(spec["path"])
    require(not root.is_symlink(), "Symlink bundle refused")
    fp = fingerprint(root / "manifest.json")
    require(fp["sha256"] == spec["manifest_sha256"], "Manifest pin mismatch")
    manifest = json.loads((root / "manifest.json").read_bytes())
    body = {k: v for k, v in manifest.items() if k != "bundle_id"}
    require(
        bytes_record(canonical_bytes(body))["sha256"] == manifest["bundle_id"] == root.name,
        "Content identity mismatch",
    )
    require(
        {p.name for p in root.iterdir()} == {*manifest["files"], "manifest.json"},
        "Bundle membership mismatch",
    )
    checked(root / "manifest.json", fp, snapshots)
    for name, record in manifest["files"].items():
        require(Path(name).name == name, "Unsafe payload name")
        checked(root / name, record, snapshots)
    for name, record in manifest["sources"].items():
        checked(Path(name), record, snapshots)
    return root, manifest


def probability_audit(actual: Any, expected: Any) -> dict[str, Any]:
    actual, expected = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    require(
        actual.shape == expected.shape and actual.ndim == 1 and len(actual) > 0,
        "Probability support mismatch",
    )
    require(np.isfinite(actual).all() and np.isfinite(expected).all(), "Nonfinite probabilities")
    require(
        ((actual >= 0) & (actual <= 1)).all() and ((expected >= 0) & (expected <= 1)).all(),
        "Probability outside [0, 1]",
    )
    differences = np.abs(actual - expected)
    exceeded = int((differences > ACCEPTANCE["absolute_tolerance"]).sum())
    return {
        "rows": len(actual),
        "max_absolute_difference": float(differences.max()),
        "nonidentical_probabilities": int((actual != expected).sum()),
        "exceeding_tolerance": exceeded,
        "status": "PASS" if exceeded == 0 else "FAIL",
    }


def key_rows(frame: pd.DataFrame) -> list[Any]:
    return frame[beta.KEYS].to_records(index=False).tolist()


def membership(frame: pd.DataFrame, predictors: list[str]) -> dict[str, Any]:
    return {
        "rows": len(frame),
        "onsets": int(frame.onset_target.sum()),
        "keys": bytes_record(serialize_table(frame[beta.KEYS])),
        "keys_targets_labels": bytes_record(
            serialize_table(frame[[*beta.KEYS, "target_month", "onset_target"]])
        ),
        "ordered_float64_predictors": bytes_record(
            serialize_table(frame[predictors].astype(float))
        ),
    }


def load_sources() -> dict[str, Any]:
    snapshots: dict[str, Any] = {}
    require(fingerprint(DESIGN)["sha256"] == DESIGN_SHA, "Initial DELTA protocol changed")
    snapshots[str(DESIGN)] = fingerprint(DESIGN)
    design = json.loads(DESIGN.read_bytes())
    roots, manifests = {}, {}
    for name in ("G0", "canonical", "benchmark"):
        roots[name], manifests[name] = read_bundle(design["sources"][name], snapshots)
    original = json.loads((roots["G0"] / "provenance.json").read_bytes())
    code = original["execution"]["code"]
    for name in (
        "src/sat_dengue/experiments/exp_beta01.py",
        "src/sat_dengue/experiments/exp_beta01_engine.py",
        "src/sat_dengue/experiments/onset.py",
        "src/sat_dengue/canonical/table.py",
        "src/sat_dengue/datasets/legacy_preparation/pipeline.py",
        "src/sat_dengue/datasets/legacy_preparation/persistence.py",
        "src/sat_dengue/training_preparation/serialization.py",
    ):
        checked(Path(name), code[name], snapshots)
    for path in (Path(__file__), Path("src/sat_dengue/configuration.py")):
        checked(path, fingerprint(path), snapshots)
    runtime = {
        n: importlib.metadata.version(n) for n in ("numpy", "pandas", "xgboost", "scikit-learn")
    }
    require(
        all(v == original["execution"]["packages"][n] for n, v in runtime.items()),
        "Original numerical runtime required; do not broaden tolerance",
    )
    protocol = json.loads((roots["G0"] / "protocol.json").read_bytes())
    require(
        protocol == json.loads(Path(design["beta_protocol"]["path"]).read_bytes()),
        "BETA protocol changed",
    )
    columns = json.loads((roots["canonical"] / "columns.json").read_bytes())
    fields = [
        {**f, "dtype": {"boolean": "bool"}.get(f["dtype"], f["dtype"])} for f in columns["columns"]
    ]
    raw = pd.read_csv(
        roots["canonical"] / "canonical_model_table_v1.csv", dtype="string", keep_default_na=False
    )
    require(list(raw) == [f["name"] for f in fields], "Canonical column order changed")
    table = parse_fields(raw, {"schema": fields})
    prepared = beta.prepare(
        {"table": table, "columns": columns, "protocol": protocol},
        {"profile": "exp_beta01", "tracking": "disabled"},
    )
    frames = {}
    for name in ("G0", "benchmark"):
        frame = pd.read_csv(
            roots[name] / "predictions.csv",
            float_precision="round_trip",
            dtype={"municipality_code": "string", "department_code": "string", "alert": "string"},
        )
        frame["alert"] = frame.alert.map(
            {"True": True, "False": False, "true": True, "false": False}
        )
        require(frame.alert.notna().all(), "Invalid alert tokens")
        frames[name] = frame
    return {
        "snapshots": snapshots,
        "design": design,
        "roots": roots,
        "manifests": manifests,
        "original": original,
        "runtime": runtime,
        "prepared": prepared,
        "frames": frames,
        "cells": json.loads((roots["G0"] / "cells.json").read_bytes())["cells"],
        "policies": json.loads((roots["G0"] / "policies.json").read_bytes())["policies"],
    }


@contextmanager
def no_fitting():
    """Fail immediately if any prohibited scientific operation is reached."""
    import xgboost as xgb

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Training, recalibration and threshold selection are forbidden")

    with ExitStack() as stack:
        for obj, names in (
            (xgb, ("train", "cv")),
            (xgb.XGBModel, ("fit",)),
            (xgb.XGBClassifier, ("fit",)),
            (xgb.Booster, ("update", "boost")),
            (beta, ("fit_intercept", "fit_adaptation", "thresholds")),
        ):
            for name in names:
                stack.enter_context(patch.object(obj, name, forbidden))
        yield


def recover(source: dict[str, Any]) -> dict[str, bytes]:
    """Gate all evaluation cells before predicting any selection population."""
    from xgboost import XGBClassifier

    ledger, audits, ready = [], [], []
    off = sorted(
        [c for c in source["cells"] if c["climate"] == "OFF"],
        key=lambda c: (c["horizon"], c["year"]),
    )
    require(
        [(c["horizon"], c["year"]) for c in off]
        == [(h, y) for h, years in EXPECTED.items() for y in years],
        "Expected eight OFF cells",
    )
    for cell in off:
        h, year = cell["horizon"], cell["year"]
        partition = beta.role_parts(
            source["prepared"]["cohorts"][h], year, source["prepared"]["protocol"]
        )
        require(partition["audit"] == cell["role_audit"], "Original roles/embargo changed")
        parts, predictors = partition["parts"], cell["predictors"]
        require(
            predictors == [n for n in PREDICTORS if n not in CLIMATE], "Predictor order changed"
        )
        require(len(parts["selection"]) == EXPECTED[h][year], "Selection population changed")
        keys = {r: set(key_rows(f)) for r, f in parts.items()}
        require(all(len(keys[r]) == len(f) for r, f in parts.items()), "Duplicate role keys")
        for role in ("train", "calibration", "adaptation", "evaluation"):
            require(not keys["selection"] & keys[role], "Selection role leakage")
        for role in ("train", "calibration"):
            require(
                parts[role].target_month.max() < parts["selection"].year_month.min(),
                "Temporal overlap",
            )
        evaluation = parts["evaluation"]
        require(
            bytes_record(serialize_table(evaluation[beta.KEYS]))["sha256"]
            == cell["evaluation_keys_sha256"],
            "Original evaluation keys changed",
        )
        frozen = source["frames"]["G0"]
        frozen = frozen.loc[
            frozen.arm.eq("G0")
            & frozen.climate.eq("OFF")
            & frozen.horizon.eq(h)
            & frozen.year.eq(year)
        ].sort_values(beta.KEYS)
        benchmark = source["frames"]["benchmark"]
        benchmark = benchmark.loc[
            benchmark.arm.eq("G0_OFF") & benchmark.horizon.eq(h) & benchmark.year.eq(year)
        ].sort_values(beta.KEYS)
        require(key_rows(frozen) == key_rows(evaluation), "Evaluation keys differ")
        require(
            frozen.truth.tolist() == evaluation.onset_target.tolist()
            and frozen.target_month.tolist() == evaluation.target_month.tolist(),
            "Evaluation labels/targets differ",
        )
        require(
            all(
                frozen[n].tolist() == benchmark[n].tolist()
                for n in [*beta.KEYS, "target_month", "truth", "score", "alert"]
            ),
            "Stored benchmark differs",
        )
        model_path = source["roots"]["G0"] / cell["model_file"]
        checked(
            model_path, source["manifests"]["G0"]["files"][cell["model_file"]], source["snapshots"]
        )
        model = XGBClassifier(n_jobs=1)
        model.load_model(model_path)
        require(model.get_booster().feature_names == predictors, "Native feature order changed")
        raw = model.predict_proba(evaluation[predictors].astype(float))[:, 1].astype(float)
        score = beta.shifted(raw, np.zeros(len(raw)) + cell["global_offset"])
        audit = {
            "horizon": h,
            "evaluation_year": year,
            **probability_audit(score, frozen.score.to_numpy()),
        }
        policy = next(
            p
            for p in source["policies"]
            if p["arm"] == "G0"
            and p["climate"] == "OFF"
            and p["horizon"] == h
            and p["year"] == year
        )
        alerts = (
            np.zeros(len(score), dtype=bool)
            if policy["threshold"] is None
            else score >= policy["threshold"]
        )
        audit["frozen_alert_discrepancies"] = int((alerts != frozen.alert.to_numpy()).sum())
        if audit["frozen_alert_discrepancies"]:
            audit["status"] = "FAIL"
        audits.append(audit)
        ready.append((cell, parts, model))
    if any(a["status"] != "PASS" for a in audits):
        WORK.mkdir(parents=True, exist_ok=True)
        (WORK / "blocked-evaluation.json").write_bytes(
            canonical_bytes(
                {"status": "RECOVERY_BLOCKED", "audits": audits, "selection_inference_calls": 0}
            )
        )
        raise ValueError("Material evaluation discrepancy; no selection recovery or publication")

    payloads = {
        "acceptance.json": canonical_bytes(ACCEPTANCE),
        "evaluation_reproduction.json": canonical_bytes({"cells": audits}),
        "limitations.json": canonical_bytes({"limitations": LIMITATIONS}),
        "recovery_script.py": Path(__file__).read_bytes(),
    }
    for cell, parts, model in ready:
        selection, predictors = parts["selection"], cell["predictors"]
        raw = model.predict_proba(selection[predictors].astype(float))[:, 1].astype(float)
        score = beta.shifted(raw, np.zeros(len(raw)) + cell["global_offset"])
        probability_audit(score, score)
        roles = {
            r: {**cell["role_audit"][r], **membership(f, predictors)} for r, f in parts.items()
        }
        calibrator = {
            "type": "original_global_log_odds_intercept",
            "offset": cell["global_offset"],
            "cells_identity": fingerprint(source["roots"]["G0"] / "cells.json"),
            "calibration_membership": roles["calibration"],
            "procedure_identity": fingerprint(Path("src/sat_dengue/experiments/exp_beta01.py")),
        }
        name = f"selection-h{cell['horizon']}-{cell['year']}.csv"
        frame = selection[[*beta.KEYS, "department_code", "target_month", "onset_target"]].copy()
        frame["horizon"], frame["evaluation_year"], frame["role"] = (
            cell["horizon"],
            cell["year"],
            "selection",
        )
        frame["raw_score"], frame["score"] = raw, score
        payloads[name] = serialize_table(frame)
        ledger.append(
            {
                "horizon": cell["horizon"],
                "evaluation_year": cell["year"],
                "selection_file": name,
                "model_file": cell["model_file"],
                "model_identity": fingerprint(source["roots"]["G0"] / cell["model_file"]),
                "calibrator": calibrator,
                "calibrator_sha256": bytes_record(canonical_bytes(calibrator))["sha256"],
                "predictors": predictors,
                "transformations": "Original prepare/role_parts; "
                "zone mapping EXITO/SEGURIDAD/ALERTA/EXCESO to 0/1/2/3; float64 X; "
                "positive-class predict_proba float32 converted to float64; original shifted().",
                "roles": roles,
                "selection_disjoint_from_fitted_roles": True,
            }
        )
    payloads["cells.json"] = canonical_bytes({"cells": ledger})
    payloads["provenance.json"] = canonical_bytes(
        {
            "evidence_type": "reconstructed_from_original_frozen_G0_OFF_not_original_export",
            "authority": ACCEPTANCE["authority"],
            "initial_protocol": fingerprint(DESIGN),
            "source_identities": source["snapshots"],
            "runtime": source["runtime"],
            "python": platform.python_version(),
            "script": fingerprint(Path(__file__)),
            "model_fits": 0,
            "calibrator_fits": 0,
            "threshold_selections": 0,
            "inference_calls_per_pass": 16,
            "evaluation_cells_passed": len(audits),
        }
    )
    body = {
        "schema": "exp-delta01-recovered-selection-publication-v1",
        "status": "RECOVERY_VERIFIED",
        "initial_protocol_sha256": DESIGN_SHA,
        "sources": {n: source["design"]["sources"][n] for n in ("G0", "canonical", "benchmark")},
        "files": {n: bytes_record(b) for n, b in payloads.items()},
        "cells": len(ledger),
        "selection_scores": sum(EXPECTED[h][y] for h in EXPECTED for y in EXPECTED[h]),
        "evaluation_rows": sum(a["rows"] for a in audits),
        "model_fits": 0,
        "calibrator_fits": 0,
        "threshold_selections": 0,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    payloads["manifest.json"] = canonical_bytes(
        {**body, "bundle_id": bytes_record(canonical_bytes(body))["sha256"]}
    )
    return payloads


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    frozen_acceptance = WORK / "pre-inference-acceptance.json"
    if frozen_acceptance.exists():
        require(frozen_acceptance.read_bytes() == canonical_bytes(ACCEPTANCE), "Acceptance changed")
    else:
        with frozen_acceptance.open("xb") as stream:
            stream.write(canonical_bytes(ACCEPTANCE))
    with no_fitting():
        source = load_sources()
        payloads = recover(source)
        repeated = recover(load_sources())
    require(payloads == repeated, "Repeated recovery not byte-identical")
    for path, expected in source["snapshots"].items():
        require(fingerprint(Path(path)) == expected, f"Historical input changed: {path}")
    manifest = json.loads(payloads["manifest.json"])
    target = publish_bundle(
        OUTPUT, manifest["bundle_id"], payloads, existing_policy="reuse_identical"
    )
    verify_bundle(target, payloads)
    # Exercise actual existing-output refusal; this must not replace or rewrite files.
    from sat_dengue.datasets.legacy_preparation.contract import PreparationError

    try:
        publish_bundle(OUTPUT, manifest["bundle_id"], payloads, existing_policy="error")
    except PreparationError as exc:
        require("already exists" in str(exc), "Unexpected publication refusal")
    else:
        raise ValueError("Existing-output refusal did not fire")
    verify_bundle(target, payloads)
    receipt = {
        "status": manifest["status"],
        "path": str(target),
        "bundle_id": manifest["bundle_id"],
        "manifest": fingerprint(target / "manifest.json"),
        "two_pass_payload_byte_equality": "PASS",
        "overwrite_refusal": "PASS",
        "historical_preservation": "PASS",
        "total_inference_calls": 32,
        "model_fits": 0,
        "calibrator_fits": 0,
        "threshold_selections": 0,
        "selection_scores": manifest["selection_scores"],
    }
    (WORK / "receipt.json").write_bytes(canonical_bytes(receipt))
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
