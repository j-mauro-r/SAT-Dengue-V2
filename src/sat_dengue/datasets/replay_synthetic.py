"""Internally generated E2E fixtures; no private source or native evidence reads."""

from __future__ import annotations

from typing import Any

import pandas as pd  # type: ignore[import-untyped]


def stage2_fixture() -> tuple[dict[str, Any], Any, Any]:
    from sat_dengue.data.consolidation import CLIMATE_DAILY_VARIABLES, compute_schema_contract

    catalog = [
        {
            "CODIGO_MUNICIPIO": f"{i:03}",
            "CODIGO_DEPARTAMENTO": dept,
            "CODIGO_DPTO_MPIO": dept + f"{i:03}",
            "NOMBRE_MUNICIPIO": "Synthetic " + dept + f"{i:03}",
        }
        for dept, count in [("50", 29), ("73", 47)]
        for i in range(1, count + 1)
    ]
    columns = ["COD_DPTO_R", "COD_MUN_R", "INI_SIN", "ANO"] + [f"fixture_{i}" for i in range(65)]
    raw = []
    for source in ("dengue.csv", "dengue_grave.csv"):
        rows = []
        for m, dept in enumerate(("50", "73")):
            for index, month in enumerate(pd.period_range("2007-01", "2025-12", freq="M")):
                count = 1 if source == "dengue_grave.csv" else 1 + (index * (m + 1)) % 9
                for _ in range(count):
                    rows.append(
                        {
                            **dict.fromkeys(columns, ""),
                            "COD_DPTO_R": dept,
                            "COD_MUN_R": "1",
                            "INI_SIN": f"01/{month.month:02}/{month.year}",
                            "ANO": str(month.year),
                        }
                    )
        raw.append((source, pd.DataFrame(rows, columns=columns)))
    days = pd.date_range("2007-01-01", "2025-12-31")
    climate = pd.concat(
        [
            pd.DataFrame(
                {
                    "date": days.strftime("%Y-%m-%d"),
                    "dpto_ccdgo": municipality["CODIGO_DEPARTAMENTO"],
                    "mpio_cdpmp": municipality["CODIGO_DPTO_MPIO"],
                    **{name: (10 + days.month).astype(str) for name in CLIMATE_DAILY_VARIABLES},
                }
            )
            for municipality in catalog
        ],
        ignore_index=True,
    )
    sources = {
        "construction": compute_schema_contract(
            [], pd.DataFrame(), version="candidate-construction-v1"
        ),
        "native_manifest": {"headers": {"epi_columns": columns}},
        "divipola": {"resultado": catalog},
        "provenance": {"inputs": {}, "native_documents": {}},
    }
    return sources, iter(raw), iter([climate])


def fit_fixture_preparers(
    inputs: dict[str, Any], sources: dict[str, Any], tracking: str
) -> dict[str, Any]:
    """The existing train-only fixture boundary; sixteen synthetic state fits only."""
    from sat_dengue.training_preparation import workflow
    from sat_dengue.training_preparation.preprocessing import PreparerSpec
    from sat_dengue.training_preparation.serialization import bytes_record, json_bytes

    saved: dict[str, Any] = {"states": {}, "provenance": {}}
    resolved = workflow.resolve_preparation_configuration(
        inputs, {"profile": "preparation", "tracking": tracking}, sources, saved
    )
    keys, features = workflow.features(sources, resolved)
    controls, _ = workflow.eligibility(sources, resolved)
    producer, consumer = workflow.boundaries(resolved)
    windows = workflow.partitions(keys, features, controls, sources, resolved, producer, consumer)
    for window, entry in windows.items():
        saved["states"][window] = {}
        for name, spec in sources["contract"]["temporal_preparation"]["profiles"].items():
            train = entry["splits"]["train"]
            saved["states"][window][name] = workflow.fit_training_partition(
                train["X"],
                train["controls"],
                PreparerSpec(**spec),
                list(train["X"]),
                int(window[-1]),
                producer[window],
                "train",
            )
    saved["provenance"]["state_files"] = {
        f"{w}_{n}_preparer.json": bytes_record(json_bytes(state))
        for w, states in saved["states"].items()
        for n, state in states.items()
    }
    return saved


def saved_fixture_inference(
    sources: dict[str, Any], cohorts: dict[str, Any], resolved: dict[str, Any]
) -> dict[str, Any]:
    """Apply actual native synthetic training components to both fixture horizons.

    The existing bounded training fixture fits T+1 models only. Reusing their
    feature-compatible states for T+2 here tests interfaces, never scientific parity.
    """
    from sat_dengue.final_evaluation.workflow import validate_sources
    from sat_dengue.model_training.candidate_families import restore_model

    validate_sources(sources, resolved)
    result = {}
    for procedure in sources["proposal"]["procedures"]:
        family = procedure["candidate"]
        component = sources["e2e_components"][family]
        fitted = restore_model(family, component["model"], component["preparer"])
        cohort = cohorts["cohorts"][procedure["horizon"]]
        result[f"{family}_t{procedure['horizon']}"] = fitted.predict(cohort.X).astype("Float64")
    return result
