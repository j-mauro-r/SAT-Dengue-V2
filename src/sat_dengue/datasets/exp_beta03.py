"""Explicit frozen native R0 development scores and isolated policy publication."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kedro.io import DatasetError

from sat_dengue.datasets.canonical import CanonicalBundleDataset, verify_records
from sat_dengue.datasets.exp_beta01 import BetaSourcesDataset
from sat_dengue.datasets.stage2 import identity, local_path, verified_json

PROTOCOL_PATH = "docs/product/experiments/EXP-BETA03/protocol.json"
PROTOCOL_SHA256 = "0b8b5f22ef678039147fd55dafd7938d70de6333c85afe631a31c3e8386ee386"


class PolicySourcesDataset(BetaSourcesDataset):
    """No search, training, recalibration, or optional reference fallback."""

    def load(self) -> dict[str, Any]:
        from sat_dengue.experiments.exp03_1_reporting import _restore_frame, read_real_bundle
        from sat_dengue.experiments.exp03_persistence import load_cell

        fp = identity(local_path(PROTOCOL_PATH))
        if fp["sha256"] != PROTOCOL_SHA256:
            raise DatasetError("Unapproved Beta03 protocol identity")
        protocol = verified_json(PROTOCOL_PATH, fp)
        source = super().load()
        folder = local_path(protocol["reference_path"])
        if identity(folder / "manifest.json")["sha256"] != protocol["reference_manifest_sha256"]:
            raise DatasetError("Incorrect mandatory native R0 manifest")
        publication = read_real_bundle(folder, protocol["reference_bundle_id"])
        records = source["provenance"]["sources"]
        records[PROTOCOL_PATH] = fp
        # Native reader verifies full membership, hashes, zero-fit score replay and
        # exact evaluation linkage. Keep the same transitive identities at publish.
        replay = publication["replay"]
        records[str((folder / "replay/manifest.json").relative_to(Path.cwd()))] = identity(
            folder / "replay/manifest.json"
        )
        records.update(
            {f"{protocol['reference_path']}/replay/{n}": v for n, v in replay["files"].items()}
        )
        cells = []
        for summary in publication["bundle"]["cells"]:
            if (summary["variant"], summary["family"], summary["objective"]) != (
                "M00",
                "xgboost",
                "onset",
            ):
                continue
            native = load_cell(folder / "replay" / summary["cell_id"])
            frames = {
                role: _restore_frame(spec["frame"])
                for role, spec in native.metadata["roles"].items()
            }
            cells.append(
                {
                    "cell_id": native.cell_id,
                    "horizon": summary["horizon"],
                    "year": int(native.metadata["window"]["evaluation"][0][:4]),
                    "window": native.metadata["window"],
                    "parts": frames,
                    "reference_threshold": native.threshold,
                    "reference_selection": native.metadata["threshold_selection"],
                }
            )
        execution = source["provenance"]["execution"]
        paths = [
            Path("src/sat_dengue/datasets/exp_beta03.py"),
            Path("src/sat_dengue/experiments/exp_beta03.py"),
            *Path("src/sat_dengue/pipelines/exp_beta03").glob("*.py"),
            *Path("src/sat_dengue/experiments").glob("exp03*.py"),
        ]
        execution["code"].update({str(p): identity(p) for p in paths})
        verify_records(records)
        return {
            **source,
            "canonical_protocol": source["protocol"],
            "protocol": protocol,
            "cells": cells,
            "native_replay": {"cells": len(replay["cells"]), "fits": 0},
        }

    def _describe(self) -> dict[str, Any]:
        return {"protocol": PROTOCOL_PATH, "sha256": PROTOCOL_SHA256, "fits": 0}


class PolicyBundleDataset(CanonicalBundleDataset):
    """Reuse atomic no-overwrite publication in the separate policy namespace."""
