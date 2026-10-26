"""MLflow artifact URI without private absolute paths; local JSON receipts only.

MLflow 3.17.2 canonicalizes file URIs to private absolute paths. Its supported
artifact repository extension point keeps a logical local URI in the database.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


def register_local_artifacts() -> None:
    # Optional imports stay behind the enabled tracking boundary.
    from mlflow.store.artifact.artifact_repository_registry import _artifact_repository_registry
    from mlflow.store.artifact.local_artifact_repo import LocalArtifactRepository

    from sat_dengue.tracking.local import allowed_parameters

    class ReceiptRepository(LocalArtifactRepository):
        def __init__(
            self,
            artifact_uri: str,
            tracking_uri: str | None = None,
            registry_uri: str | None = None,
        ) -> None:
            parsed = urlsplit(artifact_uri)
            relative = unquote(parsed.path).lstrip("/")
            folder = Path(relative)
            if (
                parsed.scheme != "satlocal"
                or parsed.netloc
                or parsed.query
                or parsed.fragment
                or not relative.startswith("tmp/")
                or ".." in folder.parts
                or any(p.is_symlink() for p in (folder, *folder.parents))
                or not folder.resolve().is_relative_to(Path.cwd().resolve() / "tmp")
            ):
                raise ValueError("Artifact URI must identify ignored repository-local storage")
            # MLflow decodes once more; give it an encoded form of the exact
            # filesystem path checked above, including any literal percent signs.
            super().__init__(quote(relative, safe="/"), tracking_uri, registry_uri)

        def log_artifact(self, local_file: str, artifact_path: str | None = None) -> None:
            source = Path(local_file)
            if (
                artifact_path is not None
                or re.fullmatch(r"[0-9a-f]{32}\.json", source.name) is None
                or source.is_symlink()
                or not source.resolve().is_relative_to(Path.cwd().resolve() / "tmp")
            ):
                raise ValueError("Only generated local lineage receipts may be logged")
            value = json.loads(source.read_text())
            if value.get("schema") == "bounded-mlflow-lineage-v1":
                valid = (
                    set(value) == {"schema", "parameters", "real_adjustments"}
                    and value["real_adjustments"] == 0
                )
            elif value.get("schema") == "exp01-synthetic-mlflow-lineage-v1":
                children = value.get("children")
                valid = (
                    set(value)
                    == {"schema", "parameters", "children", "real_model_fits", "real_adjustments"}
                    and value["real_model_fits"] == 0
                    and value["real_adjustments"] == 0
                    and isinstance(children, list)
                    and len(children) == 36
                    and len({tuple(child) for child in children if isinstance(child, list)}) == 36
                    and all(
                        isinstance(child, list)
                        and len(child) == 4
                        and child[0] in {"excess", "onset"}
                        and child[1] in {"xgboost", "lightgbm", "gam"}
                        and child[2] in {"1", "2"}
                        and child[3].startswith("synthetic_window_")
                        for child in children
                    )
                )
            elif value.get("schema") == "exp01-paired-mlflow-lineage-v1":
                from itertools import product

                from sat_dengue.experiments.exp01 import load_protocol

                protocol = load_protocol()
                children = value.get("children")
                fields = {
                    "objective",
                    "family",
                    "horizon",
                    "window",
                    "cohort_sha256",
                    "predictors_sha256",
                }
                expected = set(
                    product(
                        ("excess", "onset"),
                        protocol["design"]["families"],
                        (1, 2),
                        [window["id"] for window in protocol["design"]["windows"]],
                    )
                )
                valid = (
                    set(value) == {"schema", "parameters", "children"}
                    and isinstance(children, list)
                    and len(children) == 36
                    and all(isinstance(child, dict) and set(child) == fields for child in children)
                    and {(c["objective"], c["family"], c["horizon"], c["window"]) for c in children}
                    == expected
                    and all(
                        isinstance(c[key], str) and re.fullmatch(r"[0-9a-f]{64}", c[key])
                        for c in children
                        for key in ("cohort_sha256", "predictors_sha256")
                    )
                )
            else:
                valid = False
            if not valid:
                raise ValueError("Unapproved tracking artifact schema")
            allowed_parameters(value["parameters"])
            super().log_artifact(str(source))

        def log_artifacts(self, local_dir: str, artifact_path: str | None = None) -> None:
            raise ValueError("Bundle/directory uploads are forbidden")

        def download_artifacts(self, artifact_path: str, dst_path: str | None = None) -> str:
            if dst_path is None or not Path(dst_path).resolve().is_relative_to(
                Path.cwd().resolve() / "tmp"
            ):
                raise ValueError("Explicit local scratch download destination required")
            return str(super().download_artifacts(artifact_path, dst_path))

    _artifact_repository_registry.register("satlocal", ReceiptRepository)
