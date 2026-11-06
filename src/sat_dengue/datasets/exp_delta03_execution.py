"""EXP-DELTA03 authorization and transactional native evidence; no implicit real run."""

from __future__ import annotations

import fcntl
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sat_dengue.datasets.exp_delta03 import identity, safe_path
from sat_dengue.experiments.exp_delta03_contract import canonical, digest, validate_freeze

STAGES = ("trained", "calibrated", "selected", "predicted", "evaluated")
CODE_FILES = (
    "src/sat_dengue/experiments/exp_delta03_contract.py",
    "src/sat_dengue/experiments/exp_delta03_learning.py",
    "src/sat_dengue/experiments/exp_delta03_evaluation.py",
    "src/sat_dengue/model_training/exp_delta03_adapter.py",
    "src/sat_dengue/datasets/exp_delta03_training.py",
    "src/sat_dengue/datasets/exp_delta03_execution.py",
    "src/sat_dengue/pipelines/exp_delta03/pipeline.py",
    "src/sat_dengue/configuration.py",
    "src/sat_dengue/config_loader.py",
    "src/sat_dengue/settings.py",
    "src/sat_dengue/pipeline_registry.py",
    "conf/base/catalog.yml",
    "conf/base/parameters.yml",
    "pyproject.toml",
)


