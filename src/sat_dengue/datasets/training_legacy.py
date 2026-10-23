"""One explicit read-only native-component loader; no module-name monkeypatching."""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import FrameType
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from kedro.io import DatasetError

from sat_dengue.configuration import AUTHORITIES
from sat_dengue.datasets.legacy_training.contract import ModelTrainingConfig
from sat_dengue.datasets.legacy_training.events import load_event_context
from sat_dengue.datasets.legacy_training.loading import load_temporal_source, load_window_dataset
from sat_dengue.datasets.preparation import SavedPreparersDataset
from sat_dengue.datasets.stage2 import identity, local_path, verified_json
from sat_dengue.model_training.contract import ModelTrainingError
from scripts.final_evaluation.cohorts import load_cohorts
from scripts.final_evaluation.protocol import PROPOSAL_BUNDLE, PROPOSAL_SHA

BUNDLES: dict[str, dict[str, Any]] = {
    (
        "artifacts/model_final_evaluation/"
        "768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35"
    ): {
        "bytes": 9956,
        "sha256": "5a526fa996112c86b014c533260f234b94c7c31bbcf47fa465fd61480c9b768f",
    },
    ("artifacts/model_training/0ab9ae6666a420802554f72756f1dab4e848ec1d6714954662763e77aa380bb8"): {
        "bytes": 8675,
        "sha256": "29c06b553a08d46388e6b30e234339a014b6f5c1b0510423197d4058f3bd4dd4",
    },
    (
        "artifacts/model_training/candidate_suite/"
        "592c3e555ab9e6c2c1249311c6f22226d43f691bfee94f4af81602eb6ad96e25"
    ): {
        "bytes": 2837,
        "sha256": "b134b696dc66d1d060a209fb55bdadf876aa338bb91b02a890209ac58c5ce365",
    },
    (
        "artifacts/model_training/gam/full/"
        "19288825e94ed9feaa6bdbdce6d2ecb07d1332ec9888083dd61d2988daf585f2"
    ): {
        "bytes": 16284,
        "sha256": "278f2986608eccbb4783ddaefb236dd3b3ccebc74cfc9cff4e38d3b5387264eb",
    },
    (
        "artifacts/model_training/lightgbm/full/"
        "4c2db880d3f94cd44ff9c564e032e4a8af66a9b8c5deba5a59b8f0baeb6a0c35"
    ): {
        "bytes": 16182,
        "sha256": "5278eda2abd42575ce074dd2eca4b1f70ad88e7bd24cc229d375ab3ef44f4a9c",
    },
    (
        "artifacts/model_training/xgboost/full/"
        "96d7ecd7dc4ffebf28f7e0e425c7b44513d221bcd037af9aa52cb3cdd3d599a8"
    ): {
        "bytes": 16534,
        "sha256": "c60a1f86f77f15548ee8deb0e50f08767229025f7ada54b590521fbaaa7d4099",
    },
    (
        "artifacts/model_training/xgboost/without_climate/"
        "d3c43df69fe106221b2a4da72a14220f98532f5e4c40b8e9ebdbb9b100734fa2"
    ): {
        "bytes": 17082,
        "sha256": "bc999e8c72e8b0a66b00afdbfdcc77773ce501ab7e9c6f1068d2acbbfd989713",
    },
    (
        "artifacts/model_training/xgboost/without_zones/"
        "b08e4fd027a2dc8541dec6eb5ab0e9ccb93cea4b102f7dfdbee902d1693da66c"
    ): {
        "bytes": 16661,
        "sha256": "88b2920429dcf2be0496c6177a0777c8cb8dba585d2f3382d55d463121b4d597",
    },
}
REFERENCE = (
    "artifacts/model_training/0ab9ae6666a420802554f72756f1dab4e848ec1d6714954662763e77aa380bb8"
)
SUITE = (
    "artifacts/model_training/candidate_suite/"
    "592c3e555ab9e6c2c1249311c6f22226d43f691bfee94f4af81602eb6ad96e25"
)
FINAL = (
    "artifacts/model_final_evaluation/"
    "768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35"
)
EXPERIMENTS: dict[str, str] = {
    "gam": (
        "artifacts/model_training/gam/full/"
        "19288825e94ed9feaa6bdbdce6d2ecb07d1332ec9888083dd61d2988daf585f2"
    ),
    "lightgbm": (
        "artifacts/model_training/lightgbm/full/"
        "4c2db880d3f94cd44ff9c564e032e4a8af66a9b8c5deba5a59b8f0baeb6a0c35"
    ),
    "xgboost": (
        "artifacts/model_training/xgboost/full/"
        "96d7ecd7dc4ffebf28f7e0e425c7b44513d221bcd037af9aa52cb3cdd3d599a8"
    ),
    "xgboost_without_climate": (
        "artifacts/model_training/xgboost/without_climate/"
        "d3c43df69fe106221b2a4da72a14220f98532f5e4c40b8e9ebdbb9b100734fa2"
    ),
    "xgboost_without_zones": (
        "artifacts/model_training/xgboost/without_zones/"
        "b08e4fd027a2dc8541dec6eb5ab0e9ccb93cea4b102f7dfdbee902d1693da66c"
    ),
}


