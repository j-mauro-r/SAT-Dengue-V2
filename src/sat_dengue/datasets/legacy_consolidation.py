"""Build candidate Stage 2 datasets for consolidated epidemiological-climate analysis.

This module implements Chapter 1 (dataset construction and validation) of the
new consolidated pipeline notebook. It creates two candidate datasets:

1. data/processed/dengue_y_dengue_grave.csv
2. data/processed/panel_mensual_dengue_clima.csv

The implementation preserves raw epidemiological columns as supplied, adds
provenance metadata, links daily climate by residence municipality and symptom
onset date, and derives a municipality-month panel for Tolima/Meta scope.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.consolidation import (
    CANAL_PERCENTILES as CANAL_PERCENTILES,
)
from sat_dengue.data.consolidation import (
    CANAL_ZONE_VALUES as CANAL_ZONE_VALUES,
)
from sat_dengue.data.consolidation import (
    CLIMATE_DAILY_VARIABLES as CLIMATE_DAILY_VARIABLES,
)
from sat_dengue.data.consolidation import (
    CLIMATE_FILENAME as CLIMATE_FILENAME,
)
from sat_dengue.data.consolidation import (
    CLIMATE_MONTHLY_MEAN_MAP as CLIMATE_MONTHLY_MEAN_MAP,
)
from sat_dengue.data.consolidation import (
    CLIMATE_MONTHLY_SUM_MAP as CLIMATE_MONTHLY_SUM_MAP,
)
from sat_dengue.data.consolidation import (
    EPI_FILENAMES as EPI_FILENAMES,
)
from sat_dengue.data.consolidation import (
    EXPECTED_OUTPUT_PATH_BY_KEY as EXPECTED_OUTPUT_PATH_BY_KEY,
)
from sat_dengue.data.consolidation import (
    SCOPE_DEPARTMENTS as SCOPE_DEPARTMENTS,
)
from sat_dengue.data.consolidation import (
    SOURCE_LABEL_BY_FILE as SOURCE_LABEL_BY_FILE,
)
from sat_dengue.data.consolidation import (
    Y_HORIZONS as Y_HORIZONS,
)
from sat_dengue.data.consolidation import (
    Y_PERCENTILE as Y_PERCENTILE,
)
from sat_dengue.data.consolidation import (
    Y_PERCENTILE_METHOD as Y_PERCENTILE_METHOD,
)
from sat_dengue.data.consolidation import (
    Y_REFERENCE_YEARS as Y_REFERENCE_YEARS,
)
from sat_dengue.data.consolidation import (
    PipelineValidationError as PipelineValidationError,
)
from sat_dengue.data.consolidation import (
    add_months as add_months,
)
from sat_dengue.data.consolidation import (
    aggregate_monthly_climate as aggregate_monthly_climate,
)
from sat_dengue.data.consolidation import (
    build_epi_monthly_counts as build_epi_monthly_counts,
)
from sat_dengue.data.consolidation import (
    build_epi_monthly_counts_from_counter as build_epi_monthly_counts_from_counter,
)
from sat_dengue.data.consolidation import (
    build_monthly_panel as build_monthly_panel,
)
from sat_dengue.data.consolidation import (
    build_panel_grid as build_panel_grid,
)
from sat_dengue.data.consolidation import (
    classify_endemic_zone as classify_endemic_zone,
)
from sat_dengue.data.consolidation import (
    compute_current_endemic_channel as compute_current_endemic_channel,
)
from sat_dengue.data.consolidation import (
    compute_schema_contract as _compute_schema_contract,
)
from sat_dengue.data.consolidation import (
    compute_y_labels as compute_y_labels,
)
from sat_dengue.data.consolidation import (
    date_parse_status as date_parse_status,
)
from sat_dengue.data.consolidation import (
    describe_consolidated_schema_from_columns as describe_consolidated_schema_from_columns,
)
from sat_dengue.data.consolidation import (
    enrich_epi_chunk as enrich_epi_chunk,
)
from sat_dengue.data.consolidation import (
    history_periods_for_target as history_periods_for_target,
)
from sat_dengue.data.consolidation import (
    month_range as month_range,
)
from sat_dengue.data.consolidation import (
    normalize_climate_chunks as normalize_climate_chunks,
)
from sat_dengue.data.consolidation import (
    normalize_code_series as normalize_code_series,
)
from sat_dengue.data.consolidation import (
    normalize_numeric_code as normalize_numeric_code,
)
from sat_dengue.data.consolidation import (
    normalize_scope_catalog as normalize_scope_catalog,
)
from sat_dengue.data.consolidation import (
    panel_assignment_reason as panel_assignment_reason,
)
from sat_dengue.data.consolidation import (
    parse_epi_date_series as parse_epi_date_series,
)
from sat_dengue.data.consolidation import (
    percentile_type7 as percentile_type7,
)
from sat_dengue.data.consolidation import (
    summarize_y_labels as summarize_y_labels,
)


@dataclass(frozen=True)
class PipelinePaths:
    """Resolved project paths for the candidate dataset pipeline.

    Args:
        root: Repository root directory.
        raw_dir: Input raw data directory.
        sources_dir: Input reference directory.
        processed_dir: Output processed data directory.
        interim_dir: Output interim evidence directory.
    """

    root: Path
    raw_dir: Path
    sources_dir: Path
    processed_dir: Path
    interim_dir: Path


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for candidate dataset construction.

    Args:
        chunksize_epi: Chunksize for epidemiological CSV reads.
        chunksize_climate: Chunksize for climate CSV reads.
        contract_version: Candidate construction contract version string.
        perform_safe_write: If true, write outputs to disk; else dry run.
        reuse_existing_outputs: If true, reuse existing outputs when manifest checks pass.
    """

    chunksize_epi: int = 200_000
    chunksize_climate: int = 250_000
    contract_version: str = "candidate-construction-v1"
    perform_safe_write: bool = True
    reuse_existing_outputs: bool = False


