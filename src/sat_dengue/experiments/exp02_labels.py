"""Ciencia pura de etiquetas y episodios; no realiza I/O ni ajustes."""

from __future__ import annotations

import itertools
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.consolidation import (
    compute_current_endemic_channel,
    history_periods_for_target,
)
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.onset import KEYS, validate_keys

HISTORY_YEARS = (5, 7, 9)


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convierte tipos pandas/nulos a JSON finito para publicación local."""
    import json

    return list(json.loads(frame.to_json(orient="records", double_precision=15)))


def episodes(states: pd.DataFrame, years: int) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Identifica secuencias calendáricas máximas, conservando censura y duración."""
    validate_keys(states)
    frame = states.sort_values(KEYS).reset_index(drop=True).copy()
    lookup = frame.set_index(KEYS).excess.to_dict()
    previous = pd.Series(
        [
            lookup.get((m, str(pd.Period(t, freq="M") - 1)), pd.NA)
            for m, t in frame[KEYS].itertuples(index=False, name=None)
        ],
        dtype="Int64",
    )
    frame["onset"] = (frame.excess.eq(1) & previous.eq(0)).astype("Int64")
    frame.loc[previous.isna() | frame.excess.isna(), "onset"] = pd.NA
    frame["episode_id"] = pd.Series([None] * len(frame), dtype="string")
    frame["episode_duration"] = pd.Series([pd.NA] * len(frame), dtype="Int64")
    frame["episode_censored"] = False
    output: list[dict[str, Any]] = []
    for municipality, group in frame.groupby("municipality_code", sort=True):
        active: list[int] = []

        def finish(active: list[int] = active, municipality: str = str(municipality)) -> None:
            if not active:
                return
            start, end = (
                str(frame.loc[active[0], "year_month"]),
                str(frame.loc[active[-1], "year_month"]),
            )
            prior = lookup.get((municipality, str(pd.Period(start, freq="M") - 1)), pd.NA)
            following = lookup.get((municipality, str(pd.Period(end, freq="M") + 1)), pd.NA)
            identifier = f"{municipality}:{start}:{years}"
            item = {
                "municipality_code": str(municipality),
                "history_years": years,
                "episode_id": identifier,
                "start": start,
                "end": end,
                "observed_duration": len(active),
                "left_censored": bool(pd.isna(prior)),
                "right_censored": bool(pd.isna(following)),
                "confirmed_onset": bool(not pd.isna(prior) and prior == 0),
                "confirmed_end": bool(not pd.isna(following) and following == 0),
            }
            output.append(item)
            frame.loc[active, "episode_id"] = identifier
            frame.loc[active, "episode_duration"] = len(active)
            frame.loc[active, "episode_censored"] = item["left_censored"] or item["right_censored"]
            active.clear()

        for index, row in group.iterrows():
            positive = not pd.isna(row.excess) and row.excess == 1
            contiguous = (
                not active
                or pd.Period(row.year_month, freq="M")
                == pd.Period(frame.loc[active[-1], "year_month"], freq="M") + 1
            )
            if not positive or not contiguous:
                finish()
            if positive:
                active.append(int(index))
        finish()
    return frame, output


def construct_variants(
    panel: pd.DataFrame, years: tuple[int, ...] = HISTORY_YEARS
) -> dict[int, dict[str, Any]]:
    """Reutiliza canal parametrizable; descarta toda columna heredada de etiquetas."""
    validate_keys(panel)
    if tuple(years) != HISTORY_YEARS:
        raise ValueError("EXP02 requiere las ventanas congeladas5/7/9")
    if (
        not panel.year_month.str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all()
        or panel.year_month.ge("2025-01").any()
    ):
        raise ValueError("Calendario inválido o2025consumido")
    source = panel[KEYS + ["dengue_notifications_count"]].sort_values(KEYS).reset_index(drop=True)
    values = (
        pd.to_numeric(source.dengue_notifications_count, errors="raise")
        .dropna()
        .to_numpy(dtype=float)
    )
    if not np.isfinite(values).all() or (values < 0).any() or (values % 1 != 0).any():
        raise ValueError("Conteos inválidos")
    lookup = source.set_index(KEYS).dengue_notifications_count.to_dict()
    variants = {}
    for history in years:
        channel, trace, _ = compute_current_endemic_channel(source, history_years=history)
        states = channel[KEYS].copy()
        states["excess"] = channel.zona_canal_t.map(
            {"EXITO": 0, "SEGURIDAD": 0, "ALERTA": 0, "EXCESO": 1}
        ).astype("Int64")
        states["p75"] = channel.p75_canal_t
        states["p75_zero"] = states.p75.eq(0) & states.p75.notna()
        states["history_available"] = trace.history_valid_years
        states["non_evaluable_reason"] = trace.canal_status
        zeros = []
        for m, t in states[KEYS].itertuples(index=False, name=None):
            past = [lookup.get((m, v), pd.NA) for v in history_periods_for_target(t, 5)]
            zeros.append(
                sum(not pd.isna(v) and v == 0 for v in past) / 5
                if all(not pd.isna(v) for v in past)
                else None
            )
        states["baseline_zero_fraction"] = zeros
        states, event_rows = episodes(states, history)
        variants[history] = {"states": states, "episodes": event_rows}
    return variants


