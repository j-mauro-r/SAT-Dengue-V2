"""Explicit producer/consumer bridges; native parity precedes real-stage reuse."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sat_dengue.datasets.replay_identity import CACHED, stage_inputs, verify_publication
from sat_dengue.datasets.stage2 import identity, local_path


def data_inputs(context: dict[str, Any]) -> tuple[Any, ...]:
    inputs = stage_inputs(context, "data")
    params = {"profile": "data", "tracking": context["operational"]["tracking"]}
    if "data" in context["cache"]:
        return inputs, params, CACHED, CACHED, CACHED
    if context["mode"] == "synthetic":
        from .replay_synthetic import stage2_fixture

        sources, epi, climate = stage2_fixture()
    else:
        from .stage2 import Stage2RawCsvDataset, Stage2SourcesDataset

        sources = Stage2SourcesDataset().load()
        epi = Stage2RawCsvDataset(
            ["data/raw/dengue.csv", "data/raw/dengue_grave.csv"], 200000, True
        ).load()
        climate = Stage2RawCsvDataset(["data/raw/google_earth_engine.csv"], 250000).load()
    return inputs, params, sources, epi, climate


def data_parity(record: dict[str, Any]) -> None:
    from .stage2 import NATIVE_MANIFEST

    manifest = json.loads(local_path(NATIVE_MANIFEST).read_text())
    folder = local_path(record["path"])
    roles = {
        "panel.csv": "panel_mensual_dengue_clima",
        "y_history.csv": "y_label_history_traceability",
        "channel_history.csv": "current_endemic_channel_traceability",
    }
    for name, role in roles.items():
        expected = {k: manifest["outputs"][role][k] for k in ("bytes", "sha256")}
        if identity(folder / name) != expected:
            raise ValueError("Complete Stage2 output parity failed: " + name)
    expected = {k: manifest["outputs"]["dengue_y_dengue_grave"][k] for k in ("bytes", "sha256")}
    if identity(local_path(record["manifest"]["consolidated"]["path"])) != expected:
        raise ValueError("Complete consolidated parity failed")


def preparation_inputs(context: dict[str, Any], data: dict[str, Any]) -> tuple[Any, ...]:
    verify_publication(data, context)
    if context["mode"] == "replay":
        data_parity(data)
    inputs = stage_inputs(context, "preparation")
    params = {"profile": "preparation", "tracking": context["operational"]["tracking"]}
    if "preparation" in context["cache"]:
        return inputs, params, CACHED, CACHED
    from sat_dengue.training_preparation.eligibility import policy_from_years

    from .legacy_preparation.pipeline import read_panel
    from .legacy_readiness import read_notification_year_metadata

    contract = inputs["authorities"]["training_preparation_contract_v1"]["document"]
    folder = local_path(data["path"])
    panel = (
        read_panel(folder / "panel.csv", contract, reference_end="2024-12")
        .sort_values(["municipality_code", "year_month"])
        .reset_index(drop=True)
    )
    years = read_notification_year_metadata(local_path(data["manifest"]["consolidated"]["path"]))
    provenance = {
        str((folder / n).relative_to(Path.cwd())): identity(folder / n)
        for n in ("panel.csv", "y_history.csv", "channel_history.csv", "construction.json")
    }
    sources = {
        "panel": panel,
        "contract": contract,
        "policy": policy_from_years(int(years["min_year"]), int(years["max_year"]), "2025-01"),
        "provenance": provenance,
    }
    if context["mode"] == "replay":
        from .preparation import SavedPreparersDataset

        saved = SavedPreparersDataset().load()
    else:
        from .replay_synthetic import fit_fixture_preparers

        saved = fit_fixture_preparers(inputs, sources, params["tracking"])
    return inputs, params, sources, saved


def preparation_parity(record: dict[str, Any]) -> None:
    from .preparation import DEVELOPMENT, NATIVE_PREPARATION, TEMPORAL, verified_native_bundle

    folder = local_path(record["path"])
    for relative in (DEVELOPMENT, TEMPORAL):
        native = verified_native_bundle(relative, NATIVE_PREPARATION[relative])
        for name, expected in native["files"].items():
            if name in {"provenance.json", "manifest.json"}:
                continue
            if identity(folder / name) != expected:
                raise ValueError("Complete preparation parity failed: " + name)


def training_inputs(context: dict[str, Any], preparation: dict[str, Any]) -> tuple[Any, ...]:
    verify_publication(preparation, context)
    if context["mode"] == "replay":
        preparation_parity(preparation)
    inputs = stage_inputs(context, "training")
    mode = context["mode"]
    params = {"profile": "training_" + mode, "tracking": context["operational"]["tracking"]}
    if mode == "synthetic":
        return inputs, params
    if "training" in context["cache"]:
        return inputs, params, CACHED
    from .training import TrainingSourcesDataset

    sources = TrainingSourcesDataset().load()
    return inputs, params, sources


def evaluation_inputs(context: dict[str, Any], training: dict[str, Any]) -> tuple[Any, ...]:
    verify_publication(training, context)
    inputs = stage_inputs(context, "evaluation")
    params = {
        "profile": "evaluation_" + context["mode"],
        "tracking": context["operational"]["tracking"],
    }
    if "evaluation" in context["cache"]:
        return inputs, params, CACHED
    if context["mode"] == "replay":
        from .evaluation import FrozenEvaluationSourcesDataset
        from .replay_parity import training_parity

        training_parity(training)
        sources = FrozenEvaluationSourcesDataset().load()
    else:
        from sat_dengue.final_evaluation.synthetic import synthetic_sources

        sources = synthetic_sources(inputs["authorities"])
        folder = local_path(training["path"])
        sources["e2e_components"] = {
            family: {
                "model": (folder / (family + "_model.json")).read_bytes(),
                "preparer": json.loads((folder / (family + "_preparer.json")).read_text()),
            }
            for family in ("xgboost", "lightgbm", "gam")
        }
    return inputs, params, sources
