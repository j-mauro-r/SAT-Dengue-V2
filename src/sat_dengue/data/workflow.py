"""Pure node boundaries: explicit resolved configuration, frames and provenance."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable, Iterator
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes, resolve_configuration
from sat_dengue.data import consolidation as domain
from sat_dengue.data import readiness
from sat_dengue.data.validation import validate_panel_keys, validate_stage2_configuration


def resolve_data_configuration(
    inputs: dict[str, Any], parameters: dict[str, Any], sources: dict[str, Any]
) -> dict[str, Any]:
    resolved = resolve_configuration(inputs, parameters)
    resolved.pop("configuration_sha256")
    resolved["stage2"] = sources
    resolved["configuration_sha256"] = hashlib.sha256(canonical_bytes(resolved)).hexdigest()
    validate_stage2_configuration(resolved)
    return resolved


def scope_catalog(resolved: dict[str, Any]) -> pd.DataFrame:
    validate_stage2_configuration(resolved)
    return domain.normalize_scope_catalog(resolved["stage2"]["divipola"])


def normalize_climate(
    raw: Iterable[pd.DataFrame], catalog: pd.DataFrame, resolved: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    validate_stage2_configuration(resolved)
    return domain.normalize_climate_chunks(raw, set(catalog["municipality_code"]))


def consolidate(
    raw: Iterable[tuple[str, pd.DataFrame]],
    daily: pd.DataFrame,
    catalog: pd.DataFrame,
    resolved: dict[str, Any],
) -> dict[str, Any]:
    validate_stage2_configuration(resolved)
    columns = resolved["stage2"]["native_manifest"]["headers"]["epi_columns"]
    if len(columns) != 69 or len(set(columns)) != 69:
        raise ValueError("Expected ordered 69-column epidemiological schema")
    scope = set(catalog["municipality_code"])

    def enriched_chunks() -> Iterator[pd.DataFrame]:
        seen: dict[str, int] = defaultdict(int)
        for source, chunk in raw:
            if source not in domain.EPI_FILENAMES or list(chunk.columns) != columns:
                raise ValueError("Incorrect epidemiological source/schema")
            frame = domain.enrich_epi_chunk(
                chunk,
                source_file=source,
                source_row_start=seen[source] + 1,
                scope_codes=scope,
                climate_lookup=daily,
            )
            seen[source] += len(chunk)
            yield frame
        if set(seen) != set(domain.EPI_FILENAMES) or not all(seen.values()):
            raise ValueError("Missing epidemiological source")

    return {"resolved": resolved, "chunks": enriched_chunks()}


def aggregate_notifications(
    consolidated: dict[str, Any], resolved: dict[str, Any]
) -> dict[str, Any]:
    validate_stage2_configuration(resolved)
    counter: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"dengue": 0, "dengue_grave": 0}
    )
    rows = 0
    years: set[int] = set()
    reconciliation = {
        "outside_scope_rows": 0,
        "missing_or_unparseable_onset_rows": 0,
        "no_climate_match_assignable_rows": 0,
        "assignable_rows": 0,
    }
    source_rows: dict[str, int] = defaultdict(int)
    schema: list[dict[str, Any]] = []
    for chunk in consolidated["chunks"]:
        schema = domain.describe_consolidated_schema_from_columns(list(chunk.columns))
        rows += len(chunk)
        for source, count in chunk["source_file"].value_counts().items():
            source_rows[str(source)] += int(count)
        parsed = pd.to_numeric(chunk["ANO"].str.strip(), errors="coerce").dropna().astype(int)
        years.update(parsed.unique().tolist())
        reason = chunk["panel_assignment_reason"]
        reconciliation["outside_scope_rows"] += int(reason.eq("out_of_scope_municipality").sum())
        reconciliation["missing_or_unparseable_onset_rows"] += int(
            reason.isin(["missing_ini_sin", "unparseable_ini_sin"]).sum()
        )
        assignable = chunk[reason.eq("assignable")]
        reconciliation["assignable_rows"] += len(assignable)
        reconciliation["no_climate_match_assignable_rows"] += int(
            assignable["climate_join_status"].eq("no_climate_match").sum()
        )
        counts = domain.build_epi_monthly_counts(chunk)
        for row in counts.itertuples(index=False):
            counter[(str(row.municipality_code), str(row.year_month))]["dengue"] += int(
                row.dengue_notifications_count
            )
            counter[(str(row.municipality_code), str(row.year_month))]["dengue_grave"] += int(
                row.dengue_grave_notifications_count
            )
    if not counter or not years:
        raise ValueError("No assignable notifications or notification-year metadata")
    return {
        "counts": domain.build_epi_monthly_counts_from_counter(counter),
        "rows": rows,
        "schema": schema,
        "years": sorted(years),
        "source_rows": dict(source_rows),
        "reconciliation": reconciliation,
        "consolidated_identity": consolidated["identity"],
    }


def aggregate_climate(daily: pd.DataFrame, resolved: dict[str, Any]) -> pd.DataFrame:
    validate_stage2_configuration(resolved)
    return domain.aggregate_monthly_climate(daily)


def build_panel(
    epidemiology: dict[str, Any],
    monthly: pd.DataFrame,
    catalog: pd.DataFrame,
    resolved: dict[str, Any],
) -> pd.DataFrame:
    validate_stage2_configuration(resolved)
    counts = epidemiology["counts"]
    epi_start, epi_end = str(counts["year_month"].min()), str(counts["year_month"].max())
    start, end = (
        min(epi_start, str(monthly["year_month"].min())),
        max(epi_end, str(monthly["year_month"].max())),
    )
    grid = domain.build_panel_grid(catalog, start, end)
    panel = domain.build_monthly_panel(
        grid=grid,
        epi_counts=counts,
        climate_monthly=monthly,
        epi_coverage_start=epi_start,
        epi_coverage_end=epi_end,
    )
    validate_panel_keys(panel)
    return panel


def label_targets(
    panel: pd.DataFrame, resolved: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    policy = validate_stage2_configuration(resolved)["target_labeling_policy"]
    validate_panel_keys(panel)
    return domain.compute_y_labels(
        panel, horizons=tuple(policy["horizons_months"]), history_years=policy["reference_years"]
    )


def current_channel(
    panel: pd.DataFrame, resolved: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    policy = validate_stage2_configuration(resolved)["current_endemic_channel_policy"]
    validate_panel_keys(panel)
    return domain.compute_current_endemic_channel(panel, history_years=policy["reference_years"])


def audit_readiness(
    panel: pd.DataFrame, epidemiology: dict[str, Any], resolved: dict[str, Any]
) -> tuple[dict[str, Any], pd.DataFrame]:
    validate_stage2_configuration(resolved)
    validate_panel_keys(panel)
    reserved = resolved["authorities"]["training_preparation_contract_v1"]["document"][
        "temporal_policy"
    ]["reserved_final_block_start"]
    policy = readiness.build_model_eligibility_policy(
        min(epidemiology["years"]), max(epidemiology["years"]), reserved_block_start=reserved
    )
    lower, upper, _ = readiness.extract_development_target_bounds(policy)
    eligibility = panel[["municipality_code", "year_month"]].copy()
    counts = {}
    for horizon in (1, 2):
        suffix = f"t{horizon}"
        target = panel[f"target_period_{suffix}"]
        allowed = target.between(lower, upper)
        eligible = allowed & panel[f"y_evaluable_{suffix}"]
        reason = panel[f"y_status_{suffix}"].astype("string").copy()
        reason = (
            reason.mask(allowed & eligible, "eligible")
            .mask(target < lower, "before_backed_history")
            .mask(target > upper, "outside_development_target")
        )
        eligibility[f"eligible_{suffix}"] = eligible
        eligibility[f"exclusion_reason_{suffix}"] = reason
        independent = readiness.independent_select_supervised_rows(
            panel, horizon, target_min_period=lower, target_max_period=upper
        )
        pd.testing.assert_frame_equal(
            independent[["municipality_code", "year_month"]].reset_index(drop=True),
            panel.loc[eligible, ["municipality_code", "year_month"]].reset_index(drop=True),
        )
        counts[suffix] = int(eligible.sum())
    channel = readiness.recompute_channel_independently(panel)
    for column in ["p25_canal_t", "p50_canal_t", "p75_canal_t", "zona_canal_t"]:
        pd.testing.assert_series_equal(
            panel[column].astype("string") if column == "zona_canal_t" else panel[column],
            channel[f"independent_{column}"].astype("string")
            if column == "zona_canal_t"
            else channel[f"independent_{column}"],
            check_names=False,
        )
    edge = readiness.compute_edge_contribution(
        panel, f"{min(epidemiology['years']):04d}-01", f"{max(epidemiology['years']):04d}-12"
    )
    return {
        "status": "PASS",
        "policy": policy,
        "eligible_rows": counts,
        "edge_contribution": edge,
        "independent_channel": "PASS",
        "real_fits": 0,
        "operational_as_of_certified": False,
    }, eligibility


def assemble_bundle(
    panel: pd.DataFrame,
    y_trace: pd.DataFrame,
    channel_trace: pd.DataFrame,
    channel_summary: dict[str, Any],
    epidemiology: dict[str, Any],
    climate_summary: dict[str, Any],
    audit: dict[str, Any],
    eligibility: pd.DataFrame,
    resolved: dict[str, Any],
) -> dict[str, Any]:
    validate_stage2_configuration(resolved)
    validate_panel_keys(panel)
    for source, column in [
        ("dengue.csv", "dengue_notifications_count"),
        ("dengue_grave.csv", "dengue_grave_notifications_count"),
    ]:
        expected = int(epidemiology["counts"][column].sum())
        if int(panel[column].fillna(0).sum()) != expected:
            raise ValueError(f"Derived notification reconciliation failed: {source}")
    contract = domain.compute_schema_contract(
        epidemiology["schema"],
        panel,
        version=resolved["stage2"]["construction"]["contract_version"],
        generated_utc=resolved["execution"]["created_at"],
    )
    return {
        "resolved": resolved,
        "tables": {
            "panel.csv": panel,
            "y_history.csv": y_trace,
            "channel_history.csv": channel_trace,
            "eligibility.csv": eligibility,
        },
        "documents": {
            "readiness.json": audit,
            "construction.json": contract,
            "summary.json": {
                "source_rows": epidemiology["source_rows"],
                "consolidated_rows": epidemiology["rows"],
                "reconciliation": epidemiology["reconciliation"],
                "climate": climate_summary,
                "targets": domain.summarize_y_labels(panel),
                "channel": channel_summary,
            },
        },
        "consolidated_identity": epidemiology["consolidated_identity"],
    }
