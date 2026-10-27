"""Causal EXP03 additions; immutable EXP01 still owns onset labels and base features."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments import exp01
from sat_dengue.experiments.onset import partitions


def prepare(panel: pd.DataFrame, contract: dict[str, Any], horizon: int) -> pd.DataFrame:
    frame = exp01.prepare(panel, contract, horizon)
    counts = panel.set_index(
        ["municipality_code", "year_month"]
    ).dengue_notifications_count.to_dict()
    counts = {key: np.nan if pd.isna(value) else float(value) for key, value in counts.items()}
    thresholds, ratios = [], []
    for municipality, origin in frame[["municipality_code", "year_month"]].itertuples(
        index=False, name=None
    ):
        period = pd.Period(origin, freq="M")
        target = period + horizon
        reference = [
            pd.Period(year=target.year - n, month=target.month, freq="M") for n in range(1, 6)
        ]
        if any(month > period for month in reference):
            raise ValueError("Future reference in target thresholds")
        values = [counts.get((municipality, str(month)), np.nan) for month in reference]
        thresholds.append(np.quantile(values, [0.25, 0.75], method="linear"))
        history = [counts.get((municipality, str(period - 12 * n)), np.nan) for n in range(1, 6)]
        expected = float(np.mean(history))
        observed = float(counts[(municipality, origin)])
        ratios.append(
            observed / expected if expected > 0 else 0.0 if expected == observed == 0 else np.nan
        )
    frame[["channel_target_p25", "channel_target_p75"]] = np.asarray(thresholds)
    frame["sir_notification_ratio_t"] = ratios
    for suffix, zone in (("t", "zona_canal_t"), ("lag_1", "zona_canal_lag_1")):
        frame["channel_excess_" + suffix] = (
            frame[zone].eq("EXCESO").astype("Float64").where(frame[zone].notna())
        )
    frame["transmission_profile"] = pd.cut(
        frame.dengue_media_3m.astype(float),
        [-np.inf, 1, 10, np.inf],
        labels=["low", "medium", "high"],
    ).astype("string")
    return frame


def validate_design(design: dict[str, Any]) -> int:
    groups, variants = design["groups"], design["variants"]
    columns: list[str] = sum((groups[g] for g in design["variant_groups"]["full"]), [])
    all_columns: list[str] = sum(groups.values(), [])
    if (
        len(columns) != len(set(columns))
        or columns != design["predictors"]
        or len(all_columns) != len(columns)
        or set(all_columns) != set(columns)
    ):
        raise ValueError("Groups must be disjoint and exhaust full")
    if len(variants) != 10 or len({frozenset(v) for v in variants.values()}) != 10:
        raise ValueError("Ten unique predictor sets required; duplicate variant")
    for name, include in design["variant_groups"].items():
        if variants[name] != sum((groups[g] for g in include), []):
            raise ValueError("Variant group composition changed")
    if set(variants) != set(design["variant_groups"]):
        raise ValueError("Variant membership mismatch")
    base: list[str] = sum((groups[g] for g in ("history", "season", "context")), [])
    if any(not set(base) <= set(v) for v in variants.values()):
        raise ValueError("Every variant requires history, season and municipality")
    if set(design["inventory"]) != set(columns) or any(
        row["availability_offset_months"] > 0 for row in design["inventory"].values()
    ):
        raise ValueError("Missing provenance or future predictor")
    for group, names in groups.items():
        for name in names:
            row = design["inventory"][name]
            if row["group"] != group or any(
                not row.get(key) for key in ("source", "formula", "transform", "leakage_risk")
            ):
                raise ValueError("Incomplete predictor provenance")
    if len(design["contrasts"]) != 11 or len({c["id"] for c in design["contrasts"]}) != 11:
        raise ValueError("Eleven unique contrasts required")
    for c in design["contrasts"]:
        if c["left"] not in variants or c["right"] not in variants or c["left"] == c["right"]:
            raise ValueError("Unbound contrast")
    climate = next(c for c in design["contrasts"] if c["id"] == "full_without_climate")
    if climate != {
        "id": "full_without_climate",
        "left": "full",
        "right": "baseline_plus_complete_channel",
        "semantic_roles": {"right": "full_without_climate"},
    }:
        raise ValueError("Climate contrast must reuse canonical run")
    if variants["full"] != columns:
        raise ValueError("Full predictor union mismatch")
    years: set[int] = set()
    for window in design["windows"]:
        # Existing temporal validator forbids selection/fitting in 2024/2025.
        ends = [window[r] for r in ("train", "calibration", "selection", "evaluation")]
        if any(a[1] >= b[0] for a, b in zip(ends, ends[1:], strict=False)):
            raise ValueError("Temporal roles overlap")
        if any(a[1] >= "2024-01" for a in ends[:-1]) or ends[-1][1] >= "2025-01":
            raise ValueError("Reserved years in fitting/selection")
        if window["evidence_type"] == "retrospective_development":
            if ends[-1][1] >= "2024-01":
                raise ValueError("Stress in development")
            current = set(range(int(ends[-1][0][:4]), int(ends[-1][1][:4]) + 1))
            if years & current:
                raise ValueError("Duplicate development OOF years")
            years |= current
    if len(years) < 3:
        raise ValueError("Insufficient temporal support: need three development OOF years")
    return (
        len(variants) * len(design["families"]) * len(design["horizons"]) * len(design["windows"])
    )


def cohorts(
    panel: pd.DataFrame, contract: dict[str, Any], design: dict[str, Any]
) -> dict[tuple[int, str], Any]:
    validate_design(design)
    output = {}
    for h in design["horizons"]:
        frame = prepare(panel, contract, h)
        years, municipalities = set(), set()
        positive_years, positive_municipalities = set(), set()
        for window in design["windows"]:
            parts = partitions(frame, window)
            common = {
                r: f.loc[
                    f.onset_target.notna()
                    & f.excess_target.notna()
                    & f[design["predictors"]].notna().all(axis=1)
                ].copy()
                for r, f in parts.items()
            }
            if any(f.empty for f in common.values()) or any(
                common[r].onset_target.nunique() != 2 for r in ("train", "calibration")
            ):
                raise ValueError("Insufficient common coverage/classes before reservation or fits")
            if window["evidence_type"] == "retrospective_development":
                years.update(common["evaluation"].target_month.str[:4])
                municipalities.update(common["evaluation"].municipality_code)
                positives = common["evaluation"].loc[common["evaluation"].onset_target.eq(1)]
                positive_years.update(positives.target_month.str[:4])
                positive_municipalities.update(positives.municipality_code)
            output[h, window["id"]] = (parts, common)
        if len(years) < 3 or len(municipalities) < 2:
            raise ValueError("Insufficient temporal cluster support before reservation or fits")
        if len(positive_years) < 3 or len(positive_municipalities) < 2:
            raise ValueError("Insufficient onset cluster support before reservation or fits")
    return output


def coverage(
    frame: pd.DataFrame, columns: list[str], full: list[str] | None = None
) -> dict[str, Any]:
    valid = frame.onset_target.notna() & frame[columns].notna().all(axis=1)
    common = (
        frame.onset_target.notna()
        & frame.excess_target.notna()
        & frame[full or columns].notna().all(axis=1)
    )
    recovered = frame.loc[valid & ~common]

    def summarize(f: pd.DataFrame) -> dict[str, int]:
        return {
            "rows": len(f),
            "municipalities": f.municipality_code.nunique(),
            "months": f.target_month.nunique(),
        }

    return {
        **summarize(frame.loc[valid]),
        "recovered_rows": len(recovered),
        "recovered_municipalities": len(
            set(frame.loc[valid].municipality_code) - set(frame.loc[common].municipality_code)
        ),
        "recovered_months": len(
            set(frame.loc[valid].target_month) - set(frame.loc[common].target_month)
        ),
        "additional_municipality_months": len(recovered),
        "excluded_outcome": int(frame.onset_target.isna().sum()),
        "missing_predictors": {c: int(frame[c].isna().sum()) for c in columns},
        "by_department": {
            str(k): summarize(f)
            for k, f in frame.loc[valid].groupby(frame.loc[valid].municipality_code.str[:2])
        },
        "by_transmission_profile": {
            str(k): summarize(f) for k, f in frame.loc[valid].groupby("transmission_profile")
        },
    }
