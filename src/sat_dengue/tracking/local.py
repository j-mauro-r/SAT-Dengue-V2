"""A small explicit MLflow client, limited to ignored local SQLite/artifacts."""

from __future__ import annotations

import fcntl
import importlib
import json
import math
import os
import re
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sat_dengue.configuration import AUTHORITIES, canonical_bytes

from .experiments import MLFLOW_EXPERIMENT_NAME, resolve_experiment
from .lineage import AGGREGATES, COUNTERS, verified_lineage

PARAMETERS = {
    "git_revision",
    "git_dirty",
    "python_version",
    "kedro_version",
    "mlflow_version",
    "environment_sha256",
    "code_sha256",
    "input_sha256",
    "configuration_sha256",
    "bundle_id",
    "manifest_sha256",
    "pipeline_identity_sha256",
    "profile",
    "kind",
    "metric_definition_sha256",
    "seed",
    "cohort",
    "window",
    "G5",
    "champion",
    "native_pointer",
    "family",
    "horizon",
    "decision",
    "observability_profile",
    *("contract_" + n for n in AUTHORITIES),
    *("version_" + n for n in AUTHORITIES),
}


def allowed_parameters(values: dict[str, Any]) -> dict[str, str]:
    if not set(values) <= PARAMETERS:
        raise ValueError("Tracking field is not allowlisted")
    result = {}
    for name, value in values.items():
        text = str(value)
        if re.search(r"(?:gh[pousr]_\w+|AKIA[A-Z0-9]+|AIza\w+|PRIVATE.KEY)", text):
            raise ValueError("Credential-shaped tracking value rejected")
        pattern = r"[A-Za-z0-9_.+-]{1,128}"
        if name == "native_pointer":
            pattern = r"tmp/[A-Za-z0-9_./-]+/[0-9a-f]{64}"
        if (
            re.fullmatch(pattern, text) is None
            or ".." in Path(text).parts
            or Path(text).is_absolute()
        ):
            raise ValueError("Tracking value rejected; use hashes and approved tokens")
        if name.endswith("sha256") or name.startswith("contract_") or name == "bundle_id":
            if re.fullmatch(r"[0-9a-f]{64}", text) is None:
                raise ValueError("Tracking hash is invalid")
        result[name] = text
    return result


