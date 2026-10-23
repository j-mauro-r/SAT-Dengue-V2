"""Strict, read-only comparators shared by synthetic CI and protected replay."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from cleanup_support import previous_engineering, verify_cleanup, verify_cleanup_originals

RTOL = 1e-8
ATOL = 1e-10
BASELINE_SHA256 = "d86338cd34dcde884e2be9d102271969d0f3b52f57b8ffdebd1829771977a5b3"
SCOPE_SHA256 = "5f16db6458a771fd2ee32197247b3331ecd5f57b148319e7ba99ba806cc9165f"
FINAL_ID = "768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35"
FINAL_PATH = Path("artifacts/model_final_evaluation") / FINAL_ID


def new_evidence_directory(stage: str) -> Path:
    """Allocate a fresh receipt directory; never overwrite another session's evidence."""
    root = Path(__file__).resolve().parents[2]
    relative = Path(
        os.environ.get(
            "SAT_DENGUE_VALIDATION_EVIDENCE_ROOT", "tmp/kedro-migration/validation-evidence"
        )
    )
    allowed_plan = Path(".dwp/plans/PLAN_030_kedro_architecture_migration/analysis_results")
    assert not relative.is_absolute() and ".." not in relative.parts
    assert relative.is_relative_to("tmp") or relative.is_relative_to(allowed_plan)
    assert stage and stage.replace("-", "").isalnum()
    target = root / relative / stage / uuid4().hex
    assert target.resolve().is_relative_to(root)
    assert not any(p.is_symlink() for p in (target, *target.parents))
    target.mkdir(parents=True, exist_ok=False)
    return target


def fingerprint(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise AssertionError(f"Required regular evidence file missing or symlinked: {path.name}")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"sha256": digest, "bytes": path.stat().st_size}


def safe_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise AssertionError("Unsafe evidence path")
    resolved = root / path
    if not resolved.resolve().is_relative_to(root.resolve()):
        raise AssertionError("Evidence escapes repository")
    return resolved


def require_records(root: Path, records: dict[str, Any]) -> int:
    if not records:
        raise AssertionError("Zero eligible evidence records")
    for relative, expected in records.items():
        if fingerprint(safe_path(root, relative)) != expected:
            raise AssertionError(f"Protected fingerprint mismatch: {relative}")
    return len(records)


METADATA_REVISION = "32f96a69521c24b1f9dc2117c1a31b2851d45d72"
METADATA_ORIGINALS = {
    "pyproject.toml": {
        "bytes": 1029,
        "sha256": "7814ce9485a506dd691d86dd8b99b6e61d94f5695579833744bdc5c7e43d8a3f",
    },
    "requirements-modeling.txt": {
        "bytes": 167,
        "sha256": "fa26f3fc467c81c64b95d02856ff1e9f3bc06cafb1d0761e448f3b79cd46729d",
    },
}


def verify_preservation_records(root: Path, records: dict[str, Any]) -> int:
    """Verify originals, every prior closed mapping and the separate cleanup overlay."""
    verify_cleanup(root)
    if not set(METADATA_ORIGINALS).issubset(records):
        return verify_data_preservation(root, records)
    ledger_path = root / "docs/operations/kedro-foundation-metadata.json"
    if not ledger_path.exists():
        return require_records(root, records)
    assert not ledger_path.is_symlink(), "Metadata ledger cannot be symlinked"
    ledger = json.loads(ledger_path.read_text())
    assert set(ledger) == {"schema", "original_revision", "baseline_sha256", "files"}
    assert ledger["schema"] == "kedro-foundation-metadata-v1"
    assert ledger["original_revision"] == METADATA_REVISION
    assert ledger["baseline_sha256"] == BASELINE_SHA256
    assert set(ledger["files"]) == set(METADATA_ORIGINALS), "Expanded metadata exception"
    for name, original in METADATA_ORIGINALS.items():
        entry = ledger["files"][name]
        assert set(entry) == {"original", "engineering"}
        assert records[name] == entry["original"] == original, "Original metadata identity changed"
        raw = subprocess.check_output(["git", "show", f"{METADATA_REVISION}:{name}"], cwd=root)
        assert {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} == original
        assert previous_engineering(root, name) == entry["engineering"], (
            f"Engineering metadata fingerprint mismatch: {name}"
        )
    others = {name: value for name, value in records.items() if name not in METADATA_ORIGINALS}
    return verify_data_preservation(root, others) + len(METADATA_ORIGINALS)


DATA_REVISION = "f837c9fa27dd2244307786156895794fc3158434"
DATA_ORIGINALS = {
    "scripts/stage2_consolidated_dataset_pipeline.py": {
        "bytes": 85188,
        "sha256": "749074cca6b6a9c79953a13153265c4da894223d5b79f3af61d00c7327a9bbde",
    },
    "scripts/validate_stage2_training_readiness.py": {
        "bytes": 96887,
        "sha256": "5c6397b3999f1f26dd169659a73ae3fd36cd5a9bdb6b20a5419edf230e297ddd",
    },
}


DATA_ENGINEERING = {
    "scripts/stage2_consolidated_dataset_pipeline.py": {
        "bytes": 332,
        "sha256": "d1cadfebfdc593b06e6381f693b3289d2c42961059cc744795e031097c8385da",
    },
    "scripts/validate_stage2_training_readiness.py": {
        "bytes": 328,
        "sha256": "99595441e56190b11264722ed4908d1bbd080b3acd5f170afcc0844e42cf0b78",
    },
}


