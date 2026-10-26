"""EXP01 publication tracking using the established local client and tag schema."""

from __future__ import annotations

import json
from itertools import product
from typing import Any

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.stage2 import identity
from sat_dengue.experiments.exp01 import digest, load_protocol
from sat_dengue.experiments.exp01_preflight import safe_path
from sat_dengue.tracking.local import LocalTracking


def verified_result(publication: dict[str, Any]) -> dict[str, Any]:
    folder = safe_path(publication["path"], temporary=True)
    manifest = json.loads((folder / "manifest.json").read_text())
    body = {k: v for k, v in manifest.items() if k != "bundle_id"}
    if (
        manifest != publication["manifest"]
        or digest(body) != manifest["bundle_id"]
        or folder.name != manifest["bundle_id"]
        or set(manifest["files"]) != {"result.json", "provenance.json"}
        or {p.name for p in folder.iterdir()} != {"manifest.json", *manifest["files"]}
    ):
        raise ValueError("Invalid EXP01 publication manifest")
    for name, expected in manifest["files"].items():
        if identity(safe_path(str(folder / name))) != expected:
            raise ValueError("EXP01 publication payload changed")
    result = json.loads((folder / "result.json").read_text())
    provenance = json.loads((folder / "provenance.json").read_text())
    validate_result(result, provenance)
    return {"result": result, "provenance": provenance, "manifest": manifest}


def validate_result(result: dict[str, Any], provenance: dict[str, Any]) -> None:
    """Validate in memory before atomic native publication or any tracking success."""
    protocol = load_protocol()
    if (
        type(result["synthetic"]) is not bool
        or result["schema"] != "exp01-paired-result-v1"
        or result["experiment_id"] != "EXP01"
        or provenance["protocol_sha256"] != digest(protocol)
        or provenance["code_sha256"] != digest(provenance["code"])
        or provenance["environment_sha256"] != digest(provenance["runtime"])
        or result["G5"] != "NOT_APPROVED"
        or result["champion"] != "not_selected"
        or any(
            result[k] != (0 if result["synthetic"] else 36)
            for k in ("real_model_fits", "real_preparer_refits", "calibrator_fits")
        )
    ):
        raise ValueError("EXP01 result identity or counters differ")
    expected = set(
        product(
            ("excess", "onset"),
            protocol["design"]["families"],
            (1, 2),
            [w["id"] for w in protocol["design"]["windows"]],
        )
    )
    children = result["children"]
    actual = [(c["objective"], c["family"], c["horizon"], c["window"]) for c in children]
    if len(children) != 36 or set(actual) != expected:
        raise ValueError("EXP01 requires the frozen 36-child structure")
    paired: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
    for child in children:
        paired.setdefault((child["family"], child["horizon"], child["window"]), []).append(child)
    for arms in paired.values():
        if any(
            arms[0][key] != arms[1][key]
            for key in ("cohort_sha256", "predictors_sha256", "coverage", "role_sha256")
        ):
            raise ValueError("EXP01 paired cohorts or predictors differ")


