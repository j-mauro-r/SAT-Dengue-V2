"""Generated complete source identities for EXP01 admission and integration tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_preparation.contract import CONTRACT_PATH, PreparationConfig
from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint

ROOT = Path(__file__).resolve().parents[2]


def generated_panel(start: str = "2010-01", end: str = "2025-02") -> pd.DataFrame:
    """Generate declared columns with valid raw/coverage values and unused targets."""
    contract = json.loads((ROOT / CONTRACT_PATH).read_text())
    rng = np.random.default_rng(130)
    rows = []
    for code in ("50001", "73001"):
        for period in pd.period_range(start, end, freq="M"):
            row: dict[str, Any] = {
                f["name"]: (
                    None
                    if f["nullable"]
                    else False
                    if f["dtype"].lower() == "bool"
                    else 0
                    if f["dtype"].lower() in ("float64", "int64")
                    else ""
                )
                for f in contract["schema"]
            }
            count, grave = int(rng.integers(0, 100)), int(rng.integers(0, 5))
            row.update(
                municipality_code=code,
                department_code=code[:2],
                municipality_name="Generated",
                year_month=str(period),
                dengue_notifications_count=count,
                dengue_grave_notifications_count=grave,
                total_notifications_count=count + grave,
                in_epi_coverage=True,
                epi_count_status="records_present" if count + grave else "zero_in_coverage",
                climate_days_observed=period.days_in_month,
                expected_days_in_month=period.days_in_month,
            )
            for column in row:
                if column.endswith("_valid_days"):
                    row[column] = period.days_in_month
                    row[column.removesuffix("_valid_days")] = float(rng.uniform(-2, 5))
            for h in (1, 2):
                row[f"target_period_t{h}"] = str(period + h)
                row[f"y_evaluable_t{h}"] = False
                row[f"y_status_t{h}"] = "insufficient_history"
            rows.append(row)
    return pd.DataFrame(rows)


def write_sources(root: Path, panel: pd.DataFrame) -> PreparationConfig:
    """Write a complete manifest with fresh hashes for this particular CSV variant."""
    config = PreparationConfig(root)
    contract = json.loads((ROOT / CONTRACT_PATH).read_text())
    config.resolve(CONTRACT_PATH).parent.mkdir(parents=True, exist_ok=True)
    config.resolve(CONTRACT_PATH).write_text(json.dumps(contract))
    upstream = contract["upstream_contract_path"]
    paths = {
        "dengue_y_dengue_grave": "data/processed/dengue_y_dengue_grave.csv",
        "panel_mensual_dengue_clima": contract["panel_path"],
        "candidate_contract": upstream,
        "y_label_history_traceability": (
            "data/interim/stage2_consolidated_dataset_pipeline/y_label_history_traceability.csv"
        ),
        "current_endemic_channel_traceability": (
            "data/interim/stage2_consolidated_dataset_pipeline/"
            "current_endemic_channel_traceability.csv"
        ),
    }
    records = {}
    for key, relative in paths.items():
        path = config.resolve(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        if key == "panel_mensual_dengue_clima":
            panel.to_csv(path, index=False)
        elif key == "candidate_contract":
            path.write_text(
                json.dumps(
                    {"datasets": {"panel_mensual_dengue_clima": {"schema": contract["schema"]}}}
                )
            )
        else:
            path.write_text("generated,fixture\n")
        records[key] = {"path": relative, **fingerprint(path)}
    records["panel_mensual_dengue_clima"].update(rows=len(panel), columns=len(panel.columns))
    start, end = str(panel.year_month.min()), str(panel.year_month.max())
    coverage = dict(
        panel_month_start=start,
        panel_month_end=end,
        epi_coverage_start_month=start,
        epi_coverage_end_month=end,
        climate_coverage_start_month=start,
        climate_coverage_end_month=end,
        scope_municipalities=2,
    )
    config.resolve(config.manifest_path).write_text(
        json.dumps({"outputs": records, "coverage": coverage})
    )
    catalog = config.resolve("data/sources/Divipola-municipios.md")
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        json.dumps(
            {
                "resultado": [
                    {"CODIGO_DPTO_MPIO": code, "CODIGO_DEPARTAMENTO": code[:2]}
                    for code in ("50001", "73001")
                ]
            }
        )
    )
    return config
