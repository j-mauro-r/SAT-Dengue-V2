"""A small explicit MLflow client, limited to ignored local SQLite/artifacts."""

from __future__ import annotations

import importlib
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from sat_dengue.configuration import AUTHORITIES, canonical_bytes

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
        self, pipeline: str, execution: str, root: str | None = None, profile: str | None = None
    ) -> None:
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
        if not self.root.resolve().is_relative_to(Path.cwd().resolve() / "tmp") or any(
            p.is_symlink() for p in [self.root, *self.root.parents]
        ):
            raise ValueError("Tracking storage escapes the local repository")
        if any(
            subprocess.run(["git", "check-ignore", "-q", "--", str(self.root / child)]).returncode
            != 0
            for child in ("tracking.sqlite", "artifacts/probe")
        ):
            raise ValueError("Tracking metadata and artifacts must be ignored by Git")
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
        artifact_location = "satlocal:/" + str(self.root / "artifacts")
        previous_root = os.environ.get("_MLFLOW_SERVER_ARTIFACT_ROOT")
        os.environ["_MLFLOW_SERVER_ARTIFACT_ROOT"] = artifact_location
        try:
            self.client: Any = client_module.MlflowClient(
                tracking_uri="sqlite:///" + str(self.root / "tracking.sqlite")
            )
        finally:
            if previous_root is None:
                os.environ.pop("_MLFLOW_SERVER_ARTIFACT_ROOT", None)
            else:
                os.environ["_MLFLOW_SERVER_ARTIFACT_ROOT"] = previous_root
        experiment = self.client.get_experiment_by_name("sat-dengue-bounded-v1")
        self.experiment = (
            experiment.experiment_id
            if experiment
            else self.client.create_experiment(
                "sat-dengue-bounded-v1", artifact_location=artifact_location
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
        self.parent = self.client.create_run(
            self.experiment,
            tags={
                "mlflow.runName": pipeline + ":" + self.execution,
                "pipeline": pipeline,
                "status": "running",
            },
        ).info.run_id
        self.pipeline = pipeline
        self.terminal = False
        self.children: list[str] = []
        self.params(self.parent, {"observability_profile": profile})

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
        if self.terminal:
            raise RuntimeError("Tracking run is already terminal")
        try:
            params, candidates = verified_lineage(publication)
            self.params(self.parent, params)
            self.metrics(self.parent, dict.fromkeys(COUNTERS, 0.0))
            previous = self.client.search_runs(
                [self.experiment],
                filter_string="attributes.status = 'FINISHED' and params.bundle_id = '"
                + params["bundle_id"]
                + "' and tags.pipeline = '"
                + self.pipeline
                + "'",
            )
            if previous:
                self.client.set_tag(self.parent, "status", "duplicate_verified")
                self.client.set_terminated(self.parent, "KILLED")
                self.terminal = True
                return str(previous[0].info.run_id)
            for candidate in candidates:
                child = self.client.create_run(
                    self.experiment,
                    tags={
                        "mlflow.parentRunId": self.parent,
                        "mlflow.runName": candidate["family"]
                        + ":t"
                        + candidate["horizon"]
                        + ":"
                        + candidate.get("window", "2025"),
                        "status": "verified",
                    },
                ).info.run_id
                self.children.append(child)
                self.params(
                    child, {k: candidate[k] for k in ("family", "horizon", "decision", "window")}
                )
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