@dataclass
class PipelineResult:
    """Structured output metadata produced by the pipeline run.

    Args:
        consolidated_path: Final consolidated output path.
        panel_path: Final panel output path.
        consolidated_rows: Number of rows written to consolidated output.
        panel_rows: Number of rows written to panel output.
        consolidated_columns: Number of columns written to consolidated output.
        panel_columns: Number of columns written to panel output.
        manifest_path: Execution manifest path.
        contract_path: Candidate contract artifact path.
        y_traceability_path: Y history traceability artifact path.
    """

    consolidated_path: Path
    panel_path: Path
    consolidated_rows: int
    panel_rows: int
    consolidated_columns: int
    panel_columns: int
    manifest_path: Path
    contract_path: Path
    y_traceability_path: Path


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp.

    Returns:
        Current UTC timestamp in ISO format.
    """

    return datetime.now(UTC).isoformat()


def sha256_file(path: Path) -> str:
    """Compute SHA-256 digest for a file.

    Args:
        path: File path to hash.

    Returns:
        Hex SHA-256 digest.
    """

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_repo_root(start: Path | None = None) -> Path:
    """Resolve repository root by searching parent directories.

    Args:
        start: Optional start path. If omitted, uses this module path.

    Returns:
        Repository root path.

    Raises:
        PipelineValidationError: If root cannot be resolved.
    """

    anchor = (start or Path(__file__).resolve()).resolve()
    candidates = [anchor, *anchor.parents]
    for candidate in candidates:
        if (candidate / "AGENTS.md").exists() and (candidate / "pyproject.toml").exists():
            return candidate
    raise PipelineValidationError("Unable to resolve repository root from module location")


def build_paths(root: Path) -> PipelinePaths:
    """Build standardized pipeline path mapping.

    Args:
        root: Repository root path.

    Returns:
        Resolved path dataclass.
    """

    return PipelinePaths(
        root=root,
        raw_dir=root / "data/raw",
        sources_dir=root / "data/sources",
        processed_dir=root / "data/processed",
        interim_dir=root / "data/interim/stage2_consolidated_dataset_pipeline",
    )


def read_csv_header(path: Path) -> list[str]:
    """Read CSV header preserving original names.

    Args:
        path: CSV file path.

    Returns:
        Ordered header list.
    """

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        return next(reader)


def load_scope_catalog(paths: PipelinePaths) -> pd.DataFrame:
    payload = json.loads((paths.sources_dir / "Divipola-municipios.md").read_text(encoding="utf-8"))
    return normalize_scope_catalog(payload)


def validate_epi_headers(paths: PipelinePaths) -> list[str]:
    """Validate epidemiological headers and return canonical columns.

    Args:
        paths: Pipeline paths.

    Returns:
        Canonical epidemiological columns.

    Raises:
        PipelineValidationError: If headers diverge.
    """

    headers = {filename: read_csv_header(paths.raw_dir / filename) for filename in EPI_FILENAMES}
    first = headers[EPI_FILENAMES[0]]
    for filename in EPI_FILENAMES[1:]:
        if headers[filename] != first:
            raise PipelineValidationError(
                "Epidemiological headers diverge; candidate requires explicit reconciliation "
                f"before construction ({EPI_FILENAMES[0]} vs {filename})"
            )
    if len(first) != 69:
        raise PipelineValidationError(f"Expected 69 epidemiological columns, found {len(first)}")
    return first


def validate_climate_header(paths: PipelinePaths) -> list[str]:
    """Validate climate source header.

    Args:
        paths: Pipeline paths.

    Returns:
        Climate header list.

    Raises:
        PipelineValidationError: If required columns are missing.
    """

    header = read_csv_header(paths.raw_dir / CLIMATE_FILENAME)
    required = {
        "date",
        "dpto_ccdgo",
        "mpio_cdpmp",
        *CLIMATE_DAILY_VARIABLES,
    }
    missing = sorted(required - set(header))
    if missing:
        raise PipelineValidationError(f"Climate source missing required columns: {missing}")
    return header


def load_scope_climate_daily(
    paths: PipelinePaths, scope_codes: set[str], config: PipelineConfig
) -> tuple[pd.DataFrame, dict[str, Any]]:
    chunks = pd.read_csv(
        paths.raw_dir / CLIMATE_FILENAME,
        dtype=str,
        chunksize=config.chunksize_climate,
        keep_default_na=False,
    )
    return normalize_climate_chunks(chunks, scope_codes)


def compute_schema_contract(
    consolidated_schema: list[dict[str, Any]], panel: pd.DataFrame, *, version: str
) -> dict[str, Any]:
    return _compute_schema_contract(
        consolidated_schema, panel, version=version, generated_utc=utc_now_iso()
    )


def ensure_directory(path: Path) -> None:
    """Create directory recursively if absent.

    Args:
        path: Directory path.
    """

    path.mkdir(parents=True, exist_ok=True)


def safe_replace_file(
    *,
    tmp_path: Path,
    final_path: Path,
    backup_dir: Path,
) -> dict[str, Any]:
    """Atomically replace output file with backup preservation.

    Args:
        tmp_path: Temporary file path.
        final_path: Final target path.
        backup_dir: Backup directory.

    Returns:
        Backup metadata dictionary.

    Raises:
        PipelineValidationError: If replacement cannot be completed.
    """

    ensure_directory(final_path.parent)
    ensure_directory(backup_dir)

    metadata: dict[str, Any] = {
        "target": str(final_path),
        "had_previous": final_path.exists(),
    }

    if final_path.exists():
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = backup_dir / f"{final_path.name}.{timestamp}.bak"
        shutil.copy2(final_path, backup_path)
        metadata["backup_path"] = str(backup_path)
        metadata["backup_sha256"] = sha256_file(backup_path)

    tmp_path.replace(final_path)
    metadata["final_sha256"] = sha256_file(final_path)
    metadata["final_bytes"] = final_path.stat().st_size
    return metadata


def fingerprint_inputs(paths: PipelinePaths) -> dict[str, Any]:
    """Compute source fingerprints for reproducibility evidence.

    Args:
        paths: Pipeline paths.

    Returns:
        Input fingerprint dictionary.
    """

    files = [
        paths.raw_dir / "dengue.csv",
        paths.raw_dir / "dengue_grave.csv",
        paths.raw_dir / "google_earth_engine.csv",
        paths.sources_dir / "Divipola-municipios.md",
        paths.sources_dir / "divipola-provenance.json",
    ]
    return {
        str(path.relative_to(paths.root)): {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in files
    }


def build_pipeline_signature(paths: PipelinePaths, config: PipelineConfig) -> dict[str, Any]:
    """Build a deterministic pipeline signature for reuse validation.

    Args:
        paths: Pipeline paths.
        config: Active pipeline configuration.

    Returns:
        Signature dictionary that includes module identity and configuration.
    """

    module_relpath = "scripts/stage2_consolidated_dataset_pipeline.py"
    module_path = paths.root / module_relpath
    return {
        "module": module_relpath,
        "module_sha256": sha256_file(module_path),
        "contract_version": config.contract_version,
        "chunksize_epi": config.chunksize_epi,
        "chunksize_climate": config.chunksize_climate,
    }


def validate_manifest_reuse_candidate(
    *,
    root: Path,
    config: PipelineConfig,
    manifest: dict[str, Any],
    required_output_keys: Iterable[str],
) -> tuple[bool, list[str], dict[str, Any]]:
    """Validate whether execution-manifest artifacts are safe to reuse.

    Args:
        root: Repository root.
        config: Active pipeline configuration.
        manifest: Loaded execution manifest.
        required_output_keys: Required output aliases for reuse.

    Returns:
        Tuple ``(can_reuse, reasons, summary)``.
        ``reasons`` is empty when reuse is allowed.
    """

    paths = build_paths(root)
    reasons: list[str] = []

    expected_signature = build_pipeline_signature(paths, config)
    manifest_pipeline = manifest.get("pipeline")
    if not isinstance(manifest_pipeline, dict):
        reasons.append("pipeline_signature_missing")
        manifest_pipeline = {}

    for key, expected_value in expected_signature.items():
        if key not in manifest_pipeline:
            reasons.append(f"pipeline_{key}_missing")
            continue
        if manifest_pipeline[key] != expected_value:
            reasons.append(f"pipeline_{key}_mismatch")

    expected_inputs = fingerprint_inputs(paths)
    for field in ("input_fingerprints_before", "input_fingerprints_after"):
        observed = manifest.get(field)
        if not isinstance(observed, dict):
            reasons.append(f"{field}_missing")
            continue
        if observed != expected_inputs:
            reasons.append(f"{field}_mismatch")

    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict):
        reasons.append("outputs_section_missing")
        outputs = {}

    for output_key in required_output_keys:
        output_info = outputs.get(output_key)
        if not isinstance(output_info, dict):
            reasons.append(f"output_entry_missing:{output_key}")
            continue

        relative_path = output_info.get("path")
        if not isinstance(relative_path, str):
            reasons.append(f"output_path_missing:{output_key}")
            continue

        expected_relative_path = EXPECTED_OUTPUT_PATH_BY_KEY.get(output_key)
        if expected_relative_path is not None and relative_path != expected_relative_path:
            reasons.append(f"output_path_mismatch:{output_key}")
            continue

        output_path = root / relative_path
        if not output_path.exists():
            reasons.append(f"output_file_missing:{output_key}")
            continue

        expected_sha256 = output_info.get("sha256")
        if not isinstance(expected_sha256, str):
            reasons.append(f"output_sha256_missing:{output_key}")
        else:
            actual_sha256 = sha256_file(output_path)
            if actual_sha256 != expected_sha256:
                reasons.append(f"output_sha256_mismatch:{output_key}")

        expected_bytes = output_info.get("bytes")
        if expected_bytes is None:
            reasons.append(f"output_bytes_missing:{output_key}")
        else:
            actual_bytes = int(output_path.stat().st_size)
            try:
                if int(expected_bytes) != actual_bytes:
                    reasons.append(f"output_bytes_mismatch:{output_key}")
            except (TypeError, ValueError):
                reasons.append(f"output_bytes_invalid:{output_key}")

    can_reuse = len(reasons) == 0
    summary: dict[str, Any] = {}
    if can_reuse:
        consolidated = outputs.get("dengue_y_dengue_grave", {})
        panel = outputs.get("panel_mensual_dengue_clima", {})
        if isinstance(consolidated, dict) and isinstance(panel, dict):
            summary = {
                "consolidated_path": str(Path(str(consolidated.get("path", "")))),
                "panel_path": str(Path(str(panel.get("path", "")))),
                "consolidated_rows": int(consolidated.get("rows", -1)),
                "panel_rows": int(panel.get("rows", -1)),
            }

    return can_reuse, sorted(set(reasons)), summary


def _coerce_non_negative_int(value: Any) -> int | None:
    """Best-effort parse for non-negative integer metadata fields."""

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def build_pipeline_result_from_manifest(
    paths: PipelinePaths, manifest: dict[str, Any]
) -> PipelineResult:
    """Build a ``PipelineResult`` from an already-validated execution manifest.

    Args:
        paths: Pipeline paths.
        manifest: Loaded execution manifest.

    Returns:
        Reconstructed pipeline result.

    Raises:
        PipelineValidationError: If required output paths are missing.
    """

    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict):
        raise PipelineValidationError("Execution manifest outputs section missing for reuse")

    def required_output_path(output_key: str) -> Path:
        output_info = outputs.get(output_key)
        if not isinstance(output_info, dict):
            raise PipelineValidationError(f"Execution manifest output missing: {output_key}")
        relative_path = output_info.get("path")
        if not isinstance(relative_path, str):
            raise PipelineValidationError(f"Execution manifest path missing: {output_key}")
        absolute_path = paths.root / relative_path
        if not absolute_path.exists():
            raise PipelineValidationError(f"Execution manifest file missing: {relative_path}")
        return absolute_path

    consolidated_path = required_output_path("dengue_y_dengue_grave")
    panel_path = required_output_path("panel_mensual_dengue_clima")
    y_traceability_path = required_output_path("y_label_history_traceability")
    contract_path = required_output_path("candidate_contract")

    consolidated_info = outputs.get("dengue_y_dengue_grave", {})
    panel_info = outputs.get("panel_mensual_dengue_clima", {})
    consolidated_rows = (
        _coerce_non_negative_int(consolidated_info.get("rows"))
        if isinstance(consolidated_info, dict)
        else None
    )
    consolidated_columns = (
        _coerce_non_negative_int(consolidated_info.get("columns"))
        if isinstance(consolidated_info, dict)
        else None
    )
    panel_rows = (
        _coerce_non_negative_int(panel_info.get("rows")) if isinstance(panel_info, dict) else None
    )
    panel_columns = (
        _coerce_non_negative_int(panel_info.get("columns"))
        if isinstance(panel_info, dict)
        else None
    )

    if consolidated_rows is None or consolidated_columns is None:
        consolidated_header = pd.read_csv(consolidated_path, nrows=0)
        consolidated_columns = int(consolidated_header.shape[1])
        with consolidated_path.open("r", encoding="utf-8") as stream:
            consolidated_rows = max(sum(1 for _ in stream) - 1, 0)

    if panel_rows is None or panel_columns is None:
        panel_header = pd.read_csv(panel_path, nrows=0)
        panel_columns = int(panel_header.shape[1])
        with panel_path.open("r", encoding="utf-8") as stream:
            panel_rows = max(sum(1 for _ in stream) - 1, 0)

    return PipelineResult(
        consolidated_path=consolidated_path,
        panel_path=panel_path,
        consolidated_rows=int(consolidated_rows),
        panel_rows=int(panel_rows),
        consolidated_columns=int(consolidated_columns),
        panel_columns=int(panel_columns),
        manifest_path=paths.interim_dir / "execution_manifest.json",
        contract_path=contract_path,
        y_traceability_path=y_traceability_path,
    )


def write_dataframe_to_tmp(frame: pd.DataFrame, output_path: Path) -> Path:
    """Write dataframe to temp CSV in destination directory.

    Args:
        frame: Dataframe to write.
        output_path: Destination output path.

    Returns:
        Temporary file path.
    """

    ensure_directory(output_path.parent)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        suffix=".tmp",
        prefix=f"{output_path.name}.",
        dir=output_path.parent,
        delete=False,
    ) as tmp:
        frame.to_csv(tmp.name, index=False)
        return Path(tmp.name)


def run_pipeline(root: Path | None = None, config: PipelineConfig | None = None) -> PipelineResult:
    """Compatibility entrypoint using the single catalog-backed Stage 2 implementation.

    Outputs have new isolated engineering identities. Dry runs use disposable storage;
    reuse never selects or overwrites an implicit historical/latest bundle.
    """
    from sat_dengue.datasets.stage2 import run_compatibility

    return run_compatibility(resolve_repo_root(root), config or PipelineConfig())


def _print_summary(result: PipelineResult, root: Path) -> None:
    """Print concise aggregate execution summary.

    Args:
        result: Pipeline result metadata.
        root: Repository root.
    """

    payload = {
        "consolidated_path": str(result.consolidated_path.relative_to(root)),
        "panel_path": str(result.panel_path.relative_to(root)),
        "y_traceability_path": str(result.y_traceability_path.relative_to(root)),
        "consolidated_rows": result.consolidated_rows,
        "panel_rows": result.panel_rows,
        "consolidated_columns": result.consolidated_columns,
        "panel_columns": result.panel_columns,
        "manifest_path": str(result.manifest_path.relative_to(root)),
        "contract_path": str(result.contract_path.relative_to(root)),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument iterable.

    Returns:
        Parsed namespace.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build datasets in memory and validate without replacing outputs.",
    )
    parser.add_argument(
        "--chunksize-epi",
        type=int,
        default=PipelineConfig.chunksize_epi,
        help="Chunksize for epidemiological source reads.",
    )
    parser.add_argument(
        "--chunksize-climate",
        type=int,
        default=PipelineConfig.chunksize_climate,
        help="Chunksize for climate source reads.",
    )
    parser.add_argument(
        "--reuse-existing-outputs",
        action="store_true",
        help=(
            "Retained compatibility flag; publish a new isolated engineering run. "
            "Historical outputs are never reused or overwritten."
        ),
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entry point for candidate dataset construction.

    Args:
        argv: Optional command-line arguments.

    Returns:
        Process exit code.
    """

    args = parse_args(argv)
    config = PipelineConfig(
        chunksize_epi=args.chunksize_epi,
        chunksize_climate=args.chunksize_climate,
        perform_safe_write=not args.dry_run,
        reuse_existing_outputs=args.reuse_existing_outputs,
    )

    root = resolve_repo_root()
    result = run_pipeline(root=root, config=config)
    _print_summary(result, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