def fingerprint(root: Path, context: dict[str, Any], roots: dict[str, str]) -> dict[str, Any]:
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    versions = {}
    for name in ("kedro", "numpy", "pandas", "xgboost", "scipy", "scikit-learn", "mlflow"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "UNAVAILABLE"
    return {
        "commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "code": {p: identity(root / p) for p in CODE_FILES},
        "runtime": versions,
        "training_contract_sha256": context["training_contract_sha256"],
        "protocol_sha256": identity(
            root / "docs/product/experiments/EXP-DELTA03/protocol.draft.json"
        )["sha256"],
        "matrix_manifest_sha256": context["contract"]["matrix_bundle"]["manifest_sha256"],
        "execution_plan_sha256": digest(context["plan"]),
        "roots": roots,
    }


def authorize(
    root: Path,
    context: dict[str, Any],
    current: dict[str, Any],
    *,
    authorization_relative: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Read-only; no reservation, data-row read, estimator or tracker precedes this gate."""
    validate_freeze(context["contract"], synthetic=False)
    path = safe_path(root, authorization_relative, "tmp/exp-delta03-phase3")
    if not path.is_file():
        raise PermissionError("Separate explicit Phase3 authorization is required")
    authorization_bytes = path.read_bytes()
    grant = json.loads(authorization_bytes)
    if grant.get("schema") != "exp-delta03-phase3-authorization-v1" or grant.get("phase") != 3:
        raise PermissionError("Unexpected scientific authorization")
    if grant.get("approved_by") != "Mauricio" or current["dirty"]:
        raise PermissionError("Human approval and a clean frozen commit are required")
    if grant.get("identity") != current or grant.get("identity_sha256") != digest(current):
        raise PermissionError("Scientific execution identity mismatch")
    now = now or datetime.now(UTC)
    start = datetime.fromisoformat(grant["issued_at"])
    end = datetime.fromisoformat(grant["expires_at"])
    if start.tzinfo is None or end.tzinfo is None or not start <= now <= end:
        raise PermissionError("Authorization time window is not valid")
    counts = context["plan"]["counts"]
    limits = grant["limits"]
    if (
        limits["max_models"] != counts["models"]
        or limits["max_calibrators"] != counts["calibrators"]
        or limits["threads_per_model"] != 1
        or limits["wall_seconds"] <= 0
    ):
        raise PermissionError("Execution/resource cap differs from frozen derived plan")
    expected = {
        "retrospective_only",
        "no_PIT_or_deployment",
        "2025_excluded",
        "2024_stress_separate",
        "manual_execution",
    }
    if set(grant["acknowledgements"]) != expected:
        raise PermissionError("Scientific scope acknowledgements missing")
    if any(value == "UNAVAILABLE" for value in current["runtime"].values()):
        raise PermissionError("Scientific runtime extras unavailable")
    safe_path(root, current["roots"]["publication"], "data/processed/exp_delta03")
    safe_path(root, current["roots"]["tracking"], "tmp")
    return {
        "identity": current,
        "authorization_sha256": hashlib.sha256(authorization_bytes).hexdigest(),
        "allow_resume": grant["allow_resume"],
        "limits": limits,
    }


def token(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]{1,100}", value) is None:
        raise ValueError("Unsafe execution token")
    return value


def snapshot(path: Path, expected: dict[str, Any]) -> bytes:
    raw = path.read_bytes()
    if {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)} != expected:
        raise ValueError("Native checkpoint/artifact changed")
    return raw


class ExecutionStore:
    """One locked execution, immutable stage checkpoints and atomic final publication."""

    def __init__(
        self,
        root: Path,
        relative: str,
        execution_identity: dict[str, Any],
        *,
        synthetic: bool,
        resume: bool = False,
        permission: dict[str, Any] | None = None,
    ) -> None:
        if not synthetic and (
            permission is None or permission.get("identity") != execution_identity
        ):
            raise PermissionError("Real execution storage requires a verified Phase3 grant")
        if not synthetic and (
            relative != execution_identity["roots"]["publication"]
            or (resume and permission is not None and not permission["allow_resume"])
        ):
            raise PermissionError("Publication root/resume differs from authorization")
        prefix = "tmp/exp-delta03-phase2" if synthetic else "data/processed/exp_delta03"
        self.root, self.prefix, self.relative = root, prefix, relative
        self.identity = execution_identity
        self.execution = digest(execution_identity)
        self.parent = safe_path(root, relative, prefix)
        self.resume = resume
        self.closed = False
        self.started = time.monotonic()
        self.fd: int | None = None
        self.path = self.parent / self.execution

    def _path(self, *names: str) -> Path:
        return safe_path(
            self.root, str(self.path.joinpath(*names).relative_to(self.root)), self.prefix
        )

    def __enter__(self):
        self.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = safe_path(self.root, str(self.path.relative_to(self.root)), self.prefix)
        self.path.mkdir(exist_ok=True, mode=0o700)
        lock = self._path(".lock")
        self.fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state_path = self._path("state.json")
            if state_path.exists():
                state = json.loads(state_path.read_bytes())
                if state["identity"] != self.identity:
                    raise ValueError("Execution identity changed")
                if state["status"] != "COMPLETE" and not self.resume:
                    raise ValueError("Incomplete execution requires explicit resume")
                self.state = state
            else:
                self.state = {
                    "schema": "exp-delta03-execution-state-v1",
                    "identity": self.identity,
                    "status": "INCOMPLETE",
                    "stages": {},
                    "publication": None,
                }
                self._save_state()
            return self
        except BaseException:
            os.close(self.fd)
            self.fd = None
            raise

    def __exit__(self, exc_type, exc, traceback):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        self.closed = True

    def _save_state(self) -> None:
        target = self._path("state.json")
        fd, name = tempfile.mkstemp(prefix=".state-", dir=self.path)
        scratch = Path(name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(canonical(self.state))
                stream.flush()
                os.fsync(stream.fileno())
            safe_path(self.root, str(target.relative_to(self.root)), self.prefix)
            os.replace(scratch, target)
        finally:
            scratch.unlink(missing_ok=True)

    def read_stage(self, cell: str, stage: str) -> dict[str, bytes] | None:
        key = token(cell) + "." + stage
        if stage not in STAGES:
            raise ValueError("Unknown scientific stage")
        record = self.state["stages"].get(key)
        if record is None:
            orphan = self._path(key)
            if not orphan.exists():
                return None
            if not self.resume:
                raise ValueError("Orphan checkpoint requires explicit resume")
            raw = self._path(key, "stage-manifest.json").read_bytes()
            stage_record = json.loads(raw)
            if (
                stage_record["identity_sha256"] != digest(self.identity)
                or stage_record["cell"] != cell
                or stage_record["stage"] != stage
            ):
                raise ValueError("Orphan checkpoint identity changed")
            record = {
                "files": stage_record["files"],
                "identity_sha256": digest(self.identity),
                "stage_manifest_sha256": hashlib.sha256(raw).hexdigest(),
            }
            self.state["stages"][key] = record
        manifest_raw = self._path(key, "stage-manifest.json").read_bytes()
        if hashlib.sha256(manifest_raw).hexdigest() != record["stage_manifest_sha256"]:
            raise ValueError("Checkpoint manifest changed")
        parsed = json.loads(manifest_raw)
        if (
            parsed["identity_sha256"] != digest(self.identity)
            or parsed["cell"] != cell
            or parsed["stage"] != stage
            or parsed["files"] != record["files"]
        ):
            raise ValueError("Checkpoint identity/record changed")
        if {p.name for p in self._path(key).iterdir()} != {"stage-manifest.json", *record["files"]}:
            raise ValueError("Checkpoint inventory changed")
        folder = self._path(key)
        return {
            name: snapshot(
                safe_path(self.root, str((folder / name).relative_to(self.root)), self.prefix), fp
            )
            for name, fp in record["files"].items()
        }

    def save_stage(self, cell: str, stage: str, payloads: dict[str, bytes]) -> None:
        if self.closed or self.fd is None or self.state["status"] == "COMPLETE":
            raise ValueError("Execution is not writable")
        previous = self.read_stage(cell, stage)
        if previous is not None:
            if previous != payloads:
                raise ValueError("Checkpoint overwrite forbidden")
            return
        index = STAGES.index(stage)
        if index and self.read_stage(cell, STAGES[index - 1]) is None:
            raise ValueError("Missing preceding scientific stage")
        key = token(cell) + "." + stage
        destination = self._path(key)
        records = {
            name: {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            for name, raw in payloads.items()
        }
        manifest = canonical(
            {
                "schema": "exp-delta03-stage-v1",
                "cell": cell,
                "stage": stage,
                "identity_sha256": digest(self.identity),
                "files": records,
            }
        )
        if "stage-manifest.json" in payloads:
            raise ValueError("Reserved checkpoint member")
        self._write_directory(destination, {**payloads, "stage-manifest.json": manifest})
        self.state["stages"][key] = {
            "files": records,
            "identity_sha256": digest(self.identity),
            "stage_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        }
        self._save_state()

    def _write_directory(self, destination: Path, payloads: dict[str, bytes]) -> None:
        if not payloads or any(Path(n).name != n or n in {".", ".."} for n in payloads):
            raise ValueError("Unsafe native member")
        staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=self.path))
        try:
            for name, raw in payloads.items():
                with (staging / name).open("xb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                (staging / name).chmod(0o600)
            if destination.exists():
                raise ValueError("Existing native destination is never replaced")
            safe_path(self.root, str(destination.relative_to(self.root)), self.prefix)
            os.rename(staging, destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)

    def publish(self, payloads: dict[str, bytes]) -> dict[str, Any]:
        if self.closed or self.fd is None:
            raise ValueError("Publication requires an active execution lock")
        if not payloads or any(
            Path(n).name != n or n in {"manifest.json", ".", ".."} for n in payloads
        ):
            raise ValueError("Unsafe/reserved publication member")
        records = {
            n: {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            for n, raw in sorted(payloads.items())
        }
        bundle = digest(records)
        manifest = canonical(
            {
                "schema": "exp-delta03-native-bundle-v1",
                "bundle_id": bundle,
                "execution_identity_sha256": digest(self.identity),
                "files": records,
            }
        )
        if self.state["status"] == "COMPLETE":
            recorded = self.state["publication"]
            if recorded is None or recorded["bundle_id"] != bundle:
                raise ValueError("Completed execution cannot publish different payloads")
            actual = verify_publication(
                self.root, recorded, synthetic=self.prefix.startswith("tmp/")
            )
            if actual != payloads:
                raise ValueError("Completed publication differs")
            return dict(recorded)
        destination = self._path(bundle)
        complete = {**payloads, "manifest.json": manifest}
        if destination.exists():
            if {p.name for p in destination.iterdir()} != set(complete):
                raise ValueError("Existing publication inventory changed")
            for name, raw in complete.items():
                if self._path(bundle, name).read_bytes() != raw:
                    raise ValueError("Existing publication changed")
        else:
            self._write_directory(destination, complete)
        publication = {
            "path": str(destination.relative_to(self.root)),
            "bundle_id": bundle,
            "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "execution_identity_sha256": digest(self.identity),
        }
        self.state.update(status="COMPLETE", publication=publication)
        self._save_state()
        return publication


def verify_publication(
    root: Path, publication: dict[str, Any], *, synthetic: bool
) -> dict[str, Any]:
    prefix = "tmp/exp-delta03-phase2" if synthetic else "data/processed/exp_delta03"
    folder = safe_path(root, publication["path"], prefix)
    raw = safe_path(root, publication["path"] + "/manifest.json", prefix).read_bytes()
    if hashlib.sha256(raw).hexdigest() != publication["manifest_sha256"]:
        raise ValueError("Native publication manifest changed")
    manifest = json.loads(raw)
    if (
        digest(manifest["files"]) != publication["bundle_id"]
        or folder.name != publication["bundle_id"]
    ):
        raise ValueError("Native bundle identity changed")
    if {f.name for f in folder.iterdir()} != {"manifest.json", *manifest["files"]}:
        raise ValueError("Native publication inventory changed")
    return {
        name: snapshot(safe_path(root, publication["path"] + "/" + name, prefix), fp)
        for name, fp in manifest["files"].items()
    }
