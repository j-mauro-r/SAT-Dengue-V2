"""V4 orchestration of unchanged V2 domain rules, parity and temporal metadata."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.canonical.national import build_national
from sat_dengue.canonical.table import CLIMATE, KEYS
from sat_dengue.data.national_diagnostics import (
    COUNTS as EVENTS,
)
from sat_dengue.data.national_diagnostics import (
    build_review_calendar,
    classify_notifications,
)

DATASET = "canonical_model_table_national_v4"
CONSUMED = "consumed_retrospective_evidence"
HISTORICAL = "historical_development_evidence"


@dataclass(frozen=True)
class V4Window:
    """The authorized retrospective panel; January 2026 is explicitly excluded."""

    start_month: str = "2011-06"
    end_month: str = "2025-12"


def aggregate_notifications(
    chunks: Iterable[tuple[str, pd.DataFrame]],
    catalog: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Reuse residence/onset/event admission and calendar zeros, without microdata output."""
    accepted, located, reconciliation = [], [], []
    window = V4Window()
    for event, raw in chunks:
        frame = classify_notifications(raw, catalog, event, window)
        accepted.append(frame.loc[frame.accepted].groupby(KEYS).size().rename(EVENTS[event]))
        valid_location = (
            ~frame.invalid_territory & ~frame.invalid_onset & ~frame.outside_review_window
        )
        located.append(
            frame.loc[valid_location].groupby(KEYS).size().rename(EVENTS[event] + "_source_rows")
        )
        reconciliation.append(
            {
                "event": event,
                "source_rows": len(frame),
                "accepted": int(frame.accepted.sum()),
                "unassigned_in_window": int(
                    (frame.invalid_territory & ~frame.outside_review_window).sum()
                ),
                "outside_panel": int(frame.outside_review_window.sum()),
                "invalid_onset": int(frame.invalid_onset.sum()),
                "event_review": int((frame.invalid_event | frame.stream_event_mismatch).sum()),
            }
        )

    def combine(parts: list[pd.Series]) -> pd.DataFrame:
        values = pd.concat(parts, axis=1).fillna(0)
        # Both chunks of a stream and the two streams can share municipality-month keys.
        return values.T.groupby(level=0).sum().T.groupby(level=KEYS).sum().reset_index()

    calendar = build_review_calendar(catalog, combine(accepted), window, combine(located))
    return calendar, {
        "streams": pd.DataFrame(reconciliation).groupby("event").sum().to_dict("index")
    }


def cast_common(table: pd.DataFrame, columns: list[dict[str, Any]]) -> pd.DataFrame:
    """Preserve the national V1 physical type contract in its original column order."""
    result = table.copy()
    for field in columns:
        result[field["name"]] = result[field["name"]].astype(field["dtype"])
    return result


def compare_tables(
    current: pd.DataFrame,
    reference: pd.DataFrame,
    *,
    label: str,
    require_all_keys: bool = True,
    outcome_end: str | None = None,
) -> list[dict[str, Any]]:
    """Compare every shared value and null; only approved climate precision is tolerated."""
    if not set(reference) <= set(current):
        raise ValueError(f"{label}: missing reference columns")
    shared = [n for n in reference if n not in KEYS]
    left = current.merge(reference[KEYS], on=KEYS, validate="one_to_one")
    right = reference.merge(current[KEYS], on=KEYS, validate="one_to_one")
    if require_all_keys and len(left) != len(reference):
        raise ValueError(f"{label}: missing reference keys")
    left, right = (f.sort_values(KEYS).reset_index(drop=True) for f in (left, right))
    if not left[KEYS].equals(right[KEYS]):
        raise ValueError(f"{label}: key mismatch")
    report = []
    for name in shared:
        a, b = left[name], right[name]
        missing = a.isna().ne(b.isna())
        equal = (a.eq(b) | (a.isna() & b.isna())).fillna(False)
        different = ~equal
        material = different.copy()
        explained = pd.Series(False, index=left.index)
        cause = "exact_or_climate_precision"
        # Regional V1 has January 2026 observations. V4 explicitly excludes them.
        # Admit only the four known outcome-gated fields, and only when V4 retains
        # the exact inherited outside-panel state. All other differences still fail.
        for h in (1, 2):
            expected_outside = {
                f"p75_t{h}": None,
                f"y_t{h}": None,
                f"y_evaluable_t{h}": False,
                f"y_status_t{h}": "target_outside_panel",
            }
            if outcome_end is not None and name in expected_outside:
                outside = left[f"target_period_t{h}"].gt(outcome_end)
                expected = expected_outside[name]
                valid = a.isna() if expected is None else a.eq(expected).fillna(False)
                if not valid.loc[outside].all():
                    raise ValueError("Invalid V4 outside-panel outcome state")
                explained = different & outside
                material &= ~explained
                if explained.any():
                    cause = "necessary_2026_target_exclusion_from_V4_panel"
        maximum = 0.0
        if name in CLIMATE:
            delta = (a.astype(float) - b.astype(float)).abs()
            maximum = float(delta.max()) if delta.notna().any() else 0.0
            material &= ~(delta.le(1e-10) & ~missing)
        item = {
            "reference": label,
            "column": name,
            "paired_rows": len(left),
            "different_rows": int(different.sum()),
            "missing_mismatches": int(missing.sum()),
            "material_rows": int(material.sum()),
            "explained_boundary_rows": int(explained.sum()),
            "cause": cause,
            "affected_origins": sorted(left.loc[different, "year_month"].unique().tolist()),
            "maximum_absolute_difference": maximum,
            "current_dtype": str(a.dtype),
            "reference_dtype": str(b.dtype),
        }
        report.append(item)
    bad = [r for r in report if r["material_rows"]]
    if bad:
        raise ValueError(f"{label}: material parity incompatibility: {bad}")
    return report