def verify_data_preservation(root: Path, records: dict[str, Any]) -> int:
    ledger_path = root / "docs/operations/kedro-data-identities.json"
    if not set(DATA_ORIGINALS).issubset(records) or not ledger_path.exists():
        return verify_preparation_preservation(root, records)
    assert not ledger_path.is_symlink()
    ledger = json.loads(ledger_path.read_text())
    assert set(ledger) == {"schema", "original_revision", "baseline_sha256", "files"}
    assert ledger["schema"] == "kedro-data-migration-identities-v1"
    assert ledger["original_revision"] == DATA_REVISION
    assert ledger["baseline_sha256"] == BASELINE_SHA256
    assert set(ledger["files"]) == set(DATA_ORIGINALS), "Expanded Stage 2 preservation mapping"
    for name, original in DATA_ORIGINALS.items():
        entry = ledger["files"][name]
        assert set(entry) == {"original", "engineering"}
        assert records[name] == entry["original"] == original
        raw = subprocess.check_output(["git", "show", f"{DATA_REVISION}:{name}"], cwd=root)
        assert {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} == original
        assert previous_engineering(root, name) == entry["engineering"] == DATA_ENGINEERING[name], (
            "Stage 2 engineering identity mismatch"
        )
    remaining = {k: v for k, v in records.items() if k not in DATA_ORIGINALS}
    return (verify_preparation_preservation(root, remaining) if remaining else 0) + len(
        DATA_ORIGINALS
    )


def verify_native_bundle(bundle: Path) -> dict[str, Any]:
    manifest = json.loads((bundle / "manifest.json").read_text())
    files = manifest.get("files", {})
    require_records(bundle, files)
    if {p.name for p in bundle.iterdir()} != {*files, "manifest.json"}:
        raise AssertionError("Unexpected native bundle payload set")
    return manifest


def approved_scope(root: Path) -> dict[str, Any]:
    """Pinned implementation of Mauricio's PLAN_030 revision-2 exception boundary."""
    path = root / "docs/operations/kedro-baseline-scope.json"
    assert fingerprint(path)["sha256"] == SCOPE_SHA256, "Approved scope changed"
    return json.loads(path.read_text())


def source_records(identity: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (path, record["sha256"])
        for group in ("code", "stage4_code")
        for path, record in identity.get(group, {}).items()
        if isinstance(record, dict) and "sha256" in record
    }


def active_chain(root: Path, baseline: dict[str, Any], final: str) -> set[str]:
    """Derive dependencies from protected native identities, not coverage receipts."""
    records = {name: baseline["protected"][name] for name in baseline["bundles"]}
    require_records(root, records)
    index = {record["sha256"]: name for name, record in records.items()}
    assert len(index) == len(records), "Ambiguous manifest identity"
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        assert name in records, "Unknown dependency manifest"
        visited.add(name)
        identity = json.loads(safe_path(root, name).read_text()).get("identity", {})

        def dependencies(value: Any) -> None:
            if isinstance(value, dict):
                sha = value.get("sha256")
                if isinstance(sha, str) and sha in index:
                    visit(index[sha])
                for child in value.values():
                    dependencies(child)
            elif isinstance(value, list):
                for child in value:
                    dependencies(child)

        dependencies(identity)

    visit(final)
    return visited


def verify_source_scope(
    root: Path,
    baseline: dict[str, Any],
    recovered: set[tuple[str, str]],
    scope: dict[str, Any],
    coverage: dict[str, Any],
    *,
    final: str = str(FINAL_PATH / "manifest.json"),
) -> dict[str, Any]:
    chain = active_chain(root, baseline, final)
    assert sorted(chain) == scope["active_chain"], "Active dependency chain changed"
    by_bundle = {
        name: source_records(json.loads(safe_path(root, name).read_text()).get("identity", {}))
        for name in baseline["bundles"]
    }
    required = set().union(*by_bundle.values())
    active_required = set().union(*(by_bundle[name] for name in chain))
    assert active_required, "Zero eligible active source comparisons"
    assert not active_required - recovered, "Missing active source"
    missing = required - recovered
    exceptions = {(r["path"], r["sha256"]) for r in scope["historical_only_missing"]}
    assert len(exceptions) == len(scope["historical_only_missing"]), "Duplicate exception"
    assert missing == exceptions, "Closed historical source exceptions changed"
    affected = {name for name, records in by_bundle.items() if records & exceptions}
    assert affected == set(scope["historical_bundles"]), "Affected historical bundles changed"
    assert not affected & chain, "Unverified historical bundle used for equivalence"
    for name in affected:
        assert scope["historical_bundles"][name] == {
            "action": "KEEP",
            "source_status": "UNVERIFIED",
            "equivalence_evidence": False,
            "modification_allowed": False,
            "manifest": baseline["protected"][name],
        }, "Historical bundle must remain immutable KEEP / UNVERIFIED"
    observed = {
        "active_chain": sorted(chain),
        "active_missing": [],
        "historical_only_missing": [{"path": p, "sha256": s} for p, s in sorted(missing)],
    }
    assert coverage == observed, "Source coverage receipt disagrees with reconstructed evidence"
    assert scope["active_missing"] == [], "Approved active_missing must remain empty"
    verify_equivalence_scope(scope, {**scope, "equivalence_bundles": sorted(chain)})
    return observed


def verify_equivalence_scope(scope: dict[str, Any], report: dict[str, Any]) -> None:
    assert report["equivalence_bundles"] == scope["active_chain"], (
        "Equivalence must use exactly the approved active chain"
    )
    assert report["full_historical_reproducibility"] is False, (
        "Full historical reproducibility cannot be claimed"
    )
    assert report["G5"] == "NOT_APPROVED" and report["champion"] == "not_selected"
    assert report["consumed_2025"] is True
    assert report["allow_2025_selection_tuning_training"] is False
    assert report["new_real_fits"] == 0


