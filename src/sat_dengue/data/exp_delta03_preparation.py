"""Pure no-fit preparation reports; unresolved source evidence withholds affected matrices."""

from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.exp_delta03 import (
    KEYS,
    block_views,
    comparison_masks,
    h5_labels,
    land_cover,
    prepare_features,
    temporal_roles,
)
from sat_dengue.data.exp_delta03_quality import profile


def quality(sources: dict[str, Any]) -> dict[str, Any]:
    return profile(sources["frame"], sources["dictionary"], sources["contract"])


def prepare(sources: dict[str, Any], reports: dict[str, Any]) -> dict[str, Any]:
    """Return diagnostic products, never disguise unadmitted all-null blocks as matrices."""
    frame = sources["frame"]
    contract = sources["contract"]
    features, manifest = prepare_features(frame, contract)
    views = block_views(manifest, contract["variants"])
    candidate = h5_labels(frame, pd.to_numeric(frame.notificados_210))
    cohorts = []
    for h in (1, 2):
        for year in contract["evaluation_years"]:
            roles = temporal_roles(frame, year, h)
            for scope in ["national", "meta", "tolima"]:
                geo = (
                    pd.Series(True, index=frame.index)
                    if scope == "national"
                    else frame.divipola_departamento.eq("50" if scope == "meta" else "73")
                )
                for role in ["train", "calibration", "embargo", "selection", "evaluation"]:
                    mask = roles.eq(role) & geo & candidate[f"eligible_T{h}"]
                    cohorts.append(
                        {
                            "horizon": h,
                            "year": year,
                            "scope": scope,
                            "role": role,
                            "candidate_rows": int(mask.sum()),
                            "candidate_onsets": int(candidate.loc[mask, f"onset_T{h}"].sum()),
                            "status": "UNRESOLVED_count_mapping_not_historical_cohort_equivalence",
                        }
                    )
    parity = sources.get(
        "historical_comparison", {"status": "UNRESOLVED_no_verified_historical_source"}
    )
    if "baseline" in sources:
        baseline = sources["baseline"]
        joined = frame.merge(
            baseline,
            left_on=KEYS,
            right_on=["municipality_code", "year_month"],
            how="inner",
            validate="one_to_one",
        )
        comparisons = []
        for new, old in [
            ("notificados_210", "dengue_notifications_count"),
            ("notificados_220", "dengue_grave_notifications_count"),
        ]:
            a = pd.to_numeric(joined[new])
            b = pd.to_numeric(joined[old])
            equal = a.eq(b) | (a.isna() & b.isna())
            comparisons.append(
                {
                    "new_field": new,
                    "historical_field": old,
                    "common_rows": len(joined),
                    "different_values": int((~equal).sum()),
                    "new_missing": int(a.isna().sum()),
                    "historical_missing": int(b.isna().sum()),
                }
            )
        parity = {
            "status": "UNRESOLVED",
            "comparison": comparisons,
            "interpretation": (
                "Numerical equality alone cannot approve event/date/absence "
                "semantics; mapping and exact role/key/label parity still required."
            ),
        }
    lc = land_cover(frame, contract)
    availability = {
        "status": "UNVERIFIED",
        "proof_records": len(contract["availability_evidence"]),
        "features": [
            {
                "name": m["name"],
                "decision": m["decision"],
                "eligible_rows": m["eligible_rows"],
                "rows": len(frame),
            }
            for m in manifest
        ],
        "rule": (
            "Release date and source vintage must precede origin. Coverage is not"
            " publication evidence."
        ),
        "mosaic": "Separate audit-only group, no assignment to natural vegetation/agriculture.",
        "water": "No rows after 2021; observed area > 0; no structural flags in X.",
    }
    descriptors = {
        name: {
            "columns": columns,
            "population": "WATER_COMMON_all_roles"
            if name == "FULL_PLUS_SURFACE_WATER"
            else "ERA5_COMMON_all_roles"
            if name == "FULL_ERA5_PRECIPITATION"
            else "PRIMARY_COMMON",
            "status": "WITHHELD",
            "reason": (
                "H5/cohort correspondence and historical release evidence unresolved;"
                " LAND_COVER composition unresolved"
            ),
            "column_contract_only": True,
            "data_file": None,
        }
        for name, columns in views.items()
    }
    populations = []
    for h in contract["horizons"]:
        for year in contract["evaluation_years"]:
            masks = comparison_masks(frame, candidate, features, year, h, labels_admitted=False)
            for role, pairs in masks.items():
                for name, mask in pairs.items():
                    keys = frame.loc[mask, KEYS].to_csv(index=False, lineterminator="\n").encode()
                    populations.append(
                        {
                            "horizon": h,
                            "year": year,
                            "role": role,
                            "member": name,
                            "rows": int(mask.sum()),
                            "ordered_keys_sha256": hashlib.sha256(keys).hexdigest(),
                            "status": "WITHHELD_H5_UNRESOLVED_not_zero_observed_support",
                        }
                    )
    transfer = [p for p in populations if p["member"] == "TRANSFER_EXCLUDE_META_TOLIMA"]
    return {
        "quality": reports,
        "transformations": manifest,
        "availability": availability,
        "cohorts": cohorts,
        "labels": {
            "status": "UNRESOLVED",
            "count_source_candidate_only": "notificados_210",
            "source_mapping_authorized": False,
            "definition": "T1: E(T)=0,E(T+1)=1; T2: E(T)=0,E(T+1)=0,E(T+2)=1",
            "H5": "five exact preceding same-month years; type7 P75; counts>P75",
            "candidate_nonmissing_onset_T1": int(candidate.onset_T1.notna().sum()),
            "candidate_nonmissing_onset_T2": int(candidate.onset_T2.notna().sum()),
            "historical_correspondence": parity,
        },
        "blocks": descriptors,
        "paired_populations": populations,
        "transfer_geography": transfer,
        "land_cover_audit": {
            "groups": list(lc),
            "rows_with_all_groups": int(lc.notna().all(axis=1).sum()),
            "sum_outside_100_tolerance_1e_4": int(
                (lc.sum(axis=1, min_count=len(lc.columns)) - 100).abs().gt(1e-4).sum()
            ),
            "predictive_vector": "UNRESOLVED",
        },
        "leakage": {
            "event_time_operators": "strict T-1 or older, ONI central T-2; exact calendar windows",
            "learned_reference": (
                "seasonal_anomaly takes explicit training mask; no whole-panel fitting"
            ),
            "availability_guard": "unknown proof -> ineligible; all affected matrices withheld",
            "forbidden_X": (
                "keys/year/targets/structural coverage strings never in closed selectors"
            ),
            "fits": 0,
            "calibrations": 0,
            "mlflow_writes": 0,
        },
        "readiness": {
            "phase1_complete": False,
            "status": "BLOCKED_SCIENTIFIC_ADMISSION",
            "matrix_files_published": 0,
            "blockers": [
                "210/220 date/count/absence mapping to historical source is unapproved",
                "H5 and exact frozen cohort/role parity not demonstrated",
                "historical environmental/demographic/annual vintages not demonstrated",
                "MODIS mixed mosaic and final compositional predictor vector unresolved",
            ],
            "next_decision": (
                "Approve a bounded historical source correspondence study or supply "
                "matched source/vintage evidence; no final matrix, training or Phase "
                "2 authorization inferred."
            ),
        },
        "prepared_base": {
            "rows": len(features),
            "feature_contract_columns": len(manifest),
            "persisted": False,
            "reason": (
                "Do not publish all-null placeholder arms or unverified labels as final matrices."
            ),
        },
    }