@contextmanager
def no_fitting() -> Any:
    """Deny aliases, estimator/preparer fits and search dispatch; restore caller profiling."""
    previous = sys.getprofile()
    audit = {"real_model_fits": 0, "real_preparer_refits": 0, "search_calls": 0}

    def guard(frame: FrameType, event: str, arg: Any) -> None:
        if event == "call":
            name = frame.f_code.co_name
            if name.startswith(("fit", "_fit")) or name in {
                "train",
                "select_and_fit",
                "select_threshold",
                "_select_threshold",
                "GridSearchCV",
                "RandomizedSearchCV",
            }:
                raise AssertionError("Forbidden fitting/search during frozen replay: " + name)

    sys.setprofile(guard)
    try:
        yield audit
    finally:
        sys.setprofile(previous)


def checked_bundle(relative: str) -> dict[str, Any]:
    manifest = verified_json(relative + "/manifest.json", BUNDLES[relative])
    folder = local_path(relative)
    if folder.is_symlink() or folder.name != manifest["bundle_id"]:
        raise DatasetError("Native model bundle identity changed")
    if {p.name for p in folder.iterdir()} != {*manifest["files"], "manifest.json"}:
        raise DatasetError("Native model bundle membership changed")
    for name, expected in manifest["files"].items():
        if Path(name).name != name or identity(folder / name) != expected:
            raise DatasetError("Native model payload identity changed")
    return manifest