def verify_protected_inventory(root: Path, baseline: dict[str, Any]) -> dict[str, Any]:
    """Independent disk scan: catches rename/unlink/native writes beyond open hooks."""
    records = baseline["protected"]
    count = verify_preservation_records(root, records)
    for name, original in baseline["bundles"].items():
        bundle = safe_path(root, name).parent
        prefix = str(Path(name).parent) + "/"
        expected = {p.removeprefix(prefix) for p in records if p.startswith(prefix)}
        expected_entries = expected | {
            str(parent) for path in expected for parent in Path(path).parents if parent != Path(".")
        }
        entries = list(bundle.rglob("*"))
        assert not bundle.is_symlink() and not any(p.is_symlink() for p in entries)
        assert {str(p.relative_to(bundle)) for p in entries} == expected_entries, (
            f"Protected bundle membership changed: {name}"
        )
        manifest = json.loads(safe_path(root, name).read_text())
        assert manifest["bundle_id"] == original["bundle_id"], "Bundle identity changed"
        assert fingerprint(safe_path(root, name)) == original["manifest"], (
            "Protected manifest identity changed"
        )
    return {
        "status": "PASS",
        "protected_files": count,
        "protected_bytes": sum(r["bytes"] for r in records.values()),
        "bundles": len(baseline["bundles"]),
        "baseline_sha256": BASELINE_SHA256,
        "method": "independent file/Git-blob hashes and exact native bundle membership/identity",
        "metadata_git_objects": (
            len(METADATA_ORIGINALS)
            if set(METADATA_ORIGINALS).issubset(records)
            and (root / "docs/operations/kedro-foundation-metadata.json").exists()
            else 0
        ),
    }


def compare_frames(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    *,
    numeric: tuple[str, ...] = (),
    exact_numeric: bool = False,
) -> None:
    """Require the full ordered cohort and masks; only declared floats use tolerance."""
    if expected.empty or actual.empty:
        raise AssertionError("Zero eligible comparison rows")
    pd.testing.assert_index_equal(expected.index, actual.index, exact=True)
    pd.testing.assert_index_equal(expected.columns, actual.columns, exact=True)
    if not set(numeric).issubset(expected.columns):
        raise AssertionError("Unknown numeric comparison column")
    pd.testing.assert_frame_equal(expected.isna(), actual.isna(), check_exact=True)
    for name in expected.columns:
        if name in numeric:
            left = expected[name].to_numpy(dtype=float, na_value=np.nan)
            right = actual[name].to_numpy(dtype=float, na_value=np.nan)
            if np.isinf(left).any() or np.isinf(right).any():
                raise AssertionError("Infinite numeric evidence")
            np.testing.assert_allclose(
                right,
                left,
                rtol=0 if exact_numeric else RTOL,
                atol=0 if exact_numeric else ATOL,
                equal_nan=True,
            )
        else:
            pd.testing.assert_series_equal(expected[name], actual[name], check_exact=True)


PREPARATION_MAPPING: dict[str, Any] = {
    "schema": "kedro-preparation-migration-identities-v1",
    "original_revision": "925a784eb20d082efd7e166ab1b6fa35c8505a57",
    "baseline_sha256": "d86338cd34dcde884e2be9d102271969d0f3b52f57b8ffdebd1829771977a5b3",
    "files": {
        "scripts/training_preparation/audit.py": {
            "original": {
                "bytes": 1132,
                "sha256": "0d6636db2d5805e1a0f41f799aaad17bfc58571b66941f565cf9e147fcaa8630",
            },
            "engineering": {
                "bytes": 409,
                "sha256": "1007c9493052d659a6add36eac5e7826409f71928ea2b0ad4bf3892e52371c71",
            },
        },
        "scripts/training_preparation/contract.py": {
            "original": {
                "bytes": 2497,
                "sha256": "0c06b08533f19d35226081212e1c692e939255a0ca410e70dc3a908582e72c69",
            },
            "engineering": {
                "bytes": 348,
                "sha256": "f058595ce782a3fdf1856d178ebb716751c231896e7fe3ab8cb70cdf60066271",
            },
        },
        "scripts/training_preparation/development.py": {
            "original": {
                "bytes": 9137,
                "sha256": "3a811d9e1e8c3b17bcfca5e31ca4260ce40ca3ce0ba5f33908f896e2f09333d0",
            },
            "engineering": {
                "bytes": 481,
                "sha256": "93d32a255623975c5bab6bed97a3ab3d0e7e3e37e6dc7c4719d8dbde69ce5067",
            },
        },
        "scripts/training_preparation/eligibility.py": {
            "original": {
                "bytes": 4521,
                "sha256": "84057f911069f7d3d2184f6c49d64fd1eba61b614c0bfeaaa8ea82dfdb568f80",
            },
            "engineering": {
                "bytes": 351,
                "sha256": "853cca564f5749c38706914bee1edca87247ecaef19c3fd3ee4b0f7698b5eb9e",
            },
        },
        "scripts/training_preparation/features.py": {
            "original": {
                "bytes": 3809,
                "sha256": "b3f711dde9ea81f2bddd700bc9f202eefda21003b494be796a23d0ef216913a3",
            },
            "engineering": {
                "bytes": 341,
                "sha256": "97d097173dee769cf375ec9b0281743bc25b8b326089b2f6297cd3627ef19b1a",
            },
        },
        "scripts/training_preparation/notebook_execution.py": {
            "original": {
                "bytes": 7489,
                "sha256": "b4c9a73552a3f99c5881e279529d1b95563d4577a5850fa96552b37a3ebb2e3f",
            },
            "engineering": {
                "bytes": 428,
                "sha256": "85e360b7528de93b40c0564a5cbc0a5d1ac88e5aefaf32bc69a45e7aad2325c0",
            },
        },
        "scripts/training_preparation/persistence.py": {
            "original": {
                "bytes": 3815,
                "sha256": "4afb06c775463017816fdfdbe5bcdc7a7bf16d4d96571301a1c292d05a98a78d",
            },
            "engineering": {
                "bytes": 351,
                "sha256": "82e7eb635c374cfa17b0716687d407f450b8803ce67e63e4a658a2de40f4090a",
            },
        },
        "scripts/training_preparation/pipeline.py": {
            "original": {
                "bytes": 7089,
                "sha256": "820fe8ac7a0e3273262118280096fea5fbe89ae4a6b5bd192bd7b6f2c4bbd2af",
            },
            "engineering": {
                "bytes": 348,
                "sha256": "fb608a70e39a185862e0395047cf11e656cf5a7f87d6de6784c063f838d58e90",
            },
        },
        "scripts/training_preparation/preprocessing.py": {
            "original": {
                "bytes": 8842,
                "sha256": "e1dcb70370cb16718ee048a47092558b3ad992830c23e5ae26cc4bd0eabcd011",
            },
            "engineering": {
                "bytes": 346,
                "sha256": "0d2f14b823b6e204db72c9d420fea8e74e00d8e754b61cbdf95d65e429bd31a9",
            },
        },
        "scripts/training_preparation/temporal.py": {
            "original": {
                "bytes": 18994,
                "sha256": "0d417e1ee2da487f4953b5d5b19cfc6b60dbf5b305c534098d7cd9c793448279",
            },
            "engineering": {
                "bytes": 478,
                "sha256": "9bc63fc3cb57aa715ad46e0f89431e0fcbf63a32ca96b3d946d9187438a5d9cd",
            },
        },
        "scripts/training_preparation/validation.py": {
            "original": {
                "bytes": 10451,
                "sha256": "623b88797eed4352d70640c07a91bd81d44972438209f164afad5d0142901963",
            },
            "engineering": {
                "bytes": 343,
                "sha256": "711c61ebbe414d12aca65e1270f35dfc4b166b043cbf663ef8e5a5a32857e84f",
            },
        },
        "docs/product/stage-3/README.md": {
            "original": {
                "bytes": 13046,
                "sha256": "2bfefaed8ba0437e12548ec25049820e7a0e665dd79e63182d3954db15792f12",
            },
            "engineering": {
                "bytes": 6905,
                "sha256": "f62247001f959779b46573878dea81d433e93929d3305e27960f795c78562d00",
            },
        },
    },
}