class LocalTracking:
    """One pipeline parent; verified candidate/horizon children; explicit terminal state."""

    def __init__(
        self,
        pipeline: str,
        execution: str,
        root: str | None = None,
        profile: str | None = None,
        *,
        experiment_id: str | None = None,
    ) -> None:
        allowed_parameters({"profile": pipeline})
        self.conceptual = resolve_experiment(experiment_id) if experiment_id is not None else {}
        if self.conceptual and self.conceptual.pop("pipeline") != pipeline:
            raise ValueError("Registered experiment pipeline mismatch")
        if pipeline in {"replay", "training_replay", "evaluation_replay"} and not self.conceptual:
            raise ValueError("Real scientific tracking requires experiment_id")
        if re.fullmatch(r"[A-Za-z0-9_.+-]{1,128}", pipeline) is None:
            raise ValueError("Unapproved pipeline name")
        root = root if root is not None else os.environ.get("SAT_DENGUE_TRACKING_ROOT", "")
        profile = (
            profile
            if profile is not None
            else os.environ.get("SAT_DENGUE_TRACKING_PROFILE", "standard")
        )
        if profile not in {"standard", "diagnostic"}:
            raise ValueError("Unknown operational tracking profile")
        if (
            not root
            or Path(root).is_absolute()
            or ".." in Path(root).parts
            or not root.startswith("tmp/")
        ):
            raise ValueError("Enabled tracking requires SAT_DENGUE_TRACKING_ROOT=tmp/<local-store>")
        self.root = Path(root)
        self._validate_storage()
        if any(
            subprocess.run(["git", "check-ignore", "-q", "--", str(self.root / child)]).returncode
            != 0
            for child in ("tracking.sqlite", "artifacts/probe")
        ):
            raise ValueError("Tracking metadata and artifacts must be ignored by Git")
        # Local tracking must not initialize or emit the SDK's separate usage
        # telemetry. Keep this opt-out active for the lifetime of the process.
        os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
        try:
            client_module = importlib.import_module("mlflow.tracking")
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "Enabled tracking requires sat-dengue-v2[tracking]; install the optional extra"
            ) from error
        from .artifacts import register_local_artifacts

        register_local_artifacts()
        self.root.mkdir(parents=True, exist_ok=True)
        # Keep even MLflow's automatic Default experiment free of private paths.
        artifact_location = "satlocal:/" + quote(str(self.root / "artifacts"), safe="/")
        previous_root = os.environ.get("_MLFLOW_SERVER_ARTIFACT_ROOT")
        os.environ["_MLFLOW_SERVER_ARTIFACT_ROOT"] = artifact_location
        try:
            self.client: Any = client_module.MlflowClient(
                tracking_uri="sqlite:///" + quote(str(self.root / "tracking.sqlite"), safe="/")
            )
        finally:
            if previous_root is None:
                os.environ.pop("_MLFLOW_SERVER_ARTIFACT_ROOT", None)
            else:
                os.environ["_MLFLOW_SERVER_ARTIFACT_ROOT"] = previous_root
        experiment = self.client.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME)
        self.experiment = (
            experiment.experiment_id
            if experiment
            else self.client.create_experiment(
                MLFLOW_EXPERIMENT_NAME, artifact_location=artifact_location
            )
        )
        expected_location = artifact_location
        if self.client.get_experiment(self.experiment).artifact_location != expected_location:
            raise ValueError("Experiment artifact storage identity changed")
        if re.fullmatch(r"[A-Za-z0-9_.+-]{1,128}", pipeline) is None:
            raise ValueError("Unapproved pipeline name")
        # Kedro IDs can contain UTC punctuation; hash them, never log an arbitrary value.
        import hashlib

        self.execution = hashlib.sha256(execution.encode()).hexdigest()
        # Pin each scientific identity in this store, even if the registry is later edited.
        with self._lock():
            if self.conceptual:
                key = "protocol." + self.conceptual["experiment_id"]
                pinned = self.client.get_experiment(self.experiment).tags.get(key)
                if pinned is not None and pinned != self.conceptual["protocol_sha256"]:
                    raise ValueError("Experiment protocol is already frozen in this store")
                self.client.set_experiment_tag(
                    self.experiment, key, self.conceptual["protocol_sha256"]
                )
        name = (
            self.conceptual["experiment_id"] + ":" + self.conceptual["experiment_slug"]
            if self.conceptual
            else pipeline
        )
        self.parent = self.client.create_run(
            self.experiment,
            tags={
                "mlflow.runName": name + ":" + self.execution[:12],
                **self.conceptual,
                "pipeline": pipeline,
                "status": "running",
            },
        ).info.run_id
        self.pipeline = pipeline
        self.terminal = False
        self.children: list[str] = []
        self.params(self.parent, {"observability_profile": profile})

    @contextmanager
    def _lock(self) -> Iterator[None]:
        self._validate_storage()
        with (self.root / ".registration.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _validate_storage(self) -> None:
        if not self.root.resolve().is_relative_to(Path.cwd().resolve() / "tmp") or any(
            p.is_symlink() for p in [self.root, *self.root.parents]
        ):
            raise ValueError("Tracking storage escapes the local repository")
        # A safe root alone does not constrain SQLite sidecars or receipt destinations.
        if any(path.is_symlink() for path in self.root.rglob("*")):
            raise ValueError("Tracking storage must not contain symlinks")

    def params(self, run: str, values: dict[str, Any]) -> None:
        for key, value in allowed_parameters(values).items():
            self.client.log_param(run, key, value)

    def metrics(self, run: str, values: dict[str, float]) -> None:
        if not set(values) <= AGGREGATES | set(COUNTERS) or any(
            not math.isfinite(v) for v in values.values()
        ):
            raise ValueError("Tracking metric is not an approved finite aggregate")
        for key, value in values.items():
            self.client.log_metric(run, key, value)

    def finish(self, publication: dict[str, Any]) -> str:
        # Serialize duplicate lookup and success publication across local processes.
        try:
            with self._lock():
                return self._finish(publication)
        except BaseException:
            self.fail()
            raise

    def _finish(self, publication: dict[str, Any]) -> str:
        if self.terminal:
            raise RuntimeError("Tracking run is already terminal")
        try:
            self._validate_storage()
            params, candidates = verified_lineage(publication)
            real_pipeline = self.pipeline in {"replay", "training_replay", "evaluation_replay"}
            if real_pipeline and params["kind"] != "replay":
                raise ValueError("Scientific replay cannot register a synthetic publication")
            if self.pipeline.endswith("_synthetic") and params["kind"] != "synthetic":
                raise ValueError("Synthetic pipeline cannot register a real publication")
            if params["kind"] == "replay" and not self.conceptual:
                raise ValueError("Real scientific tracking requires experiment_id")
            operational = json.loads((Path(publication["path"]) / "provenance.json").read_text())[
                "operational"
            ]
            recorded_id = operational.get("experiment_id")
            if (
                recorded_id is not None or params["kind"] == "replay"
            ) and recorded_id != self.conceptual.get("experiment_id"):
                raise ValueError("Publication experiment identity mismatch")
            if self.conceptual:
                current = resolve_experiment(self.conceptual["experiment_id"])
                if current != {**self.conceptual, "pipeline": self.pipeline}:
                    raise ValueError("Experiment protocol changed during execution")
            self.params(self.parent, params)
            self.metrics(self.parent, dict.fromkeys(COUNTERS, 0.0))
            conceptual_filter = "".join(
                " and tags." + key + " = '" + self.conceptual[key] + "'"
                for key in ("experiment_id", "protocol_sha256")
                if self.conceptual
            )
            previous = self.client.search_runs(
                [self.experiment],
                filter_string="attributes.status = 'FINISHED' and params.bundle_id = '"
                + params["bundle_id"]
                + "' and tags.pipeline = '"
                + self.pipeline
                + "' and tags.status = 'verified'"
                + conceptual_filter,
            )
            previous = [
                run
                for run in previous
                if "mlflow.parentRunId" not in run.data.tags
                and all(
                    run.data.tags.get(k) == self.conceptual.get(k)
                    for k in ("experiment_id", "protocol_sha256")
                )
            ]
            if previous:
                existing = previous[0]
                if any(
                    existing.data.params.get(k) != v for k, v in allowed_parameters(params).items()
                ):
                    raise ValueError("Existing verified run lineage changed")
                existing_children = self.client.search_runs(
                    [self.experiment],
                    filter_string="tags.mlflow.parentRunId = '" + existing.info.run_id + "'",
                )
                expected = sorted((c["family"], c["horizon"], c["window"]) for c in candidates)
                actual = sorted(
                    (
                        c.data.params.get("family", ""),
                        c.data.params.get("horizon", ""),
                        c.data.params.get("window", ""),
                    )
                    for c in existing_children
                )
                if any(existing.data.metrics.get(k) != 0 for k in COUNTERS):
                    raise ValueError("Existing verified run counters changed")
                for child in existing_children:
                    candidate = next(
                        (
                            c
                            for c in candidates
                            if (c["family"], c["horizon"], c["window"])
                            == (
                                child.data.params.get("family"),
                                child.data.params.get("horizon"),
                                child.data.params.get("window"),
                            )
                        ),
                        None,
                    )
                    if (
                        candidate is None
                        or child.data.params.get("decision") != candidate["decision"]
                        or child.data.metrics != candidate["metrics"]
                        or any(child.data.tags.get(k) != v for k, v in self.conceptual.items())
                    ):
                        raise ValueError("Existing verified child scientific lineage changed")
                if actual != expected or any(
                    c.info.status != "FINISHED" for c in existing_children
                ):
                    raise ValueError("Existing verified run children changed")
                self.client.set_tag(self.parent, "duplicate_of", str(previous[0].info.run_id))
                self.client.set_tag(self.parent, "status", "duplicate_verified")
                self.client.set_terminated(self.parent, "KILLED")
                self.terminal = True
                return str(previous[0].info.run_id)
            for candidate in candidates:
                child_parameters = allowed_parameters(
                    {k: candidate[k] for k in ("family", "horizon", "decision", "window")}
                )
                child = self.client.create_run(
                    self.experiment,
                    tags={
                        "mlflow.parentRunId": self.parent,
                        "mlflow.runName": (
                            self.conceptual["experiment_id"] + ":" if self.conceptual else ""
                        )
                        + candidate["family"]
                        + ":t"
                        + candidate["horizon"]
                        + ":"
                        + candidate["window"],
                        **self.conceptual,
                        "pipeline": self.pipeline,
                        "status": "verified",
                    },
                ).info.run_id
                self.children.append(child)
                self.params(child, child_parameters)
                self.params(child, {"bundle_id": params["bundle_id"], "kind": params["kind"]})
                self.metrics(child, candidate["metrics"])
            # Upload only a typed projection; never accept caller-provided artifact bytes.
            receipt = self.root / "receipts" / (self.parent + ".json")
            receipt.parent.mkdir(exist_ok=True)
            receipt.write_bytes(
                canonical_bytes(
                    {
                        "schema": "bounded-mlflow-lineage-v1",
                        "parameters": allowed_parameters(params),
                        "real_adjustments": 0,
                    }
                )
            )
            self.client.log_artifact(self.parent, str(receipt))
            for child in self.children:
                self.client.set_terminated(child, "FINISHED")
            self.client.set_tag(self.parent, "status", "verified")
            self.client.set_terminated(self.parent, "FINISHED")
            self.terminal = True
            return str(self.parent)
        except BaseException:
            self.fail()
            raise

    def fail(self, aborted: bool = False) -> None:
        if self.terminal:
            return
        for run in [*self.children, self.parent]:
            self.client.set_tag(run, "status", "aborted" if aborted else "failed")
            self.client.set_terminated(run, "KILLED" if aborted else "FAILED")
        self.terminal = True