class LegacyTrainingLoader:
    """Read fixed JSON/native models with explicit identities; no pickle import aliases."""

    def load(self) -> dict[str, Any]:
        with no_fitting():
            return self._load()

    def _load(self) -> dict[str, Any]:
        manifests = {p: checked_bundle(p) for p in BUNDLES}
        SavedPreparersDataset().load()
        config = ModelTrainingConfig(Path.cwd())
        source = load_temporal_source(config)
        stage4 = json.loads(config.resolve(config.contract_path).read_text())
        development = {}
        for window in stage4["windows"]:
            dataset = load_window_dataset(source, window)
            development[window] = {
                "dataset": dataset,
                "context": load_event_context(
                    config, source, dataset.validation_index, target_column=dataset.target_column
                ),
            }
        components = {}
        for name, relative in EXPERIMENTS.items():
            manifest = manifests[relative]
            folder = local_path(relative)
            family = manifest["identity"]["family"]
            if manifest["identity"]["experiment"] != name or set(manifest["windows"]) != set(
                stage4["windows"]
            ):
                raise DatasetError("Unknown family/experiment/cohort identity")
            components[name] = {
                "family": family,
                "predictions": pd.read_csv(
                    folder / "predictions.csv", float_precision="round_trip"
                ),
                "metrics": pd.read_csv(folder / "metrics.csv", float_precision="round_trip"),
                "windows": {
                    window: {
                        "model": (folder / f"{window}_model.json").read_bytes(),
                        "preparer": json.loads((folder / f"{window}_preparer.json").read_text()),
                    }
                    for window in stage4["windows"]
                },
            }
        # Existing frozen cohort construction is an I/O compatibility consumer only.
        # This task does not migrate final evaluation, calibration or thresholds.
        proposal_path = local_path(str(PROPOSAL_BUNDLE) + "/freeze_proposal.json")
        if identity(proposal_path)["sha256"] != PROPOSAL_SHA:
            raise DatasetError("Frozen proposal identity changed")
        proposal = json.loads(proposal_path.read_text())
        cohorts, inputs = load_cohorts(Path.cwd(), proposal)
        if inputs != manifests[FINAL]["identity"]["inputs"]:
            raise DatasetError("Frozen component input identity changed")
        folder = local_path(FINAL)
        frozen = {
            "cohorts": {h: {"X": c.X, "keys": c.index, "y": c.y} for h, c in cohorts.items()},
            "components": {
                f"{family}_t{h}": {
                    "model": (folder / f"{family}_t{h}_model.json").read_bytes(),
                    "preparer": json.loads((folder / f"{family}_t{h}_preparer.json").read_text()),
                }
                for family in ("xgboost", "lightgbm", "gam")
                for h in (1, 2)
            },
            "predictions": pd.read_csv(
                folder / "predictions.csv",
                dtype={"municipality_code": "string"},
                float_precision="round_trip",
            ),
        }
        reference_folder = local_path(REFERENCE)
        return {
            "development": development,
            "components": components,
            "frozen": frozen,
            "reference_predictions": pd.read_csv(
                reference_folder / "predictions.csv", float_precision="round_trip"
            ),
            "reference_metrics": pd.read_csv(
                reference_folder / "metrics.csv", float_precision="round_trip"
            ),
            "provenance": {
                "native_manifests": BUNDLES,
                "native_payloads": {p: m["files"] for p, m in manifests.items()},
                "stage2_inputs": inputs,
                "stage3_manifest": identity(source.bundle / "manifest.json"),
                "proposal": identity(proposal_path),
                "G5": "NOT_APPROVED",
                "champion": "not_selected",
                "real_model_fits": 0,
                "real_preparer_refits": 0,
            },
        }

    @staticmethod
    def legacy_result(
        config: ModelTrainingConfig,
        family: str | None = None,
        ablation: str | None = None,
        suite: bool = False,
    ) -> Any:
        from sat_dengue.datasets.legacy_training.pipeline import ModelTrainingResult

        default = ModelTrainingConfig(Path.cwd())
        if (
            config.root.resolve() != default.root
            or config.contract_path != default.contract_path
            or config.stage3_contract_path != default.stage3_contract_path
            or family not in (None, "xgboost", "lightgbm", "gam")
            or (
                ablation is not None
                and (family != "xgboost" or ablation not in ("without_climate", "without_zones"))
            )
            or (suite and (family is not None or ablation is not None))
        ):
            raise ModelTrainingError("Unknown legacy training configuration/family/selection")
        for name in ("training_preparation_contract_v1", "model_engineering_contract_v1"):
            authority = AUTHORITIES[name]
            if identity(local_path(authority["path"]))["sha256"] != authority["sha256"]:
                raise ModelTrainingError("Legacy scientific authority identity changed")
        relative = (
            SUITE
            if suite
            else EXPERIMENTS[f"xgboost_{ablation}" if ablation else family]
            if family
            else REFERENCE
        )
        return ModelTrainingResult(local_path(relative), checked_bundle(relative))
