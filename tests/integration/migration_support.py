"""Strict, read-only comparators shared by synthetic CI and protected replay."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

RTOL = 1e-8
ATOL = 1e-10
BASELINE_SHA256 = "d86338cd34dcde884e2be9d102271969d0f3b52f57b8ffdebd1829771977a5b3"
SCOPE_SHA256 = "5f16db6458a771fd2ee32197247b3331ecd5f57b148319e7ba99ba806cc9165f"
FINAL_ID = "768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35"
FINAL_PATH = Path("artifacts/model_final_evaluation") / FINAL_ID


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
    """Verify originals plus the two explicitly approved engineering identities."""
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
        assert fingerprint(safe_path(root, name)) == entry["engineering"], (
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
        assert (
            fingerprint(safe_path(root, name)) == entry["engineering"] == DATA_ENGINEERING[name]
        ), "Stage 2 engineering identity mismatch"
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
        return require_records(root, records)
    assert not path.is_symlink()
    assert json.loads(path.read_text()) == PREPARATION_MAPPING, "Closed preparation mapping changed"
    for name in sorted(mapped):
        entry = files[name]
        assert records[name] == entry["original"]
        raw = subprocess.check_output(
            ["git", "show", f"{PREPARATION_MAPPING['original_revision']}:{name}"], cwd=root
        )
        assert {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} == entry["original"]
        assert fingerprint(safe_path(root, name)) == entry["engineering"]
    remaining = {n: r for n, r in records.items() if n not in files}
    return (require_records(root, remaining) if remaining else 0) + len(mapped)
