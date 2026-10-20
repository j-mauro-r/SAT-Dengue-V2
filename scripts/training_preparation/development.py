"""Build and persist milestone-2 development candidates without training or final-block EDA."""

from __future__ import annotations

import argparse
import hashlib
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .contract import PreparationConfig, PreparationError, read_json
from .eligibility import build_controls, notification_year_metadata, policy_from_years
from .features import DERIVED_COLUMNS, KEYS, derive_features
from .persistence import bytes_record, json_bytes, publish_bundle, verify_bundle
from .pipeline import fingerprint, prepare_inputs


def resolve_root(start: Path | None = None) -> Path:
    """Find the repository from a working directory or script anchor.

    Args:
        start: Optional directory anchor; defaults to the current directory.

    Returns:
        Root containing AGENTS.md and pyproject.toml.

    Raises:
        PreparationError: If the repository cannot be located.
    """
    anchor = (start or Path.cwd()).resolve()
    for candidate in (anchor, *anchor.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "pyproject.toml").is_file():
            return candidate
    raise PreparationError("Run from within the repository")


def code_fingerprints(root: Path) -> dict[str, Any]:
    """Fingerprint all load-bearing source, policy, notebook and packaging files.

    Args:
        root: Repository root.

    Returns:
        Relative paths and hashes, without machine-specific directories.
    """
    paths = list((root / "scripts/training_preparation").glob("*.py"))
    paths += [
        root / p
        for p in (
            "scripts/validate_stage2_training_readiness.py",
            "pyproject.toml",
            "notebooks/04_training_preparation_pipeline.ipynb",
        )
    ]
    return {str(p.relative_to(root)): fingerprint(p) for p in sorted(paths)}


def serialize_table(frame: pd.DataFrame) -> bytes:
    """Serialize table bytes deterministically without inventing missing values.

    Args:
        frame: Ordered table with explicit roles and sorted rows.

    Returns:
        UTF-8 CSV with stable float formatting and empty missing cells.
    """
    return frame.to_csv(index=False, na_rep="", lineterminator="\n", float_format="%.17g").encode()


@dataclass(frozen=True)
class DevelopmentResult:
    """Published development bundle and bounded review evidence.

    Args:
        bundle: Absolute local bundle directory.
        manifest: Reproducible evidence; no private case rows or final-block results.
    """

    bundle: Path
    manifest: dict[str, Any]


def check_preservation(config: PreparationConfig, baseline: Path) -> int:
    """Check pre-task fingerprints without reading scientific values.

    Args:
        config: Repository input configuration.
        baseline: Existing fingerprint map, resolved within the repository.

    Returns:
        Number of verified scientific files.

    Raises:
        PreparationError: If any byte identity changed.
    """
    expected = read_json(config.resolve(baseline))
    for relative, record in expected.items():
        if fingerprint(config.resolve(relative)) != record:
            raise PreparationError(f"Scientific input changed: {relative}")
    return len(expected)


def build_development(config: PreparationConfig, *, verify_only: bool = False) -> DevelopmentResult:
    """Construct all antecedents before auditing supervised eligibility and publishing.

    Args:
        config: Repository and preparation contract paths.
        verify_only: Recompute bytes and require a matching existing bundle; do not write.

    Returns:
        Bundle path and manifest, with development-only summaries.

    Raises:
        PreparationError: If inputs change, eligibility disagrees or publication fails.
    """
    contract = read_json(config.resolve(config.contract_path))
    output = contract["development_output"]
    prepared = prepare_inputs(config, reference_end=output["reference_end"])
    code = code_fingerprints(config.root)
    # Only source notification-year metadata is read, never counts/outcomes by final block.
    years = notification_year_metadata(config.resolve("data/processed/dengue_y_dengue_grave.csv"))
    policy = policy_from_years(
        int(years["min_year"]),
        int(years["max_year"]),
        contract["temporal_policy"]["reserved_final_block_start"],
    )
    history = prepared.panel.sort_values(KEYS).reset_index(drop=True)
    candidates = derive_features(history, contract)
    controls, eligibility = build_controls(history, contract, policy)
    features = candidates.drop(columns=KEYS)
    keys = candidates[KEYS]
    identity = {
        "data": prepared.report["input_fingerprints"],
        "code": code,
        "configuration": {
            "preparation_contract": contract,
            "reference_end": output["reference_end"],
        },
        "runtime": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
    }
    bundle_id = hashlib.sha256(json_bytes(identity)).hexdigest()
    payloads = {
        "keys.csv": serialize_table(keys),
        "features.csv": serialize_table(features),
        "controls.csv": serialize_table(controls),
    }
    summary = {
        "reference_start": str(keys["year_month"].min()),
        "reference_end": str(keys["year_month"].max()),
        "rows": len(keys),
        "municipalities": keys["municipality_code"].nunique(),
        "missing_features": {c: int(n) for c, n in features.isna().sum().items()},
        "eligible_rows_missing_features": {
            f"t{h}": int(features.loc[controls[f"eligible_t{h}"]].isna().any(axis=1).sum())
            for h in (1, 2)
        },
    }
    manifest = {
        "version": "development-features-v1",
        "bundle_id": bundle_id,
        "identity": identity,
        "roles": {
            "keys": list(keys.columns),
            "features": list(features.columns),
            "controls": list(controls.columns),
        },
        "row_alignment": (
            "All three tables share municipality_code/year_month sorted row order; "
            "controls repeat keys."
        ),
        "derived_features": list(DERIVED_COLUMNS),
        "summary": summary,
        "eligibility_policy": policy,
        "eligibility_audit": eligibility,
        "files": {name: bytes_record(data) for name, data in payloads.items()},
        "reserved_block": (
            "Separate in original input; no reserved reference features "
            "or outcome summaries produced."
        ),
        "interpretation": (
            "Candidates only; predictive utility and historical operational availability unproven."
        ),
    }
    payloads["manifest.json"] = json_bytes(manifest)
    # Prevent publishing evidence for input/config/code bytes that changed while computing.
    for relative, record in identity["data"].items():
        if fingerprint(config.resolve(relative)) != record:
            raise PreparationError(f"Input changed during feature construction: {relative}")
    if code_fingerprints(config.root) != code:
        raise PreparationError("Code changed during feature construction")
    base = config.resolve(output["base_dir"])
    if verify_only:
        bundle = base / bundle_id
        verify_bundle(bundle, payloads)
    else:
        bundle = publish_bundle(
            base, bundle_id, payloads, existing_policy=output["existing_policy"]
        )
    return DevelopmentResult(bundle, manifest)


def main() -> None:
    """Build or verify the development bundle and print only bounded aggregate evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    config = PreparationConfig(resolve_root(args.root))
    if args.baseline:
        check_preservation(config, args.baseline)
    result = build_development(config, verify_only=args.verify)
    if args.baseline:
        check_preservation(config, args.baseline)
    print(
        json_bytes(
            {
                "bundle": str(result.bundle.relative_to(config.root)),
                "summary": result.manifest["summary"],
                "eligibility": result.manifest["eligibility_audit"],
                "status": "PASS",
            }
        ).decode()
    )


if __name__ == "__main__":
    main()