def verify_preparation_preservation(root: Path, records: dict[str, Any]) -> int:
    path = root / "docs/operations/kedro-preparation-identities.json"
    files = PREPARATION_MAPPING["files"]
    mapped = set(files).intersection(records)
    if not mapped or not path.exists():
        return verify_training_preservation(root, records)
    assert not path.is_symlink()
    assert json.loads(path.read_text()) == PREPARATION_MAPPING, "Closed preparation mapping changed"
    for name in sorted(mapped):
        entry = files[name]
        assert records[name] == entry["original"]
        raw = subprocess.check_output(
            ["git", "show", f"{PREPARATION_MAPPING['original_revision']}:{name}"], cwd=root
        )
        assert {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} == entry["original"]
        assert previous_engineering(root, name) == entry["engineering"]
    remaining = {n: r for n, r in records.items() if n not in files}
    return (verify_training_preservation(root, remaining) if remaining else 0) + len(mapped)


TRAINING_MAPPING: dict[str, Any] = {
    "schema": "kedro-training-migration-identities-v1",
    "original_revision": "4e9c47025c73297ca066a8f2874bb94046fc7e4b",
    "baseline_sha256": "d86338cd34dcde884e2be9d102271969d0f3b52f57b8ffdebd1829771977a5b3",
    "files": {
        "scripts/model_training/__init__.py": {
            "original": {
                "bytes": 430,
                "sha256": "fabdddfe02fe58d741d2915f4431399ae44f8f14f5675b346d81e7ba5c657b99",
            },
            "engineering": {
                "bytes": 538,
                "sha256": "e84acdbffc04664cd071a4b1aeee2d4362d9c7b41e16d53b47dd2870a906a0e2",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_training/contract.py",
                "src/sat_dengue/datasets/legacy_training/pipeline.py",
            ],
        },
        "scripts/model_training/candidate_families.py": {
            "original": {
                "bytes": 4451,
                "sha256": "f7300e0b7b69cdeabbedfe515cc94d6b20afeaa7b3327b63f9974c84f3a48846",
            },
            "engineering": {
                "bytes": 292,
                "sha256": "7c5373f60b4889368300d24a0aa945a0f6a394dab4f3668dbb09bf4aa2f2fa0a",
            },
            "destination": ["src/sat_dengue/model_training/candidate_families.py"],
        },
        "scripts/model_training/candidate_notebook.py": {
            "original": {
                "bytes": 2839,
                "sha256": "bfaa8a81649d802c5210710baca4f90e8edb905134cddeddeb2fa475cc687066",
            },
            "engineering": {
                "bytes": 358,
                "sha256": "92a9912b7f0da693dbf1a43a31759174303341dfe3ae3f89f4cda5a9982c181b",
            },
            "destination": ["src/sat_dengue/datasets/legacy_training/candidate_notebook.py"],
        },
        "scripts/model_training/candidate_preparation.py": {
            "original": {
                "bytes": 3142,
                "sha256": "6b25b623432e1892666f16025dcf6661dc65103d1241bf2f43b8728cfbd22a16",
            },
            "engineering": {
                "bytes": 295,
                "sha256": "417b642c45f16c517c6c701ba24e8365f150bba703911a86e3c5fe75a77ab746",
            },
            "destination": ["src/sat_dengue/model_training/candidate_preparation.py"],
        },
        "scripts/model_training/candidate_selection.py": {
            "original": {
                "bytes": 8093,
                "sha256": "7359055290595a18158f3f3c5cf73981eb9344e6f7bd7fdbf48764000464a1a8",
            },
            "engineering": {
                "bytes": 293,
                "sha256": "2554a307d8f6db09b2c332dedf981227dfcd486f2ccd1e571916125aec772d1e",
            },
            "destination": ["src/sat_dengue/model_training/candidate_selection.py"],
        },
        "scripts/model_training/candidate_suite.py": {
            "original": {
                "bytes": 8647,
                "sha256": "613bd50bd6abfe5ba563e313bcd11f7e3eb53a9f63468db2ab69a4f96f6ba3e5",
            },
            "engineering": {
                "bytes": 299,
                "sha256": "b5fbaf2d38ef961ef3a1300f700353722e5456da1ca5a5013f8790ba71fc1430",
            },
            "destination": ["src/sat_dengue/datasets/legacy_training/candidate_suite.py"],
        },
        "scripts/model_training/candidates.py": {
            "original": {
                "bytes": 19310,
                "sha256": "1f1621a9c9898377964aac304a031e86a2028c8c0720634600bcef21ea9aed18",
            },
            "engineering": {
                "bytes": 294,
                "sha256": "55ecd06fc2598633e51c1aba2843364acd1e43ff13b9906ebe84495a19b5b5ef",
            },
            "destination": ["src/sat_dengue/datasets/legacy_training/candidates.py"],
        },
        "scripts/model_training/contract.py": {
            "original": {
                "bytes": 2533,
                "sha256": "effb123129401724da4268949869f36499bd12b925736a48317c3550de720d26",
            },
            "engineering": {
                "bytes": 292,
                "sha256": "80a9a148396c8c665e1d3e8e8c60fecab6f003d6c5ca4e0e5e2106f921b784bd",
            },
            "destination": ["src/sat_dengue/datasets/legacy_training/contract.py"],
        },
        "scripts/model_training/events.py": {
            "original": {
                "bytes": 5905,
                "sha256": "e99fadf26df301a59f2d3b372fff333e3d66c0c03786edf492dc77082507535b",
            },
            "engineering": {
                "bytes": 290,
                "sha256": "a697f90c7bd7f040e5c3d9d427c353b50e35680462e7555dc56834de1ec20683",
            },
            "destination": ["src/sat_dengue/datasets/legacy_training/events.py"],
        },
        "scripts/model_training/execution.py": {
            "original": {
                "bytes": 955,
                "sha256": "5652d9b0c64dbadc0f060a74b4703a6b2d676cfa5f3b946bbfccf41eb1f2e6f4",
            },
            "engineering": {
                "bytes": 349,
                "sha256": "232aaf2ddc95ea4b7ecbc304a61c0bd6fb8b2b3d2abac34d62ba736cd4833d33",
            },
            "destination": ["src/sat_dengue/datasets/legacy_training/execution.py"],
        },
        "scripts/model_training/gam_adapter.py": {
            "original": {
                "bytes": 6401,
                "sha256": "9e77bffe0a81b3a9e25a7a216708ea4942700248eba7c83867d15a8bc7e51d26",
            },
            "engineering": {
                "bytes": 285,
                "sha256": "d6fdbc521c7a260a2c7f3a9bad0a465375ec8bdb9465861fda8d03bf9f8f31ea",
            },
            "destination": ["src/sat_dengue/model_training/gam_adapter.py"],
        },
        "scripts/model_training/lightgbm_adapter.py": {
            "original": {
                "bytes": 3108,
                "sha256": "5668c13aaa72ffeabdf8e34be1cf6e54c10e4dd8fa5cf645d426bb548b5f501e",
            },
            "engineering": {
                "bytes": 290,
                "sha256": "38fb0c0ade443e0b75808448e71f16eaff400b41d2942de371d0a395eff95a19",
            },
            "destination": ["src/sat_dengue/model_training/lightgbm_adapter.py"],
        },
        "scripts/model_training/loading.py": {
            "original": {
                "bytes": 8737,
                "sha256": "5554737ad0caea09709191c4958ee181430b2b60b2cada50dab0dc75217af5ff",
            },
            "engineering": {
                "bytes": 291,
                "sha256": "945cd9d9847e11874218f3301c8bb27ad88e7247fd98552c6bbfd45e46cdda4f",
            },
            "destination": ["src/sat_dengue/datasets/legacy_training/loading.py"],
        },
        "scripts/model_training/metrics.py": {
            "original": {
                "bytes": 10612,
                "sha256": "589c73661fd0969662e08a5bdbb8fe0dd5ced87aaf8881a842f98f9fd9091e42",
            },
            "engineering": {
                "bytes": 266,
                "sha256": "2e100a412a8405417c0bcc66369c4babbb50b841b52b6f029f12e7912a06d2f7",
            },
            "destination": ["src/sat_dengue/metrics.py"],
        },
        "scripts/model_training/notebook_execution.py": {
            "original": {
                "bytes": 7427,
                "sha256": "76be2f2e5ef673d49c59bb41bc6cbf5f3300ab0307a74e4b2f5ae98851c5c028",
            },
            "engineering": {
                "bytes": 358,
                "sha256": "6c1016a5e1eda35086f691f20ac93071d1537bbc506d8497ace735e05e9d9bbf",
            },
            "destination": ["src/sat_dengue/datasets/legacy_training/notebook_execution.py"],
        },
        "scripts/model_training/persistence.py": {
            "original": {
                "bytes": 1375,
                "sha256": "c7c5742e6e6fe36afdc5cd31913d76aaeedc056d6be2587fd6e2b28c6094fec6",
            },
            "engineering": {
                "bytes": 295,
                "sha256": "496a16f59faefc2bd7818eeb26b01df52cd163dc4503bb85df7b3893c4563f83",
            },
            "destination": ["src/sat_dengue/datasets/legacy_training/persistence.py"],
        },
        "scripts/model_training/pipeline.py": {
            "original": {
                "bytes": 11325,
                "sha256": "4d3fb73f2cc42185958b53ceb785700bc384a5a58cb61b8085645c7f35b38570",
            },
            "engineering": {
                "bytes": 292,
                "sha256": "899f946dfd12b91efc565d2c4ed1f391c11f647505128366ef6a8c4ef1dd427a",
            },
            "destination": ["src/sat_dengue/datasets/legacy_training/pipeline.py"],
        },
        "scripts/model_training/references.py": {
            "original": {
                "bytes": 3941,
                "sha256": "e6434f0cdc069e1f22380a8d9176865e0dfc7b4cba750defe10f4a786baf4445",
            },
            "engineering": {
                "bytes": 284,
                "sha256": "ac5f54838d68c4b7909f9aca98fcbb529c33e5526e8bd13f68c7d405a238e5eb",
            },
            "destination": ["src/sat_dengue/model_training/references.py"],
        },
        "scripts/model_training/xgboost_adapter.py": {
            "original": {
                "bytes": 3643,
                "sha256": "7c6973e5dbcad0531fa11da410c8b2962895670ef0d92d72b7820b19c8f29a91",
            },
            "engineering": {
                "bytes": 289,
                "sha256": "7b75a59e6f1b1444bdec8576da9b2969f4cd7f2add6124454523bd6b0fd874d4",
            },
            "destination": ["src/sat_dengue/model_training/xgboost_adapter.py"],
        },
        "scripts/evaluation_metrics.py": {
            "original": {
                "bytes": 3427,
                "sha256": "b377152e72f24dd6a30f9400412b2c919c9365a6a630642fc5b02f716d2712f0",
            },
            "engineering": {
                "bytes": 230,
                "sha256": "66b8c608f5e1932455095610387ddaf6341619164a4fd7a395f2253464051049",
            },
            "destination": ["src/sat_dengue/metrics.py"],
        },
        "docs/product/stage-4/README.md": {
            "original": {
                "bytes": 29809,
                "sha256": "36ea94b315847ac936e7debefe171046bc29676cf8cca82ef1ad2c2d3ecc936f",
            },
            "engineering": {
                "bytes": 6664,
                "sha256": "aba8bc153ada82f2b6ac05098e2656f61a1a948ed8c05d589e5dbcf26faec634",
            },
            "destination": ["docs/product/stage-4/README.md"],
        },
    },
}