def episode_overlap(left: pd.DataFrame, right: pd.DataFrame, mask: pd.Series) -> dict[str, int]:
    """Cuenta fragmentación/unión por solapamiento en el soporte común declarado."""
    a, b = left.loc[mask, "episode_id"], right.loc[mask, "episode_id"]
    edges = set(zip(a[a.notna() & b.notna()], b[a.notna() & b.notna()], strict=True))
    left_ids, right_ids = set(a.dropna()), set(b.dropna())

    def censored(frame: pd.DataFrame) -> set[str]:
        return set(frame.loc[frame.episode_censored, "episode_id"].dropna())

    left_censored, right_censored = censored(left), censored(right)
    fragmented = {value for value in left_ids if sum(x == value for x, _ in edges) > 1}
    merged = {value for value in right_ids if sum(y == value for _, y in edges) > 1}
    ambiguous_f = {
        value
        for value in fragmented
        if value in left_censored or any(y in right_censored for x, y in edges if x == value)
    }
    ambiguous_m = {
        value
        for value in merged
        if value in right_censored or any(x in left_censored for x, y in edges if y == value)
    }
    return {
        "reference_episodes": len(left_ids),
        "variant_episodes": len(right_ids),
        "fragmented_reference_episodes": len(fragmented - ambiguous_f),
        "merged_variant_episodes": len(merged - ambiguous_m),
        "ambiguous_fragmentation": len(ambiguous_f),
        "ambiguous_merging": len(ambiguous_m),
        "reference_without_overlap": sum(not any(x == v for x, _ in edges) for v in left_ids),
        "variant_without_overlap": sum(not any(y == v for _, y in edges) for v in right_ids),
    }


