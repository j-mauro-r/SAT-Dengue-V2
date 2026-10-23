"""Explicit execution identities and immutable verified checkpoints for composed replay."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sat_dengue.configuration import canonical_bytes, resolve_configuration
from sat_dengue.datasets.stage2 import identity, local_path
from sat_dengue.datasets.training import require_modeling

CACHED = {"replay_cached": True}
STAGES = ("data", "preparation", "training", "evaluation")
SCHEMAS = {
    "data": "sat-dengue-stage2-engineering-v1",
    "preparation": "sat-dengue-preparation-engineering-v1",
    "training": "sat-dengue-training-engineering-v1",
    "evaluation": "sat-dengue-evaluation-engineering-v1",
}


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def storage() -> Path:
    value = os.environ.get("SAT_DENGUE_REPLAY_ROOT", "tmp/kedro-migration/replay-runs")
    path = Path(value)
    if (
        path.is_absolute()
        or not value.startswith("tmp/")
        or ".." in path.parts
        or any(p.is_symlink() for p in (path, *path.parents))
        or not path.resolve().is_relative_to(Path.cwd().resolve() / "tmp")
    ):
        raise ValueError("Replay storage must be ignored repository-local tmp")
    if subprocess.run(
        ["git", "check-ignore", "-q", "--", str(path / "probe")], capture_output=True
    ).returncode:
        raise ValueError("Replay storage must be ignored by Git")
    return path


def immutable_json(path: Path, value: dict[str, Any]) -> None:
    payload = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != payload:
            raise ValueError("Immutable execution/checkpoint changed")
        return
    temporary = path.with_name("." + path.name + "-" + os.urandom(8).hex())
    try:
        with temporary.open("xb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
            os.fchmod(f.fileno(), 0o444)
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def native_inputs() -> dict[str, Any]:
    """Verify every pinned source and native payload without importing a fitter."""
    from sat_dengue.datasets.evaluation_legacy import NATIVE, checked_evaluation_bundle
    from sat_dengue.datasets.preparation import NATIVE_PREPARATION, verified_native_bundle
    from sat_dengue.datasets.stage2 import NATIVE_IDENTITIES, SOURCE_IDENTITIES
    from sat_dengue.datasets.training_legacy import BUNDLES, checked_bundle

    result: dict[str, Any] = {}
    for name, expected in {**SOURCE_IDENTITIES, **NATIVE_IDENTITIES}.items():
        if identity(local_path(name)) != expected:
            raise ValueError("Replay source identity changed")
        result[name] = expected
    for records, verifier in (
        (NATIVE_PREPARATION, None),
        (BUNDLES, checked_bundle),
        (NATIVE, checked_evaluation_bundle),
    ):
        for name, expected in records.items():
            manifest = (
                verified_native_bundle(name, expected) if verifier is None else verifier(name)
            )
            result[name] = {"manifest": expected, "files": manifest["files"]}
    return result


def verify_publication(
    record: dict[str, Any], context: dict[str, Any] | None = None
) -> dict[str, Any]:
    if (
        set(record) != {"path", "manifest", "stage", "context_sha256"}
        or record["stage"] not in STAGES
    ):
        raise ValueError("Incomplete replay intermediate identity")
    relative = record["path"]
    folder = Path(relative)
    if (
        folder.is_absolute()
        or not relative.startswith("tmp/")
        or ".." in folder.parts
        or any(p.is_symlink() for p in (folder, *folder.parents))
        or not folder.resolve().is_relative_to(Path.cwd().resolve() / "tmp")
    ):
        raise ValueError("Unsafe replay intermediate path")
    if context is not None and record["context_sha256"] != context["identity"]:
        raise ValueError("Stale intermediate code/configuration/input identity")
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest != record["manifest"] or manifest["schema"] != SCHEMAS[record["stage"]]:
        raise ValueError("Replay intermediate schema/manifest changed")
    if digest({k: v for k, v in manifest.items() if k != "bundle_id"}) != manifest["bundle_id"]:
        raise ValueError("Replay intermediate identity changed")
    if set(p.name for p in folder.iterdir()) != {*manifest["files"], "manifest.json"}:
        raise ValueError("Replay intermediate membership changed")
    for name, expected in manifest["files"].items():
        if Path(name).name != name or identity(folder / name) != expected:
            raise ValueError("Replay intermediate payload changed")
    if context is not None:
        stage = record["stage"]
        run_id = hashlib.sha256((context["identity"] + stage).encode()).hexdigest()[:32]
        snapshot = (
            local_path(context["folder"]) / "configuration" / stage / run_id / "resolved.json"
        )
        if any(p.is_symlink() for p in (snapshot, *snapshot.parents)):
            raise ValueError("Unsafe replay configuration path")
        expected_folder = local_path(context["folder"]) / "stages" / stage
        expected_folder = (
            expected_folder / run_id / "bundle"
            if stage == "data"
            else expected_folder / manifest["bundle_id"]
        )
        if folder.resolve() != expected_folder.resolve():
            raise ValueError("Replay intermediate belongs to a different execution path")
        identity(snapshot)
        resolved = json.loads(snapshot.read_text())
        body = {k: v for k, v in resolved.items() if k != "configuration_sha256"}
        if (
            digest(body) != manifest["configuration_sha256"]
            or resolved["configuration_sha256"] != manifest["configuration_sha256"]
            or resolved["execution"]["e2e"]
            != {
                "identity": context["identity"],
                "folder": context["folder"],
                "mode": context["mode"],
                "stage": stage,
            }
            or resolved["execution"]["run_id"] != run_id
        ):
            raise ValueError("Replay intermediate configuration binding changed")
        if "inputs" in context:
            if (
                resolved["authorities"] != context["inputs"]["authorities"]
                or resolved["execution"] != stage_inputs(context, stage)["execution"]
                or resolved["operational"]
                != {
                    "profile": {
                        "data": "data",
                        "preparation": "preparation",
                        "training": "training_" + context["mode"],
                        "evaluation": "evaluation_" + context["mode"],
                    }[stage],
                    "tracking": context["operational"]["tracking"],
                }
            ):
                raise ValueError("Replay intermediate execution/configuration changed")
    if record["stage"] == "data":
        consolidated = manifest["consolidated"]
        expected = {k: v for k, v in consolidated.items() if k != "path"}
        if identity(local_path(consolidated["path"])) != expected:
            raise ValueError("Replay consolidated input changed")
    elif manifest.get("real_model_fits") != 0 or manifest.get("real_preparer_refits") != 0:
        raise ValueError("Real fits/refits forbidden in replay")
    return record


def open_execution(
    inputs: dict[str, Any], parameters: dict[str, Any], *, mode: str
) -> dict[str, Any]:
    require_modeling()
    # Initialize optional library modules before applying call-level replay guards.
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation import workflow as _evaluation

    del _evaluation
    if parameters["profile"] not in {"foundation", "replay", "replay_synthetic"} or mode not in {
        "replay",
        "synthetic",
    }:
        raise ValueError("Unknown E2E operational profile")
    if parameters["profile"] not in {
        "foundation",
        "replay" if mode == "replay" else "replay_synthetic",
    }:
        raise ValueError("E2E pipeline/profile mismatch")
    # Retained script facades are executable dependencies of the native loaders.
    # Hash them as code too: a dirty Boolean cannot identify an adapter change.
    adapters = sorted(Path.cwd().joinpath("scripts").rglob("*.py"))
    if (
        not adapters
        or Path("scripts").is_symlink()
        or any(p.is_symlink() for p in Path("scripts").rglob("*"))
    ):
        raise ValueError("Retained adapter code inventory is missing or symlinked")
    execution = {
        **inputs["execution"],
        "code": {
            **inputs["execution"]["code"],
            **{str(p.relative_to(Path.cwd())): identity(p)["sha256"] for p in adapters},
        },
    }
    inputs = {**inputs, "execution": execution}
    resolved = resolve_configuration(
        inputs,
        {
            "profile": "replay" if mode == "replay" else "replay_synthetic",
            "tracking": parameters["tracking"],
        },
    )
    with no_adjustment():
        sources = (
            native_inputs() if mode == "replay" else {"fixture": "composed-replay-synthetic-v1"}
        )
    for entry in inputs["authorities"].values():
        path = local_path(entry["path"])
        if (
            identity(path)["sha256"] != entry["sha256"]
            or json.loads(path.read_text()) != entry["document"]
        ):
            raise ValueError("Replay scientific contract identity changed")
    execution = inputs["execution"]
    binding = {
        "schema": "sat-dengue-replay-context-v1",
        "mode": mode,
        "operational": resolved["operational"],
        "authorities": {
            n: {k: v for k, v in a.items() if k != "document"}
            for n, a in inputs["authorities"].items()
        },
        "execution": {k: v for k, v in execution.items() if k not in {"run_id", "created_at"}},
        "inputs": sources,
    }
    key = digest(binding)
    folder = storage() / key
    entry = folder / "execution.json"
    if any(p.is_symlink() for p in (folder, *folder.parents)) or entry.is_symlink():
        raise ValueError("Unsafe replay execution path")
    if entry.exists():
        envelope = json.loads(entry.read_text())
        if envelope.get("binding") != binding or envelope.get("identity") != key:
            raise ValueError("Existing execution configuration/input identity changed")
    else:
        envelope = {
            "identity": key,
            "binding": binding,
            "created_at": datetime.now(UTC).isoformat(),
        }
        immutable_json(entry, envelope)
    context = {
        "identity": key,
        "folder": str(folder),
        "mode": mode,
        "inputs": inputs,
        "operational": resolved["operational"],
        "created_at": envelope["created_at"],
        "cache": {},
    }
    parents: dict[str, Any] = {}
    for stage in STAGES:
        path = folder / ("checkpoint-" + stage + ".json")
        if path.exists():
            identity(path)
            checkpoint = json.loads(path.read_text())
            if (
                set(checkpoint) != {"schema", "identity", "stage", "parents", "record"}
                or checkpoint["schema"] != "sat-dengue-replay-checkpoint-v1"
                or checkpoint["identity"] != key
                or checkpoint["stage"] != stage
                or checkpoint["parents"] != parents
            ):
                raise ValueError("Stale/incomplete replay checkpoint lineage")
            context["cache"][stage] = verify_publication(checkpoint["record"], context)
            if mode == "replay":
                from sat_dengue.datasets.replay_parity import evaluation_parity, training_parity
                from sat_dengue.datasets.replay_sources import data_parity, preparation_parity

                with no_adjustment():
                    {
                        "data": data_parity,
                        "preparation": preparation_parity,
                        "training": training_parity,
                        "evaluation": evaluation_parity,
                    }[stage](checkpoint["record"])
            parents[stage] = identity(Path(checkpoint["record"]["path"]) / "manifest.json")
        elif any(
            (folder / ("checkpoint-" + s + ".json")).exists()
            for s in STAGES[STAGES.index(stage) + 1 :]
        ):
            raise ValueError("Replay checkpoints have missing ancestors")
    return context


def stage_inputs(context: dict[str, Any], stage: str) -> dict[str, Any]:
    execution = {
        **context["inputs"]["execution"],
        "run_id": hashlib.sha256((context["identity"] + stage).encode()).hexdigest()[:32],
        "created_at": context["created_at"],
        "e2e": {
            "identity": context["identity"],
            "folder": context["folder"],
            "mode": context["mode"],
            "stage": stage,
        },
    }
    return {"authorities": context["inputs"]["authorities"], "execution": execution}


def checkpoint(record: dict[str, Any], context: dict[str, Any]) -> None:
    verify_publication(record, context)
    stage = record["stage"]
    folder = Path(context["folder"])
    parents: dict[str, Any] = {}
    for earlier in STAGES[: STAGES.index(stage)]:
        item = json.loads((folder / ("checkpoint-" + earlier + ".json")).read_text())
        verify_publication(item["record"], context)
        parents[earlier] = identity(Path(item["record"]["path"]) / "manifest.json")
    immutable_json(
        folder / ("checkpoint-" + stage + ".json"),
        {
            "schema": "sat-dengue-replay-checkpoint-v1",
            "identity": context["identity"],
            "stage": stage,
            "parents": parents,
            "record": record,
        },
    )