def verify_training_preservation(root: Path, records: dict[str, Any]) -> int:
    path = root / "docs/operations/kedro-training-identities.json"
    files = TRAINING_MAPPING["files"]
    mapped = set(files).intersection(records)
    if not mapped or not path.exists():
        return verify_evaluation_preservation(root, records)
    assert not path.is_symlink()
    assert json.loads(path.read_text()) == TRAINING_MAPPING, "Closed training mapping changed"
    for name in sorted(mapped):
        entry = files[name]
        assert records[name] == entry["original"]
        raw = subprocess.check_output(
            ["git", "show", f"{TRAINING_MAPPING['original_revision']}:{name}"], cwd=root
        )
        assert {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} == entry["original"]
        assert previous_engineering(root, name) == entry["engineering"]
        assert all(safe_path(root, destination).is_file() for destination in entry["destination"])
    remaining = {n: r for n, r in records.items() if n not in files}
    return (verify_evaluation_preservation(root, remaining) if remaining else 0) + len(mapped)


EVALUATION_MAPPING: dict[str, Any] = {
    "schema": "kedro-evaluation-migration-identities-v1",
    "original_revision": "5e16166d17ed8c8db935756ac269d69de28de376",
    "baseline_sha256": "d86338cd34dcde884e2be9d102271969d0f3b52f57b8ffdebd1829771977a5b3",
    "files": {
        "docs/product/stage-5/README.md": {
            "original": {
                "sha256": "e34b6a99f43969e9180907ee5d86b7973522c8f3a3f487bb88616d3b298fe85a",
                "bytes": 30192,
            },
            "engineering": {
                "bytes": 35157,
                "sha256": "fad1d18765c7d02d7eb145681fb022c14f6ffb0aefc25096dbc1cac4c6db9b52",
            },
            "destination": ["docs/product/stage-5/README.md"],
        },
        "scripts/final_evaluation/__init__.py": {
            "original": {
                "sha256": "f1695c497c10eec50d32d991b771290bc87a48a54e425b2029f7c8dc5c8c9238",
                "bytes": 72,
            },
            "engineering": {
                "bytes": 300,
                "sha256": "a3bf54be98cafdaeb93e6714de6dd9cc0fde6cf9fbafc31caa5c094468284aa4",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/final_evaluation/__init__.py"
            ],
        },
        "scripts/final_evaluation/cohorts.py": {
            "original": {
                "sha256": "3630f1e8cdf6766c277a836aeb903e66d9e429975be870892527c6419a4b9ccf",
                "bytes": 9975,
            },
            "engineering": {
                "bytes": 314,
                "sha256": "606a131511a52600042137fe830c57453bbb8b628058a3893d07a5f811135f39",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/final_evaluation/cohorts.py",
                "src/sat_dengue/final_evaluation/cohorts.py",
            ],
        },
        "scripts/final_evaluation/evaluation.py": {
            "original": {
                "sha256": "c6228d971a0e5ba0b04f6c82bbcdd64563d9127ae951d11b97a5026cf37e2780",
                "bytes": 10637,
            },
            "engineering": {
                "bytes": 317,
                "sha256": "6f12536c138589cbbd82c210e779620af0621e78d14d6d1e4a6462987a0095d6",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/final_evaluation/evaluation.py",
                "src/sat_dengue/final_evaluation/evaluation.py",
            ],
        },
        "scripts/final_evaluation/execution.py": {
            "original": {
                "sha256": "2f585d8aa20d93846264086c6aaa120e81c78b092ecb89603e3c69328b1f2a41",
                "bytes": 4117,
            },
            "engineering": {
                "bytes": 372,
                "sha256": "58f575183b7ac5713266456a6c728d39105fd1dbc2d5848bd134b3b44ef58b89",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/final_evaluation/execution.py",
                "src/sat_dengue/datasets/evaluation_cli.py",
            ],
        },
        "scripts/final_evaluation/pipeline.py": {
            "original": {
                "sha256": "e57435682733ddb0665e0093ccfee4fb31941f328f9fbd032329c9e176e2da01",
                "bytes": 16254,
            },
            "engineering": {
                "bytes": 315,
                "sha256": "7dc8559b04be4e3d82535bcb43985e128af8742e57e269add323095a53197bb7",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/final_evaluation/pipeline.py",
                "src/sat_dengue/final_evaluation/prediction.py",
            ],
        },
        "scripts/final_evaluation/protocol.py": {
            "original": {
                "sha256": "27aa4736f3d11e96b182043ceded8abedebae829404dff940dbccbb3b7dc29e2",
                "bytes": 6001,
            },
            "engineering": {
                "bytes": 315,
                "sha256": "183b8dcb6c15fc1b3b0451b6a2a849ec6d7f9232a66e05ce8f171bb054209c7e",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/final_evaluation/protocol.py"
            ],
        },
        "scripts/model_assessment/__init__.py": {
            "original": {
                "sha256": "536c51c7e4f21ca8c0b19c2a2106db36a85de9d7235462e2bfa2d4829f7313e8",
                "bytes": 80,
            },
            "engineering": {
                "bytes": 300,
                "sha256": "cb3809ced0fd1d6e815d9d3ec84defbcced01fabb4f86d6a61e755ae9d448d0d",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_assessment/__init__.py"
            ],
        },
        "scripts/model_assessment/comparison.py": {
            "original": {
                "sha256": "635b115501b8fa091b4f356309ad5dcc76c5d3fdd84a711f57eb168036479c4a",
                "bytes": 4877,
            },
            "engineering": {
                "bytes": 317,
                "sha256": "0f10214f5d6a8f9d81d23917a07b5cc8e52c1d138737c757c82c92ae05de52e0",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_assessment/comparison.py",
                "src/sat_dengue/model_assessment/comparison.py",
            ],
        },
        "scripts/model_assessment/execution.py": {
            "original": {
                "sha256": "77f98936b48ace75f235026c3fc362ea75f284cb776332273d526ef7332eb6f7",
                "bytes": 3379,
            },
            "engineering": {
                "bytes": 372,
                "sha256": "c5fdaf63dbe6990b2a5a3702bd2c1c55148e03143e2c303d05183abee31b7fdf",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_assessment/execution.py",
                "src/sat_dengue/datasets/evaluation_cli.py",
            ],
        },
        "scripts/model_assessment/input_validation.py": {
            "original": {
                "sha256": "27c8c3d2ca3ade77d2022974b3733957e15f200135b1e0e86d81d55b6025c8f5",
                "bytes": 3847,
            },
            "engineering": {
                "bytes": 323,
                "sha256": "313c02e71841d47f401fe81d2d6885316ee9878dc92dfc19a4581c5c2f0d42a2",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_assessment/input_validation.py"
            ],
        },
        "scripts/model_assessment/loading.py": {
            "original": {
                "sha256": "45143718a2ccade0dddc3c52a7324ec31b270a42eb5b5b70b9a2abb080957154",
                "bytes": 6945,
            },
            "engineering": {
                "bytes": 314,
                "sha256": "60f12d6d537ceb6b1fccedea50fd8adaefa3d4fc1e97054f58daf3d1f3206934",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_assessment/loading.py",
                "src/sat_dengue/model_assessment/workflow.py",
            ],
        },
        "scripts/model_assessment/pipeline.py": {
            "original": {
                "sha256": "5edc04cd1077a7ba80ecd0179168d1c70ee4a04e9f2f368b3ed27b42daf56f2e",
                "bytes": 5845,
            },
            "engineering": {
                "bytes": 315,
                "sha256": "eabf1f40355258228c69ab5f884a42165c27db7bbfa09d84bafb9ea0e181f34b",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_assessment/pipeline.py"
            ],
        },
        "scripts/model_assessment/policy.py": {
            "original": {
                "sha256": "79ea9220fa79551d96428ad84434fe8d5abaa1fe61552f07db7c61489d0c597d",
                "bytes": 4207,
            },
            "engineering": {
                "bytes": 313,
                "sha256": "1667ca01e6dfe131886896e471fe15090f3ff61f3f026c30662f5812a0586bc0",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_assessment/policy.py",
                "src/sat_dengue/model_assessment/policy.py",
            ],
        },
        "scripts/model_assessment/proposal.py": {
            "original": {
                "sha256": "2e4cc21ed0fceb0e8654e4f4dabb852cef35cd8a82905bf95f0c58cf021b9cc5",
                "bytes": 6475,
            },
            "engineering": {
                "bytes": 315,
                "sha256": "1ce7ba589a683d3af877d3eae9a33f03c431df7abfa07fdd75bc9c048da96d74",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_assessment/proposal.py"
            ],
        },
        "scripts/model_evaluation/__init__.py": {
            "original": {
                "sha256": "1df83b4efd4c17e812c067cd60cbe0ac38de8d7658b8d7c256f75a7ba6261515",
                "bytes": 476,
            },
            "engineering": {
                "bytes": 300,
                "sha256": "2f0a812a1aec0be3a3979dfb2cc729e2c6a44467a31d43c32eb2f55310944988",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_evaluation/__init__.py"
            ],
        },
        "scripts/model_evaluation/availability.py": {
            "original": {
                "sha256": "bf5761effaf0ec8b881523a1590fe681f5137d5285798ecbf71c2a8f26cf6a71",
                "bytes": 7058,
            },
            "engineering": {
                "bytes": 319,
                "sha256": "a890d87605f390a98c760e4b3da1b5b0f35de96ae6b2b8aa3d9d4740907da01e",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_evaluation/availability.py",
                "src/sat_dengue/model_evaluation/availability.py",
            ],
        },
        "scripts/model_evaluation/contract.py": {
            "original": {
                "sha256": "5eba463708c096618186c991e0f2a7882d7d7f6bb857fe30d13b9a203d1c1f3e",
                "bytes": 10324,
            },
            "engineering": {
                "bytes": 315,
                "sha256": "437a1c18fe5e4ad960ad56fd343f74c266bd6c422dbbd0fb2caea5c61ad3a826",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_evaluation/contract.py",
                "src/sat_dengue/model_evaluation/contract.py",
            ],
        },
        "scripts/model_evaluation/decision_policy.py": {
            "original": {
                "sha256": "69e42d78efd4f3952d1419ef188d3456d1657dfc4e4de1ee60c2d3269957a1fe",
                "bytes": 5852,
            },
            "engineering": {
                "bytes": 322,
                "sha256": "7512a083234e256da7852e63e4b118ed9d400b6deb1476fccd1cd13a97dbc0c1",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_evaluation/decision_policy.py",
                "src/sat_dengue/model_evaluation/decision_policy.py",
            ],
        },
        "scripts/model_evaluation/execution.py": {
            "original": {
                "sha256": "37816fbb6d1d57116d87802764b9f87f0967cb64ebef1204fada9f362593e2d5",
                "bytes": 1130,
            },
            "engineering": {
                "bytes": 372,
                "sha256": "488957af2c356fee57ef52678ac3e2b543710261d28493164b86771882b34008",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_evaluation/execution.py",
                "src/sat_dengue/datasets/evaluation_cli.py",
            ],
        },
        "scripts/model_evaluation/internal_evidence.py": {
            "original": {
                "sha256": "83a2aa7cf4d0579f46e85e2c1590601177610b8475d0748cd1d71f72e5524d85",
                "bytes": 8039,
            },
            "engineering": {
                "bytes": 324,
                "sha256": "c4188cc7011a65ea8de9acf461120bcce6676eb08eaf815e55721e6a206c4b76",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_evaluation/internal_evidence.py"
            ],
        },
        "scripts/model_evaluation/notebook_execution.py": {
            "original": {
                "sha256": "59bc268286ae126dd7894879d6cfcabaaa9ba76e12a4eded68cec7442d6d6b4d",
                "bytes": 5197,
            },
            "engineering": {
                "bytes": 381,
                "sha256": "23baa4171b8cef85c2e7b1776ca213e5a54e7098b0c0c1b00c24f6bd26941393",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_evaluation/notebook_execution.py",
                "src/sat_dengue/datasets/evaluation_cli.py",
            ],
        },
        "scripts/model_evaluation/pipeline.py": {
            "original": {
                "sha256": "42900de97a6023af5ff797bb11c917c25471b336fd231b6cd97f27abd5446b1f",
                "bytes": 94121,
            },
            "engineering": {
                "bytes": 315,
                "sha256": "0b06e6555db481cb37f77bf94f9a2295976f65f36b1094dfda9fb4349c8099d4",
            },
            "destination": [
                "src/sat_dengue/datasets/legacy_evaluation/model_evaluation/pipeline.py",
                "src/sat_dengue/model_evaluation/calibration.py",
            ],
        },
    },
}


def verify_evaluation_preservation(root: Path, records: dict[str, Any]) -> int:
    """Verify the closed evaluation originals and their separate engineering identities."""
    path = root / "docs/operations/kedro-evaluation-identities.json"
    files = EVALUATION_MAPPING["files"]
    mapped = set(files).intersection(records)
    if not mapped or not path.exists():
        return verify_cleanup_originals(root, records)
    assert not path.is_symlink()
    assert json.loads(path.read_text()) == EVALUATION_MAPPING, "Closed evaluation mapping changed"
    for name in sorted(mapped):
        entry = files[name]
        assert records[name] == entry["original"]
        raw = subprocess.check_output(
            ["git", "show", f"{EVALUATION_MAPPING['original_revision']}:{name}"], cwd=root
        )
        assert {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} == entry["original"]
        assert previous_engineering(root, name) == entry["engineering"]
        assert all(safe_path(root, destination).is_file() for destination in entry["destination"])
    remaining = {n: v for n, v in records.items() if n not in files}
    return (verify_cleanup_originals(root, remaining) if remaining else 0) + len(mapped)