def compare_stability(
    variants: dict[int, dict[str, Any]], design: dict[str, Any]
) -> dict[str, Any]:
    """Resume cobertura, cambios pareados y episodios sin escoger una ventana."""
    frames = {h: variants[h]["states"] for h in HISTORY_YEARS}
    base = frames[5]
    if any(not f[KEYS].equals(base[KEYS]) for f in frames.values()):
        raise ValueError("Claves desalineadas entre definiciones")
    common = {
        label: pd.concat([f[label].notna() for f in frames.values()], axis=1).all(axis=1)
        for label in ("excess", "onset")
    }
    children, pairs, breakdowns, paired_groups = [], [], [], []
    for window in design["windows"]:
        period_mask = base.year_month.between(*window["evaluation"])
        for history, frame in frames.items():

            def summarize(mask: pd.Series, frame: pd.DataFrame = frame) -> dict[str, Any]:
                s, onset_mask = mask & common["excess"], mask & common["onset"]
                selected = frame.loc[mask]
                return {
                    "rows": int(mask.sum()),
                    "state_evaluable_rows": int((mask & frame.excess.notna()).sum()),
                    "onset_evaluable_rows": int((mask & frame.onset.notna()).sum()),
                    "common_state_rows": int(s.sum()),
                    "common_onset_rows": int(onset_mask.sum()),
                    "excess_positive_rows": int(frame.loc[s, "excess"].sum()),
                    "onset_count": int(frame.loc[onset_mask, "onset"].sum()),
                    "episode_count": int(frame.loc[s, "episode_id"].nunique()),
                    "p75_zero_rows": int(selected.p75_zero.sum()),
                    "non_evaluable_reasons": {
                        str(k): int(v)
                        for k, v in selected.non_evaluable_reason.value_counts().items()
                    },
                    "common_keys_sha256": digest(records(base.loc[s, KEYS])),
                }

            children.append(
                {
                    "layer": "labels",
                    "history_years": history,
                    "window": window["id"],
                    "evidence_type": window["evidence_type"],
                    **summarize(period_mask),
                }
            )
            groups = {
                "municipality": base.municipality_code,
                "department": base.municipality_code.str[:2],
                "target_year": base.year_month.str[:4],
                "zero_heavy": base.baseline_zero_fraction.gt(0.5)
                .astype(str)
                .where(base.baseline_zero_fraction.notna(), "unknown"),
                "p75_zero": frame.p75_zero.astype(str).where(frame.p75.notna(), "unknown"),
                "insufficient_history": frame.non_evaluable_reason.eq(
                    "insufficient_history"
                ).astype(str),
            }
            for dimension, group in groups.items():
                for value in sorted(group.loc[period_mask].unique()):
                    breakdowns.append(
                        {
                            "history_years": history,
                            "window": window["id"],
                            "dimension": dimension,
                            "group": value,
                            **summarize(period_mask & group.eq(value)),
                        }
                    )
        for left_h, right_h in itertools.combinations(HISTORY_YEARS, 2):
            left, right = frames[left_h], frames[right_h]

            def paired(
                mask: pd.Series, left: pd.DataFrame = left, right: pd.DataFrame = right
            ) -> dict[str, Any]:
                item: dict[str, Any] = {}
                for label in ("excess", "onset"):
                    selected = mask & common[label]
                    a, b = left.loc[selected, label], right.loc[selected, label]
                    changed = int(a.ne(b).sum())
                    item[label] = {
                        "paired_rows": int(selected.sum()),
                        "changed": changed,
                        "excluded_rows": int((mask & ~common[label]).sum()),
                        "change_rate": changed / int(selected.sum()) if selected.any() else None,
                        "zero_to_one": int((a.eq(0) & b.eq(1)).sum()),
                        "one_to_zero": int((a.eq(1) & b.eq(0)).sum()),
                        "cohort_sha256": digest(records(base.loc[selected, KEYS])),
                        "uncertainty": change_interval(
                            base.loc[selected, KEYS],
                            a.ne(b).to_numpy(dtype=float),
                            seed=design["seed"],
                        ),
                    }
                item["episodes"] = episode_overlap(left, right, mask & common["excess"])
                return item

            identity = {"reference_years": left_h, "variant_years": right_h, "window": window["id"]}
            pairs.append({**identity, **paired(period_mask)})
            # All paired strata use one fixed five-year definition, even for 7 vs 9.
            fixed_groups = {
                "municipality": base.municipality_code,
                "department": base.municipality_code.str[:2],
                "target_year": base.year_month.str[:4],
                "zero_heavy": base.baseline_zero_fraction.gt(0.5)
                .astype(str)
                .where(base.baseline_zero_fraction.notna(), "unknown"),
                "p75_zero": base.p75_zero.astype(str).where(base.p75.notna(), "unknown"),
                "insufficient_history": base.non_evaluable_reason.eq("insufficient_history").astype(
                    str
                ),
            }
            for dimension, group in fixed_groups.items():
                for value in sorted(group.loc[period_mask].unique()):
                    paired_groups.append(
                        {
                            **identity,
                            "stratum_definition": "five_year_reference",
                            "dimension": dimension,
                            "group": value,
                            **paired(period_mask & group.eq(value)),
                        }
                    )

    return {
        "children": children,
        "pairs": pairs,
        "by_group": breakdowns,
        "paired_by_group": paired_groups,
        "epidemic_axis": "pending_scientific_definition",
        "automatic_window_selection": False,
    }


def change_interval(
    keys: pd.DataFrame, changed: np.ndarray, *, seed: int, repeats: int = 1000
) -> dict[str, Any]:
    """Remuestrea claves pareadas por municipio/año sin reconstruir episodios."""
    if len(keys) != len(changed) or not np.isin(changed, [0, 1]).all():
        raise ValueError("Cambios pareados inválidos")
    municipalities = keys.municipality_code.unique()
    years = keys.year_month.str[:4].unique()
    if len(municipalities) < 2 or len(years) < 2:
        return {"status": "insufficient_cluster_support", "interval": None}
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(repeats):
        positions: list[int] = []
        for municipality in rng.choice(municipalities, len(municipalities), replace=True):
            for year in rng.choice(years, len(years), replace=True):
                positions.extend(
                    np.flatnonzero(
                        (keys.municipality_code == municipality)
                        & keys.year_month.str.startswith(year)
                    )
                )
        if positions:
            values.append(float(changed[positions].mean()))
    return {
        "status": "retrospective_paired",
        "interval": np.quantile(values, [0.025, 0.975]).tolist() if values else None,
    }
