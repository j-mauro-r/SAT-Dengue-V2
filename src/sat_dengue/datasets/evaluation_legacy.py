"""Read-only fixed Stage 5 sources and original component identities; no reconstruction fits."""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import FrameType
from typing import Any, Literal

import pandas as pd  # type: ignore[import-untyped]
from kedro.io import DatasetError

from sat_dengue.datasets.legacy_evaluation.final_evaluation.protocol import (
    PROPOSAL_SHA,
    require_authorization,
)
from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
from sat_dengue.datasets.legacy_preparation.pipeline import prepare_inputs
from sat_dengue.datasets.legacy_training.contract import ModelTrainingConfig
from sat_dengue.datasets.legacy_training.events import load_event_context
from sat_dengue.datasets.legacy_training.loading import load_temporal_source, load_window_dataset
from sat_dengue.datasets.stage2 import identity, local_path, verified_json
from sat_dengue.datasets.training_legacy import no_fitting
from sat_dengue.final_evaluation.identities import ASSESSMENT, FINAL, NATIVE, STAGE5
from sat_dengue.model_training.candidate_families import ADAPTERS
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table


@contextmanager
def no_adjustment() -> Any:
    """Deny fitting and scientific selection calls, including aliases, for real replay."""
    if set(ADAPTERS) != {"xgboost", "lightgbm", "gam"}:
        raise DatasetError("Unknown frozen family adapters")
    with no_fitting() as audit:
        previous = sys.getprofile()

        def guard(
            frame: FrameType,
            event: Literal["call", "return", "c_call", "c_return", "c_exception"],
            arg: Any,
        ) -> None:
            if previous is not None:
                previous(frame, event, arg)
            if event == "call" and frame.f_code.co_name in {
                "_choose_calibration",
                "_select_threshold_from_grid",
                "_select_configuration_from_hyperparameter_role",
                "freeze_proposal",
                "select_calibrator",
                "select_threshold",
                "GridSearchCV",
                "RandomizedSearchCV",
            }:
                raise AssertionError(
                    "Forbidden selection on consumed evidence: " + frame.f_code.co_name
                )

        sys.setprofile(guard)
        try:
            yield audit
        finally:
            sys.setprofile(previous)


def checked_evaluation_bundle(relative: str) -> dict[str, Any]:
    """Check a pinned original manifest and exact native membership before any use."""
    if relative not in NATIVE:
        raise DatasetError("Unapproved frozen evaluation bundle")
    manifest = verified_json(relative + "/manifest.json", NATIVE[relative])
    folder = local_path(relative)
    if (
        folder.name != manifest["bundle_id"]
        or folder.is_symlink()
        or {p.name for p in folder.iterdir()} != {*manifest["files"], "manifest.json"}
    ):
        raise DatasetError("Frozen evaluation bundle identity/membership changed")
    for name, expected in manifest["files"].items():
        if Path(name).name != name or identity(folder / name) != expected:
            raise DatasetError("Frozen evaluation payload identity changed")
    return manifest


def table(folder: Path, name: str) -> pd.DataFrame:
    """Preserve full saved float values and stable municipal strings."""
    header = pd.read_csv(folder / name, nrows=0)
    return pd.read_csv(
        folder / name,
        float_precision="round_trip",
        dtype={col: "string" for col in ("municipality_code",) if col in header.columns},
    )