class Exp01Tracking(LocalTracking):
    """Separate EXP01 finish boundary; EXP00's replay registration stays unchanged."""

    def initialize_paired(self, provenance: dict[str, Any], *, synthetic: bool) -> dict[str, Any]:
        """Record identity and purpose before the first adapter call, including failures."""
        if self.pipeline != ("exp01_synthetic" if synthetic else "exp01"):
            raise ValueError("EXP01 tracking route differs from execution purpose")
        purpose = (
            "synthetic_interface_probe" if synthetic else "authorized_retrospective_experiment"
        )
        common = {
            "protocol_sha256": provenance["protocol_sha256"],
            "protocol_version": load_protocol()["version"],
            "data_sha256": provenance["data_sha256"],
            "input_sha256": provenance["data_version"],
            "git_revision": provenance["git_revision"],
            "git_dirty": "false",
            "configuration_sha256": provenance["configuration_sha256"],
            "code_sha256": provenance["code_sha256"],
            "environment_sha256": provenance["environment_sha256"],
            "cohort": "non_excess_at_t",
            "kind": "synthetic" if synthetic else "real",
            "evidence_type": purpose,
            "G5": "NOT_APPROVED",
            "champion": "not_selected",
        }
        self.params(self.parent, common)
        self.client.set_tag(self.parent, "purpose", purpose)
        self.client.set_tag(self.parent, "cohort", "non_excess_at_t")
        return common

    def finish_paired(self, publication: dict[str, Any]) -> str:
        try:
            with self._lock():
                if self.terminal:
                    raise RuntimeError("EXP01 tracking is already terminal")
                verified = verified_result(publication)
                result, provenance = verified["result"], verified["provenance"]
                synthetic = result["synthetic"]
                expected_pipeline = "exp01_synthetic" if synthetic else "exp01"
                if (
                    self.pipeline != expected_pipeline
                    or self.conceptual.get("experiment_id") != "EXP01"
                ):
                    raise ValueError("EXP01 publication does not match its tracking route")
                common = self.initialize_paired(provenance, synthetic=synthetic)
                common["bundle_id"] = verified["manifest"]["bundle_id"]
                self.params(self.parent, {"bundle_id": common["bundle_id"]})
                purpose = common["evidence_type"]
                self.metrics(
                    self.parent,
                    {
                        k: float(result[k])
                        for k in ("real_model_fits", "real_preparer_refits", "calibrator_fits")
                    },
                )
                previous = self.client.search_runs(
                    [self.experiment],
                    filter_string="tags.pipeline = '"
                    + self.pipeline
                    + "' and params.bundle_id = '"
                    + common["bundle_id"]
                    + "' and attributes.status = 'FINISHED'",
                )
                if previous:
                    raise ValueError("EXP01 publication already has completed tracking")
                for child in result["children"]:
                    run = self.client.create_run(
                        self.experiment,
                        tags={
                            **self.conceptual,
                            "pipeline": self.pipeline,
                            "mlflow.parentRunId": self.parent,
                            "mlflow.runName": "EXP01:"
                            + child["objective"]
                            + ":"
                            + child["family"]
                            + ":t"
                            + str(child["horizon"])
                            + ":"
                            + child["window"],
                            "purpose": purpose,
                            "cohort": child["cohort"],
                            "status": "running",
                        },
                    ).info.run_id
                    self.children.append(run)
                    self.params(
                        run,
                        {
                            **common,
                            **{
                                k: child[k]
                                for k in (
                                    "objective",
                                    "family",
                                    "horizon",
                                    "window",
                                    "cohort",
                                    "seed",
                                )
                            },
                            "evidence_type": "synthetic_interface_probe"
                            if synthetic
                            else child["evidence_type"],
                        },
                    )
                    if not synthetic:
                        self.metrics(
                            run,
                            {
                                k: float(child[k])
                                for k in ("average_precision", "auroc", "brier")
                                if child[k] is not None
                            },
                        )
                # Only typed aggregate lineage is uploaded; full frontier stays native.
                record = self.root / "receipts" / (self.parent + ".json")
                record.parent.mkdir(exist_ok=True)
                record.write_bytes(
                    canonical_bytes(
                        {
                            "schema": "exp01-paired-mlflow-lineage-v1",
                            "parameters": common,
                            "children": [
                                {
                                    k: child[k]
                                    for k in (
                                        "objective",
                                        "family",
                                        "horizon",
                                        "window",
                                        "cohort_sha256",
                                        "predictors_sha256",
                                    )
                                }
                                for child in result["children"]
                            ],
                        }
                    )
                )
                self.client.log_artifact(self.parent, str(record))
                for run in self.children:
                    self.client.set_tag(run, "status", "verified")
                    self.client.set_terminated(run, "FINISHED")
                self.client.set_tag(self.parent, "status", "verified")
                self.client.set_terminated(self.parent, "FINISHED")
                self.terminal = True
                return str(self.parent)
        except BaseException:
            self.fail()
            raise
