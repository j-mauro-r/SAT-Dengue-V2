"""Strict read-only adapters and immutable Phase 1 publications; no model/tracking imports."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from kedro.io import AbstractDataset, DatasetError

from sat_dengue.data.exp_delta03 import KEYS, normalize

CONTRACT = "docs/product/experiments/EXP-DELTA03/phase1-contract.json"
ROOT = Path(__file__).resolve().parents[3]
CODE_FILES = [
    "src/sat_dengue/data/exp_delta03.py",
    "src/sat_dengue/data/exp_delta03_quality.py",
    "src/sat_dengue/data/exp_delta03_preparation.py",
    "src/sat_dengue/datasets/exp_delta03.py",
    "src/sat_dengue/pipelines/exp_delta03/pipeline.py",
    "src/sat_dengue/data/exp_delta03_reconciliation.py",
    "src/sat_dengue/data/exp_delta03_retrospective.py",
    "src/sat_dengue/experiments/onset.py",
    "src/sat_dengue/data/consolidation.py",
    "src/sat_dengue/configuration.py",
    "src/sat_dengue/settings.py",
    "src/sat_dengue/pipeline_registry.py",
    "conf/base/catalog.yml",
    "conf/base/parameters.yml",
]


def safe_path(root: Path, relative: str, prefix: str) -> Path:
    """Reject every symlink component, traversal and external/incorrect storage roots."""
    rel = Path(relative)
    if (
        rel.is_absolute()
        or ".." in rel.parts
        or not (relative == prefix or relative.startswith(prefix + "/"))
    ):
        raise ValueError("Unsafe or external path")
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Symlink is forbidden")
    if not current.resolve().is_relative_to(root.resolve()):
        raise ValueError("External path")
    return current


def identity(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return {
            "sha256": hashlib.file_digest(stream, "sha256").hexdigest(),
            "bytes": os.fstat(stream.fileno()).st_size,
        }


def admit(root: Path, contract: dict[str, Any], *, relative: str | None = None) -> dict[str, Any]:
    """Hash, parse and rehash the same open file; read-only identity and calendar admission."""
    source = contract["source"]
    name = relative or source["path"]
    if name != source["path"]:
        raise ValueError("Unexpected canonical source")
    path = safe_path(root, name, "data/sources/dataset_v3")
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != source["expected_sha256"] or before.st_size != source["expected_bytes"]:
            raise ValueError("Source identity mismatch")
        stream.seek(0)
        frame = pd.read_csv(
            stream, dtype={k: str for k in [*KEYS, "divipola_departamento"]}, low_memory=False
        )
        if list(frame) != contract["ordered_columns"] or len(frame) != source["expected_rows"]:
            raise ValueError("Schema or row count mismatch")
        # Actual on-disk format is strict month-start ISO; normalized data never overwrite it.
        if not frame.periodo_mes.str.fullmatch(r"\d{4}-\d{2}-01").all():
            raise ValueError("Unexpected source format")
        stream.seek(0)
        after = os.fstat(stream.fileno())
        if hashlib.file_digest(stream, "sha256").hexdigest() != digest or (
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError("Source changed during admission")
    if identity(path) != {"sha256": digest, "bytes": before.st_size}:
        raise ValueError("Source path substituted")
    numeric = {
        s
        for block, spec in contract.get("blocks", {}).items()
        for s in spec["sources"]
        if block != "CALENDAR"
        if s
        not in {
            "ndvi_disponible",
            "agua_superficial_disponible",
            "estado_cobertura_agua_superficial",
        }
    }
    numeric |= {"notificados_210", "notificados_220"}
    for name in numeric:
        converted = pd.to_numeric(frame[name], errors="coerce")
        if (frame[name].notna() & converted.isna()).any() or not np.isfinite(
            converted.dropna()
        ).all():
            raise ValueError("Invalid basic numeric field: " + name)
    normal = normalize(frame)
    if (
        normal.divipola_municipio.nunique() != source["expected_municipalities"]
        or normal.periodo_mes.nunique() != source["expected_months"]
    ):
        raise ValueError("Municipality/calendar coverage mismatch")
    if [normal.periodo_mes.min(), normal.periodo_mes.max()] != source["coverage"]:
        raise ValueError("Period coverage mismatch")
    if not {"50", "73"} <= set(normal.divipola_departamento):
        raise ValueError("Meta/Tolima missing")
    if len(normal) != source["expected_months"] * source["expected_municipalities"]:
        raise ValueError("Incomplete national grid")
    return {
        "frame": normal,
        "receipt": {
            "schema": "exp-delta03-admission-v1",
            "sha256": digest,
            "bytes": before.st_size,
            "rows": len(normal),
            "columns": len(frame.columns),
            "municipalities": int(normal.divipola_municipio.nunique()),
            "months": int(normal.periodo_mes.nunique()),
            "period": source["coverage"],
            "unique_key": KEYS,
            "source_preservation": "PASS",
            "execution": "not_authorized",
            "fits": 0,
            "calibrations": 0,
            "mlflow_writes": 0,
        },
    }


def canonical(payload: Any) -> bytes:
    return (
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
        + "\n"
    ).encode()


def publish(root: Path, relative: str, payloads: dict[str, bytes]) -> dict[str, Any]:
    """One atomic, content-addressed publication; identical verified repeats are read-only."""
    parent = safe_path(root, relative, "tmp/exp-delta03-phase1")
    parent.mkdir(parents=True, exist_ok=True)
    records = {
        name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        for name, data in sorted(payloads.items())
    }
    if any(Path(name).name != name or name == "manifest.json" for name in payloads):
        raise ValueError("Unsafe payload name")
    bundle = hashlib.sha256(canonical(records)).hexdigest()
    destination = safe_path(root, relative + "/" + bundle, "tmp/exp-delta03-phase1")
    manifest = canonical(
        {"schema": "exp-delta03-publication-v1", "bundle_id": bundle, "files": records}
    )
    complete = {**payloads, "manifest.json": manifest}
    if destination.exists():
        if not destination.is_dir() or {p.name for p in destination.iterdir()} != set(complete):
            raise ValueError("Existing publication inventory changed")
        for name, data in complete.items():
            file = safe_path(
                root, str((destination / name).relative_to(root)), "tmp/exp-delta03-phase1"
            )
            if file.read_bytes() != data:
                raise ValueError("Existing publication changed")
        return {
            "bundle_id": bundle,
            "path": str(destination.relative_to(root)),
            "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        }
    scratch = Path(tempfile.mkdtemp(prefix=".staging-", dir=parent))
    try:
        for name, data in complete.items():
            with (scratch / name).open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        # A simultaneous existing publication is never overwritten.
        os.rename(scratch, destination)
    finally:
        if scratch.exists():
            shutil.rmtree(scratch)
    return {
        "bundle_id": bundle,
        "path": str(destination.relative_to(root)),
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
    }


def frozen_frame(spec: dict[str, Any], name: str, records: dict[str, Any]) -> pd.DataFrame:
    """Admit an exact frozen payload through its independently pinned parent manifest."""
    folder = safe_path(ROOT, spec["root"], "data/processed")
    manifest_path = safe_path(ROOT, spec["root"] + "/manifest.json", "data/processed")
    manifest_identity = identity(manifest_path)
    if manifest_identity["sha256"] != spec["manifest_sha256"]:
        raise DatasetError("Frozen scientific manifest changed")
    manifest = json.loads(manifest_path.read_bytes())
    if identity(manifest_path) != manifest_identity:
        raise DatasetError("Frozen manifest substituted")
    records[str(manifest_path.relative_to(ROOT))] = manifest_identity
    expected = manifest["files"][name]
    path = safe_path(ROOT, str((folder / name).relative_to(ROOT)), "data/processed")
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        observed = {
            "sha256": hashlib.file_digest(stream, "sha256").hexdigest(),
            "bytes": before.st_size,
        }
        if observed != expected:
            raise DatasetError("Frozen scientific payload changed")
        stream.seek(0)
        if name.endswith(".csv"):
            value = pd.read_csv(
                stream,
                dtype={"municipality_code": str, "year_month": str},
                low_memory=False,
                float_precision="round_trip",
            )
        else:
            value = pd.DataFrame(json.loads(stream.read())["cells"])
        stream.seek(0)
        after = os.fstat(stream.fileno())
        if hashlib.file_digest(stream, "sha256").hexdigest() != observed["sha256"] or (
            before.st_ino,
            before.st_mtime_ns,
            before.st_size,
        ) != (after.st_ino, after.st_mtime_ns, after.st_size):
            raise DatasetError("Frozen payload changed during read")
    if identity(path) != observed:
        raise DatasetError("Frozen payload path substituted")
    records[str(path.relative_to(ROOT))] = observed
    return value


def retrospective_sources(contract: dict[str, Any]) -> dict[str, Any]:
    """Bind the explicitly approved historical target/cohorts; never open native models."""
    approval = contract["retrospective_preparation"]
    if (
        approval["status"] != "APPROVED"
        or approval["authority"] != "Mauricio"
        or approval["training_authorized"]
        or approval["operational_PIT"]
    ):
        raise DatasetError("Retrospective preparation scope is not approved")
    document = safe_path(ROOT, approval["document"], "docs/product/experiments/EXP-DELTA03")
    document_identity = identity(document)
    if document_identity["sha256"] != approval["document_sha256"]:
        raise DatasetError("Human preparation authority changed")
    records = {approval["document"]: document_identity}
    ledger_spec = contract["retrospective_source_ledger"]
    ledger_path = safe_path(ROOT, ledger_spec["path"], "docs/product/experiments/EXP-DELTA03")
    ledger_identity = identity(ledger_path)
    if ledger_identity["sha256"] != ledger_spec["sha256"]:
        raise DatasetError("Retrospective source ledger changed")
    ledger = json.loads(ledger_path.read_bytes())
    if ledger["operational_PIT_claim"] or ledger["authorization"] != approval:
        raise DatasetError("Source ledger exceeds human authorization")
    records[ledger_spec["path"]] = ledger_identity
    specs = contract["historical_sources"]
    national = frozen_frame(specs["national"], "canonical_model_table_national_v1.csv", records)
    baseline = frozen_frame(specs["regional"], "canonical_model_table_v1.csv", records)
    benchmark = frozen_frame(specs["benchmark"], "predictions.csv", records)
    controls = []
    g1_cells = frozen_frame(specs["G1"], "cells.json", records)
    for h in contract["horizons"]:
        for year in contract["evaluation_years"]:
            selected = frozen_frame(
                specs["recovered_selection"], f"selection-h{h}-{year}.csv", records
            )
            evaluated = benchmark.loc[
                benchmark.horizon.eq(h) & benchmark.year.eq(year) & benchmark.arm.eq("G0_OFF")
            ].copy()
            for role, frame in [("selection", selected), ("evaluation", evaluated)]:
                if frame.empty:
                    raise DatasetError("Missing complete historical control cell")
                controls.append(
                    {
                        "horizon": h,
                        "year": year,
                        "role": role,
                        "control": "G0",
                        "frame": frame.rename(columns={"onset_target": "truth"}),
                    }
                )
            for role in ["calibration", "selection", "evaluation"]:
                frame = frozen_frame(specs["G1"], f"scores-h{h}-{year}-{role}.csv", records)
                if frame.empty:
                    raise DatasetError("Missing frozen G1 cohort")
                controls.append(
                    {
                        "horizon": h,
                        "year": year,
                        "role": role,
                        "control": "G1",
                        "frame": frame.rename(columns={"onset_target": "truth"}),
                    }
                )
    return {
        "historical_panel": national,
        "baseline": baseline,
        "frozen_cohorts": controls,
        "vintage_ledger": ledger,
        "training_controls": g1_cells[["horizon", "year", "audit"]].to_dict("records"),
        "retrospective_verification": {
            "verified": True,
            "authority": document_identity,
            "records": records,
            "operational_PIT": False,
        },
    }


class Delta03SourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """No caller-selected inputs, scientific overrides or training actions."""

    def load(self) -> dict[str, Any]:
        path = safe_path(ROOT, CONTRACT, "docs/product/experiments/EXP-DELTA03")
        contract = json.loads(path.read_bytes())
        source = contract["source"]
        for name, digest in source["metadata_sha256"].items():
            file = safe_path(ROOT, "data/sources/dataset_v3/" + name, "data/sources/dataset_v3")
            if identity(file)["sha256"] != digest:
                raise DatasetError("Source metadata identity changed")
        with (ROOT / "data/sources/dataset_v3/v1.1.0_manifest.csv").open(
            newline=""
        ) as manifest_stream:
            entries = list(csv.DictReader(manifest_stream))
        primary = [entry for entry in entries if entry["tipo_artefacto"] == "producto_principal"]
        if len(primary) != 1:
            raise DatasetError("Ambiguous producer manifest")
        main = primary[0]
        if (
            main["ruta_relativa"] != source["producer_manifest_path"]
            or main["sha256"] != source["expected_sha256"]
            or int(main["tamano_bytes"]) != source["expected_bytes"]
            or int(main["filas"]) != source["expected_rows"]
            or int(main["columnas"]) != source["expected_columns"]
        ):
            raise DatasetError("Contradictory producer manifest identity")
        dictionary = list(
            csv.DictReader(
                io.StringIO(
                    (ROOT / "data/sources/dataset_v3/data_dictionary_v1.1.0.csv").read_text()
                )
            )
        )
        data = admit(ROOT, contract)
        data["code_records"] = {name: identity(ROOT / name) for name in CODE_FILES}
        data["frame"].attrs["source_sha256"] = data["receipt"]["sha256"]
        baseline_spec = contract["baseline"]
        baseline_root = safe_path(
            ROOT, baseline_spec["root"], "data/processed/canonical_model_table_v1"
        )
        if baseline_root.is_dir():
            manifest_path = safe_path(
                ROOT,
                str((baseline_root / "manifest.json").relative_to(ROOT)),
                "data/processed/canonical_model_table_v1",
            )
            if identity(manifest_path)["sha256"] != baseline_spec["manifest_sha256"]:
                raise DatasetError("Historical manifest changed")
            native = json.loads(manifest_path.read_bytes())
            panel = safe_path(
                ROOT,
                str((baseline_root / "canonical_model_table_v1.csv").relative_to(ROOT)),
                "data/processed/canonical_model_table_v1",
            )
            if identity(panel) != native["files"]["canonical_model_table_v1.csv"]:
                raise DatasetError("Historical table changed")
            data["baseline"] = pd.read_csv(
                panel,
                dtype={"municipality_code": str},
                usecols=[
                    "municipality_code",
                    "year_month",
                    "dengue_notifications_count",
                    "dengue_grave_notifications_count",
                ],
            )
        if contract.get("preparation_regime") == "RETROSPECTIVE_CONSOLIDATED":
            data.update(retrospective_sources(contract))
        return {
            **data,
            "contract": contract,
            "dictionary": dictionary,
            "contract_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Read-only source")

    def _describe(self) -> dict[str, Any]:
        return {"contract": CONTRACT, "access": "strict read-only"}


class Delta03PublicationDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        path = Path(filepath)
        relative = str(path.relative_to(ROOT)) if path.is_absolute() else filepath
        safe_path(ROOT, relative, "tmp/exp-delta03-phase1")
        self.filepath = relative

    def load(self) -> dict[str, Any]:
        raise DatasetError("Use the explicit immutable publication identity")

    def save(self, data: dict[str, Any]) -> None:
        publish(ROOT, self.filepath, data["payloads"])

    def _describe(self) -> dict[str, Any]:
        return {"filepath": self.filepath}


def preflight(sources: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.configuration import validate_parameters

    if validate_parameters(parameters) != {
        "profile": "exp_delta03_preflight",
        "tracking": "disabled",
    }:
        raise ValueError("Preflight requires its own disabled-tracking profile")
    return {
        "payloads": {
            "admission.json": canonical(sources["receipt"]),
            "provenance.json": canonical(
                {
                    "contract_sha256": sources["contract_sha256"],
                    "source_sha256": sources["receipt"]["sha256"],
                }
            ),
        }
    }


def analyze(
    sources: dict[str, Any], parameters: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    from sat_dengue.configuration import validate_parameters
    from sat_dengue.data.exp_delta03_preparation import quality

    if validate_parameters(parameters) != {
        "profile": "exp_delta03_preparation",
        "tracking": "disabled",
    }:
        raise ValueError("Preparation requires its own disabled-tracking profile")
    return sources, quality(sources)


def retrospective_payloads(sources: dict[str, Any], reports: dict[str, Any]) -> dict[str, bytes]:
    """Serialize a single shared matrix and verify actual CSV round trips before publication."""
    from sat_dengue.data.exp_delta03_retrospective import (
        prepare_retrospective,
        validate_materialized_tables,
    )

    prepared = prepare_retrospective(sources)
    payloads = {}
    for key, name in [
        ("base", "prepared_features.csv"),
        ("labels", "labels.csv"),
        ("memberships", "cohort_membership.csv"),
    ]:
        payloads[name] = (
            prepared[key]
            .to_csv(index=False, na_rep="", lineterminator="\n", float_format="%.17g")
            .encode()
        )
    types = {"divipola_municipio": str, "periodo_mes": str, "divipola_departamento": str}
    tables = [
        pd.read_csv(io.BytesIO(payloads[name]), dtype=types, float_precision="round_trip")
        for name in ["prepared_features.csv", "labels.csv", "cohort_membership.csv"]
    ]
    validation = validate_materialized_tables(
        tables[0], tables[1], tables[2], prepared["views"], prepared["feature_manifest"]
    )
    payloads.update(
        {
            "quality.json": canonical(reports),
            "transformations.json": canonical(prepared["feature_manifest"]),
            "matrices.json": canonical(
                {
                    "schema": "exp-delta03-retrospective-matrices-v1",
                    "layout": (
                        "one shared base; closed selectors and cell-specific reference columns"
                    ),
                    "base_file": "prepared_features.csv",
                    "labels_file": "labels.csv",
                    "cohort_file": "cohort_membership.csv",
                    "feature_contract": prepared["feature_manifest"],
                    "views": prepared["views"],
                    "validation": validation,
                    "availability_regime": prepared["availability_regime"],
                    "operational_PIT": False,
                }
            ),
            "cohort-parity.json": canonical(prepared["historical_parity"]),
            "vintage-ledger.json": canonical(sources["vintage_ledger"]),
            "cohort-key-hashes.json": canonical(
                {
                    "status": "FROZEN_AUTHORIZED_RETROSPECTIVE",
                    "views": [
                        {"id": v["id"], "status": v["status"], "roles": v["roles"]}
                        for v in prepared["views"]
                    ],
                    "operational_PIT": False,
                }
            ),
            "ndvi-references.json": canonical(prepared["references"]),
            "readiness.json": canonical(
                {
                    "scientific_preparation_ready": True,
                    "phase1_complete": False,
                    "completion_owner": "external reproduced readiness and final CI gates",
                    "matrix_files_published": 1,
                    "logical_views": validation["logical_views"],
                    "unsupported_water_views": validation["unavailable_water_views"],
                    "regime": "RETROSPECTIVE_CONSOLIDATED",
                    "operational_PIT": False,
                    "source_binding": (
                        "pinned historical V2 residence/INI_SIN/D2D3 source; no occurrence alias"
                    ),
                    "authorization": sources["contract"]["retrospective_preparation"],
                    "temporal": "original V2 cohorts/roles;2024 separate stress;2025 excluded",
                    "fits": 0,
                    "calibrations": 0,
                    "mlflow_writes": 0,
                }
            ),
            "leakage.json": canonical(
                {
                    "status": "PASS_EVENT_TIME_RETROSPECTIVE",
                    "no_operational_release_proof_claim": True,
                    "monthly_events": "T-1 or older; ONI central T-2 ends T-1",
                    "annual_events": "exact previous observation year; no missing-year replacement",
                    "history": (
                        "only historical source lags1,2,3,12; contemporaneous counts excluded"
                    ),
                    "references": (
                        "cell/population training only; transfer never learns target territories"
                    ),
                    "water": (
                        "genuine lagged observation <=2021-12; "
                        "Jan2022 may use Dec2021; no later fill"
                    ),
                    "MODIS": (
                        "four separate fractions; bare_other audit reference; "
                        "no mosaic redistribution"
                    ),
                    "target_columns_in_X": False,
                    "fits": 0,
                    "calibrations": 0,
                    "mlflow_writes": 0,
                }
            ),
        }
    )
    return payloads


def assemble(sources: dict[str, Any], reports: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.data.exp_delta03_preparation import prepare

    retrospective = sources["contract"].get("preparation_regime") == "RETROSPECTIVE_CONSOLIDATED"
    if retrospective:
        payloads = retrospective_payloads(sources, reports)
    else:
        result = prepare(sources, reports)
        payloads = {name + ".json": canonical(value) for name, value in result.items()}
    # Revalidate original inputs before making diagnostic products visible.
    if "contract_sha256" in sources:
        if (
            identity(
                safe_path(ROOT, sources["contract"]["source"]["path"], "data/sources/dataset_v3")
            )["sha256"]
            != sources["receipt"]["sha256"]
        ):
            raise ValueError("Source changed before publication")
    for name, expected in sources.get("code_records", {}).items():
        if identity(ROOT / name) != expected:
            raise ValueError("Implementation changed during preparation")
    for name, expected in sources.get("retrospective_verification", {}).get("records", {}).items():
        if identity(safe_path(ROOT, name, name.split("/")[0])) != expected:
            raise ValueError("Historical source or human authority changed during preparation")
    if (
        "contract_sha256" in sources
        and identity(ROOT / CONTRACT)["sha256"] != sources["contract_sha256"]
    ):
        raise ValueError("Preparation contract changed")
    payloads["admission.json"] = canonical(sources["receipt"])
    payloads["provenance.json"] = canonical(
        {
            "contract_sha256": sources.get("contract_sha256", "synthetic"),
            "source_sha256": sources["receipt"]["sha256"],
            "code": {name: identity(ROOT / name) for name in CODE_FILES},
            "historical_sources": sources.get("retrospective_verification", {}),
            "availability_regime": sources["contract"].get("preparation_regime", "STRICT_PIT"),
            "operational_PIT_claim": False,
        }
    )
    return {"payloads": payloads}


def load_retrospective_publication(relative: str, manifest_sha256: str) -> dict[str, Any]:
    """Explicit immutable matrix readback for verification/future read-only consumers."""
    from sat_dengue.data.exp_delta03_retrospective import validate_materialized_tables

    folder = safe_path(ROOT, relative, "tmp/exp-delta03-phase1/products")
    manifest_path = safe_path(ROOT, relative + "/manifest.json", "tmp/exp-delta03-phase1/products")
    if identity(manifest_path)["sha256"] != manifest_sha256:
        raise ValueError("Prepared matrix manifest changed")
    manifest = json.loads(manifest_path.read_bytes())
    if hashlib.sha256(canonical(manifest["files"])).hexdigest() != folder.name:
        raise ValueError("Prepared matrix content identity changed")
    for name, record in manifest["files"].items():
        if Path(name).name != name:
            raise ValueError("Unsafe prepared member")
        file = safe_path(ROOT, relative + "/" + name, "tmp/exp-delta03-phase1/products")
        if identity(file) != record:
            raise ValueError("Prepared matrix member changed")
    metadata = json.loads((folder / "matrices.json").read_bytes())
    types = {"divipola_municipio": str, "periodo_mes": str, "divipola_departamento": str}
    base, labels, members = [
        pd.read_csv(folder / name, dtype=types, float_precision="round_trip")
        for name in ["prepared_features.csv", "labels.csv", "cohort_membership.csv"]
    ]
    checked = validate_materialized_tables(
        base, labels, members, metadata["views"], metadata["feature_contract"]
    )
    return {
        "base": base,
        "labels": labels,
        "memberships": members,
        "metadata": metadata,
        "validation": checked,
        "manifest": manifest,
    }


def synthetic(parameters: dict[str, Any]) -> dict[str, Any]:
    """Generated-only probe; source loader and all private sources remain untouched."""
    from sat_dengue.configuration import validate_parameters
    from sat_dengue.data.exp_delta03 import h5_labels, historical_window

    if validate_parameters(parameters) != {
        "profile": "exp_delta03_synthetic",
        "tracking": "disabled",
    }:
        raise ValueError("Synthetic profile mismatch")
    frame = pd.DataFrame(
        {
            "divipola_municipio": ["05001"] * 96,
            "divipola_departamento": ["05"] * 96,
            "periodo_mes": pd.period_range("2007-01", "2014-12", freq="M").astype(str),
            "count": [1.0] * 95 + [10.0],
        }
    )
    frame = normalize(frame)
    labels = h5_labels(frame, frame["count"])
    window = historical_window(frame, "count", "mean")
    assert labels.onset_T1.notna().sum() > 0 and window.iloc[0] != window.iloc[0]
    return {
        "payloads": {
            "synthetic.json": canonical(
                {
                    "evidence": "generated_only",
                    "rows": len(frame),
                    "fits": 0,
                    "calibrations": 0,
                    "mlflow_writes": 0,
                    "labels_checked": True,
                    "history_checked": True,
                }
            )
        }
    }