class FrozenEvaluationLoader:
    """Load only explicit saved evidence; every write belongs to a different adapter."""

    def load(self) -> dict[str, Any]:
        with no_adjustment():
            manifests = {p: checked_evaluation_bundle(p) for p in NATIVE}
            proposal_file = local_path(ASSESSMENT + "/freeze_proposal.json")
            if identity(proposal_file)["sha256"] != PROPOSAL_SHA:
                raise DatasetError("Exact frozen proposal identity changed")
            proposal = json.loads(proposal_file.read_text())
            final = manifests[FINAL]
            if proposal["identity_inputs"] != manifests[ASSESSMENT]["identity"] or (
                final["identity"]["proposal_sha256"] != PROPOSAL_SHA
                or final["identity"]["proposal_manifest"] != NATIVE[ASSESSMENT]
                or proposal["identity_inputs"]["input_manifest"] != NATIVE[STAGE5]
            ):
                raise DatasetError("Frozen proposal/source provenance changed")
            authorization = require_authorization(Path.cwd())
            if authorization != final["identity"]["authorization"]:
                raise DatasetError("Original frozen authorization changed")
            prepared = prepare_inputs(PreparationConfig(Path.cwd()))
            inputs = prepared.report["input_fingerprints"]
            if inputs != final["identity"]["inputs"]:
                raise DatasetError("Frozen source identity changed")
            folder = local_path(FINAL)
            components = {}
            for procedure in proposal["procedures"]:
                key = f"{procedure['candidate']}_t{procedure['horizon']}"
                retained = json.loads((folder / (key + "_retained_decisions.json")).read_text())
                if retained != procedure:
                    raise DatasetError("Frozen retained decisions/proposal disagree")
                for name, expected in procedure["provenance"].items():
                    if manifests[STAGE5]["files"].get(name) != expected:
                        raise DatasetError("Retained component lineage changed")
                components[key] = {
                    "model": (folder / (key + "_model.json")).read_bytes(),
                    "preparer": json.loads((folder / (key + "_preparer.json")).read_text()),
                    "training": json.loads(
                        (folder / (key + "_training_provenance.json")).read_text()
                    ),
                }
            source = load_temporal_source(ModelTrainingConfig(Path.cwd()))
            windows = {
                w: load_window_dataset(source, w)
                for w in json.loads(
                    local_path(
                        "docs/product/stage-4/model_engineering_contract_v1.json"
                    ).read_text()
                )["windows"]
            }
            stage5_folder = local_path(STAGE5)
            stage5_components = {
                n: (stage5_folder / n).read_bytes()
                for n in manifests[STAGE5]["files"]
                if n.endswith("_model.json")
            }
            return {
                "mode": "replay",
                "proposal": proposal,
                "panel": prepared.panel,
                "preparation_contract": prepared.contract,
                "components": components,
                "reference": {
                    n: table(folder, n)
                    for n in (
                        "predictions.csv",
                        "comparison.csv",
                        "metrics.csv",
                        "uncertainty.csv",
                        "t1_evaluation_index.csv",
                        "t2_evaluation_index.csv",
                        "t1_evaluation_context.csv",
                        "t2_evaluation_context.csv",
                        "t1_resampled_month_indices.csv",
                        "t2_resampled_month_indices.csv",
                    )
                },
                "development": {
                    "windows": windows,
                    "contexts": {
                        w: load_event_context(
                            ModelTrainingConfig(Path.cwd()),
                            source,
                            d.validation_index.reset_index(drop=True),
                            target_column=d.target_column,
                        )
                        for w, d in windows.items()
                    },
                    "models": stage5_components,
                    "preparers": {
                        n: json.loads((stage5_folder / n).read_text())
                        for n in manifests[STAGE5]["files"]
                        if n.endswith("_preparer.json")
                    },
                    "internals": {
                        f"{f}_{w}": table(stage5_folder, f"{f}_{w}_internal_predictions.csv")
                        for f in ("xgboost", "lightgbm", "gam")
                        for w in windows
                    },
                    "metadata": {
                        f"{f}_{w}": json.loads(
                            (stage5_folder / f"{f}_{w}_internal_components.json").read_text()
                        )
                        for f in ("xgboost", "lightgbm", "gam")
                        for w in windows
                    },
                    "tables": {
                        n: table(stage5_folder, n)
                        for n in (
                            "posterior_predictions.csv",
                            "development_predictions.csv",
                            "threshold_selection.csv",
                            "availability_transitions.csv",
                            "temporal_audit.csv",
                        )
                    },
                    "calibrators": json.loads((stage5_folder / "calibrators.json").read_text())[
                        "calibrators"
                    ],
                    "assessment": {
                        n: table(local_path(ASSESSMENT), n)
                        for n in (
                            "window_metrics.csv",
                            "comparison.csv",
                            "utility.csv",
                            "descriptive_uncertainty.csv",
                            "linked_development_predictions.csv",
                            "breakdown_metrics.csv",
                        )
                    },
                },
                "provenance": {
                    "native_manifest_documents": manifests,
                    "native_manifests": NATIVE,
                    "native_payloads": {p: m["files"] for p, m in manifests.items()},
                    "source_inputs": inputs,
                    "panel_fingerprint": bytes_record(serialize_table(prepared.panel)),
                    "proposal_sha256": PROPOSAL_SHA,
                    "original_code": {
                        p: m["identity"].get("code", {}) for p, m in manifests.items()
                    },
                    "original_authorization": authorization,
                    "real_model_fits": 0,
                    "real_preparer_refits": 0,
                    "calibrator_fits": 0,
                    "threshold_selection": 0,
                    "hyperparameter_search": 0,
                },
            }