def add_temporal_metadata(table: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate panel maturity, evaluability, onset availability and consumed evidence."""
    table = table.copy()
    table["origin_scientific_role"] = np.where(table.year_month.ge("2025-01"), CONSUMED, HISTORICAL)
    roles = []
    for h in (1, 2):
        target = table[f"target_period_t{h}"]
        outside = target.gt("2025-12")
        table[f"maturity_t{h}"] = np.where(outside, "target_outside_panel", "mature")
        table[f"scientific_role_t{h}"] = np.where(
            table.year_month.ge("2025-01") | target.ge("2025-01"), CONSUMED, HISTORICAL
        )
        table[f"onset_status_t{h}"] = np.where(
            outside,
            "target_outside_panel",
            np.where(table[f"onset_T{h}"].notna(), "evaluable", "insufficient_history"),
        )
        if (
            table.loc[outside, [f"y_t{h}", f"onset_T{h}", f"future_dengue_count_t{h}"]]
            .notna()
            .any()
            .any()
            or not table.loc[outside, f"y_status_t{h}"].eq("target_outside_panel").all()
            or table.loc[outside, f"y_evaluable_t{h}"].any()
        ):
            raise ValueError("Invented future outcome")
        roles.append(
            pd.DataFrame(
                {
                    "municipality_code": table.municipality_code,
                    "origin_period": table.year_month,
                    "target_period": target,
                    "horizon": h,
                    "maturity": table[f"maturity_t{h}"],
                    "scientific_role": table[f"scientific_role_t{h}"],
                    "y_status": table[f"y_status_t{h}"],
                    "onset_status": table[f"onset_status_t{h}"],
                }
            )
        )
    return table, pd.concat(roles, ignore_index=True)


def build_v4(
    calendar: pd.DataFrame,
    monthly: pd.DataFrame,
    regional: pd.DataFrame,
    national: pd.DataFrame,
    contract: dict[str, Any],
    columns: list[dict[str, Any]],
) -> dict[str, Any]:
    """Recompute from raw aggregates, then reconcile both fixed historical publications."""
    # The V1 builder already accepts a declared window and preserves all scientific rules.
    table, _ = build_national(calendar, monthly, regional, contract)
    table = cast_common(table, columns)
    old_end = str(national.year_month.max())
    old_contract = {
        **contract,
        "window": {
            **contract["window"],
            "end": old_end,
            "months": national.year_month.nunique(),
            "rows": len(national),
        },
    }
    old_calendar = calendar.loc[calendar.year_month.le(old_end)]
    old_monthly = monthly.loc[monthly.year_month.le(old_end)]
    frozen, _ = build_national(old_calendar, old_monthly, regional, old_contract)
    frozen = cast_common(frozen, columns)
    parity = compare_tables(frozen, national, label="national_v1_original_window")
    if any(r["current_dtype"] != r["reference_dtype"] for r in parity):
        raise ValueError("National V1 dtype mismatch")
    # Every unchanged common field must also agree on the full extended panel.
    edge_columns = {
        f"{n}{h}"
        for h in (1, 2)
        for n in (
            "p75_t",
            "y_t",
            "y_evaluable_t",
            "y_status_t",
            "onset_T",
            "future_dengue_count_t",
            "epidemiologically_eligible_t",
            "temporally_eligible_t",
            "g1_no_climate_t",
            "g1_with_climate_t",
        )
    }
    edge_report = []
    for name in national:
        common = table.loc[
            table.year_month.le(old_end), [*KEYS, name] if name not in KEYS else KEYS
        ]
        if name in KEYS:
            continue
        if name in edge_columns:
            h = int(name[-1])
            edge_keys = table.loc[table[f"target_period_t{h}"].gt(old_end), KEYS]
            compare_tables(
                common.merge(edge_keys, on=KEYS, how="left", indicator=True)
                .query('_merge == "left_only"')
                .drop(columns="_merge"),
                national.loc[national[f"target_period_t{h}"].le(old_end), [*KEYS, name]],
                label=f"national_v1_extended_{name}",
            )
            paired = common.merge(national[[*KEYS, name]], on=KEYS, suffixes=("_v4", "_v1"))
            diff = ~(
                paired[name + "_v4"].eq(paired[name + "_v1"])
                | (paired[name + "_v4"].isna() & paired[name + "_v1"].isna())
            ).fillna(False)
            edge_report.append(
                {
                    "column": name,
                    "changed_rows": int(diff.sum()),
                    "affected_origins": sorted(paired.loc[diff, "year_month"].unique().tolist()),
                    "classification": "necessary_panel_extension_maturity",
                    "cause": "2025 targets outside V1 are observed in the authorized V4 panel",
                }
            )
        else:
            compare_tables(common, national[[*KEYS, name]], label=f"national_v1_extended_{name}")
    regional_common = regional.loc[regional.year_month.between("2011-06", "2025-12")]
    parity += compare_tables(
        table, regional_common, label="regional_v1_Meta_Tolima", outcome_end="2025-12"
    )
    table, temporal = add_temporal_metadata(table)
    schema = [{**f, "nullable": bool(table[f["name"]].isna().any())} for f in columns]
    schema += [
        {"name": n, "dtype": str(table[n].dtype), "nullable": False, "role": "control"}
        for n in table
        if n not in {f["name"] for f in columns}
    ]
    return {
        "table": table,
        "columns": schema,
        "parity": parity,
        "edge_changes": edge_report,
        "temporal_roles": temporal,
    }
