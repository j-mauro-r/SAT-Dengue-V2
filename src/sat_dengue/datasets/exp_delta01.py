"""Pinned, read-only DELTA inputs: no estimator loading or score reconstruction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from kedro.io import DatasetError

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.canonical import CanonicalBundleDataset, verify_records
from sat_dengue.datasets.exp_beta01 import BetaSourcesDataset
from sat_dengue.datasets.exp_beta01_v2 import _bundle
from sat_dengue.datasets.stage2 import identity, local_path, verified_json
from sat_dengue.experiments.academic_benchmark import (
    comparator_inputs,
    deterministic_alerts,
    read_predictions,
)
from sat_dengue.experiments.exp_beta01 import KEYS, role_parts
from sat_dengue.experiments.exp_beta01 import prepare as beta_prepare
from sat_dengue.experiments.exp_beta01_v2 import require_pair
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table

PROTOCOL = "docs/product/experiments/EXP-DELTA01/protocol.revision-2.json"
PROTOCOL_SHA = "2d1ab2a8d2686f85ca6809b26ec59b6113e8f8f322040f9d5f7c41c1ad6ff953"


def recovered_bundle(spec: dict[str, Any], records: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    root = local_path(spec["path"])
    fp = identity(root / "manifest.json")
    if fp["sha256"] != spec["manifest_sha256"]:
        raise DatasetError("Recovered selection manifest changed")
    manifest = json.loads((root / "manifest.json").read_bytes())
    body = {k: v for k, v in manifest.items() if k != "bundle_id"}
    if (
        bytes_record(canonical_bytes(body))["sha256"] != root.name
        or manifest["bundle_id"] != root.name
        or root.is_symlink()
        or {p.name for p in root.iterdir()} != {*manifest["files"], "manifest.json"}
        or manifest["status"] != "RECOVERY_VERIFIED"
        or manifest["cells"] != 8
        or manifest["selection_scores"] != 4386
    ):
        raise DatasetError("Invalid complete recovery publication")
    records[str((root / "manifest.json").relative_to(Path.cwd()))] = fp
    for name, expected in manifest["files"].items():
        if Path(name).name != name or (root / name).is_symlink():
            raise DatasetError("Unsafe recovered payload")
        records[f"{spec['path']}/{name}"] = expected
    verify_records(records)
    return root, manifest


class DeltaSourcesDataset(BetaSourcesDataset):
    """Verify existing sources and exact cell memberships without model inference."""

    def load(self) -> dict[str, Any]:
        protocol = verified_json(
            PROTOCOL, {**identity(local_path(PROTOCOL)), "sha256": PROTOCOL_SHA}
        )
        records = {PROTOCOL: identity(local_path(PROTOCOL))}
        for spec in protocol["revision_lineage"].values():
            if isinstance(spec, dict) and "path" in spec:
                if identity(local_path(spec["path"]))["sha256"] != spec["sha256"]:
                    raise DatasetError("Revision authority identity changed")
                records[spec["path"]] = identity(local_path(spec["path"]))
        original = super().load()
        records.update(original["provenance"]["sources"])
        regional = beta_prepare(original, {"profile": "exp_beta01", "tracking": "disabled"})
        source_specs = protocol["sources"]
        for name in ("G0", "canonical", "benchmark"):
            _bundle(source_specs[name]["path"], source_specs[name]["manifest_sha256"], records)
        recovery, manifest = recovered_bundle(source_specs["G0_OFF_selection"], records)
        for name in ("G0", "canonical", "benchmark"):
            if manifest["sources"][name] != source_specs[name]:
                raise DatasetError("Recovery parent source mismatch")
        g0 = local_path(source_specs["G0"]["path"])
        native_cells = json.loads((g0 / "cells.json").read_bytes())["cells"]
        g0_manifest = json.loads((g0 / "manifest.json").read_bytes())
        frozen_g0 = read_predictions(g0 / "predictions.csv")
        p0_policies = json.loads((g0 / "policies.json").read_bytes())["policies"]
        recovery_cells = json.loads((recovery / "cells.json").read_bytes())["cells"]
        reproduction = json.loads((recovery / "evaluation_reproduction.json").read_bytes())["cells"]
        if (
            len(recovery_cells) != 8
            or len(reproduction) != 8
            or any(
                a["status"] != "PASS" or a["exceeding_tolerance"] or a["frozen_alert_discrepancies"]
                for a in reproduction
            )
        ):
            raise DatasetError("Recovery reproduction incomplete or failed")
        published = pd.read_csv(
            local_path(source_specs["benchmark"]["path"] + "/predictions.csv"),
            dtype={"municipality_code": str, "department_code": str, "alert": str},
            float_precision="round_trip",
        )
        published["alert"] = published.alert.map({"True": True, "False": False})
        if published.alert.isna().any():
            raise DatasetError("Invalid benchmark alert tokens")
        table = original["table"].loc[original["table"].year_month.lt("2025-01")]
        cells = []
        for recovered in recovery_cells:
            h, year = recovered["horizon"], recovered["evaluation_year"]
            native = next(
                c
                for c in native_cells
                if (c["horizon"], c["year"], c["climate"]) == (h, year, "OFF")
            )
            partition = role_parts(regional["cohorts"][h], year, original["protocol"])
            if partition["audit"] != native["role_audit"]:
                raise DatasetError("Original role/embargo mismatch")
            if (
                recovered["model_identity"] != g0_manifest["files"][native["model_file"]]
                or recovered["calibrator"]["offset"] != native["global_offset"]
                or bytes_record(canonical_bytes(recovered["calibrator"]))["sha256"]
                != recovered["calibrator_sha256"]
            ):
                raise DatasetError("Original predictor/calibrator binding mismatch")
            parts = partition["parts"]
            selection = pd.read_csv(
                recovery / recovered["selection_file"],
                dtype={"municipality_code": str, "department_code": str},
                float_precision="round_trip",
            ).rename(columns={"onset_target": "truth"})
            require_pair(
                parts["selection"].rename(columns={"onset_target": "truth"}),
                selection,
                [*KEYS, "department_code", "target_month", "truth"],
            )
            for role, frame in parts.items():
                if (
                    bytes_record(serialize_table(frame[KEYS])) != recovered["roles"][role]["keys"]
                    or bytes_record(serialize_table(frame[[*KEYS, "target_month", "onset_target"]]))
                    != recovered["roles"][role]["keys_targets_labels"]
                ):
                    raise DatasetError("Recovered role membership/labels changed")
            keys = set(map(tuple, selection[KEYS].to_records(index=False).tolist()))
            for role in ("train", "calibration", "adaptation", "evaluation"):
                if keys & set(map(tuple, parts[role][KEYS].to_records(index=False).tolist())):
                    raise DatasetError("Selection leakage into another role")
            inputs = comparator_inputs(table, selection, h)
            selection = selection.merge(inputs, on=KEYS, validate="one_to_one")
            channel, _ = deterministic_alerts(selection, h)
            selection["channel_alert"] = channel
            evaluation = published.loc[
                published.horizon.eq(h) & published.year.eq(year) & published.arm.eq("G0_OFF")
            ].copy()
            frozen = frozen_g0.loc[
                frozen_g0.horizon.eq(h)
                & frozen_g0.year.eq(year)
                & frozen_g0.arm.eq("G0")
                & frozen_g0.climate.eq("OFF")
            ]
            require_pair(frozen, evaluation, [*KEYS, "target_month", "truth", "score", "alert"])
            p0_policy = next(
                p
                for p in p0_policies
                if (p["horizon"], p["year"], p["climate"], p["arm"]) == (h, year, "OFF", "G0")
            )
            expected_alert = (
                evaluation.score.ge(p0_policy["threshold"])
                if p0_policy["threshold"] is not None
                else pd.Series(False, index=evaluation.index)
            )
            if not evaluation.alert.eq(expected_alert).all():
                raise DatasetError("Original P0 alert/threshold mismatch")
            require_pair(
                parts["evaluation"].rename(columns={"onset_target": "truth"}),
                evaluation,
                [*KEYS, "target_month", "department_code", "truth"],
            )
            for name, output in (
                ("CHANNEL", "channel_alert"),
                ("PERSISTENCE", "persistence_alert"),
            ):
                other = published.loc[
                    published.horizon.eq(h) & published.year.eq(year) & published.arm.eq(name)
                ]
                require_pair(evaluation, other, [*KEYS, "truth", "target_excess"])
                evaluation = evaluation.sort_values(KEYS).reset_index(drop=True)
                evaluation[output] = other.sort_values(KEYS).alert.to_numpy(dtype=bool)
            for frame in (selection, evaluation):
                if not np.isfinite(frame.score).all() or not frame.score.between(0, 1).all():
                    raise DatasetError("Invalid admitted probabilities")
            cells.append(
                {
                    "horizon": h,
                    "year": year,
                    "selection": selection,
                    "evaluation": evaluation,
                    "model_identity": recovered["model_identity"],
                    "calibrator_sha256": recovered["calibrator_sha256"],
                }
            )
        execution = original["provenance"]["execution"]
        paths = [
            Path("src/sat_dengue/datasets/exp_delta01.py"),
            Path("src/sat_dengue/experiments/exp_delta01.py"),
            Path("src/sat_dengue/experiments/academic_benchmark.py"),
            *Path("src/sat_dengue/pipelines/exp_delta01").glob("*.py"),
        ]
        execution["code"].update({str(p): identity(p) for p in paths})
        verify_records(records)
        return {
            "protocol": protocol,
            "cells": cells,
            "evidence_type": "authorized_retrospective",
            "provenance": {"sources": records, "execution": execution},
            "freeze_root": "data/processed/exp_delta01/selection_freezes",
        }


class DeltaBundleDataset(CanonicalBundleDataset):
    """Existing atomic publisher, isolated DELTA results namespace."""
