"""Stage 2 graph contracts and independent negative input/publication cases."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest
from data_graph_fixture import synthetic_resolved as synthetic_resolved
from kedro.io import DatasetError

from sat_dengue.datasets import ConfigurationInputsDataset
from sat_dengue.datasets.stage2 import Stage2BundleDataset
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]


def test_data_synthetic_graph_publishes_counts_labels_and_exclusions(repo_tmp_path: Path) -> None:
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue.data.consolidation import CLIMATE_DAILY_VARIABLES
    from sat_dengue.datasets.stage2 import (
        PublishedConfigurationDataset,
        Stage2ConsolidatedDataset,
    )

    catalog_rows = [
        {
            "CODIGO_MUNICIPIO": f"{i:03}",
            "CODIGO_DEPARTAMENTO": department,
            "CODIGO_DPTO_MPIO": f"{department}{i:03}",
            "NOMBRE_MUNICIPIO": f"Town {department}{i:03}",
        }
        for department, count in [("50", 29), ("73", 47)]
        for i in range(1, count + 1)
    ]
    columns = ["COD_DPTO_R", "COD_MUN_R", "INI_SIN", "ANO"] + [f"field_{i}" for i in range(65)]
    raw = []
    for source in ["dengue.csv", "dengue_grave.csv"]:
        rows = []
        for year in range(2007, 2013):
            for _ in range(year - 2005 if source == "dengue.csv" else 1):
                rows.append(
                    {
                        **dict.fromkeys(columns, ""),
                        "COD_DPTO_R": "50",
                        "COD_MUN_R": "1",
                        "INI_SIN": f"01/01/{year}",
                        "ANO": str(year),
                    }
                )
        raw.append((source, pd.DataFrame(rows, columns=columns)))
    climate = pd.DataFrame(
        [
            {
                "date": f"{year}-01-{day:02}",
                "dpto_ccdgo": "50",
                "mpio_cdpmp": "50001",
                **dict.fromkeys(CLIMATE_DAILY_VARIABLES, "1.0"),
            }
            for year in range(2007, 2013)
            for day in range(1, 32)
        ]
    )
    construction = synthetic_resolved()["stage2"]["construction"]
    sources = {
        "construction": construction,
        "native_manifest": {"headers": {"epi_columns": columns}},
        "divipola": {"resultado": catalog_rows},
        "provenance": {"inputs": {}, "native_documents": {}},
    }
    directory = str(repo_tmp_path)
    storage = str(Path(directory) / "runs")
    datasets = {
        "configuration_inputs": MemoryDataset(ConfigurationInputsDataset().load()),
        "parameters": MemoryDataset({"profile": "data", "tracking": "disabled"}),
        "stage2_sources": MemoryDataset(sources),
        "stage2_epi_raw": MemoryDataset(iter(raw), copy_mode="assign"),
        "stage2_climate_raw": MemoryDataset(iter([climate]), copy_mode="assign"),
        "resolved_configuration": PublishedConfigurationDataset(str(Path(directory) / "config")),
        "stage2_consolidated": Stage2ConsolidatedDataset(storage),
        "stage2_bundle": Stage2BundleDataset(storage),
    }
    SequentialRunner().run(register_pipelines()["data"], DataCatalog(datasets))
    manifest = datasets["stage2_bundle"].load()
    folder = Path(storage) / manifest["run_id"] / "bundle"
    panel = pd.read_csv(folder / "panel.csv", dtype={"municipality_code": str})
    jan = panel[(panel["municipality_code"] == "50001") & (panel["year_month"] == "2012-01")].iloc[
        0
    ]
    assert jan["dengue_notifications_count"] == 7
    assert jan["p75_canal_t"] == 5
    assert jan["zona_canal_t"] == "EXCESO"
    absent = panel[panel["municipality_code"] == "50002"]
    assert absent["dengue_notifications_count"].eq(0).all()
    assert absent["rain_mm_month_sum"].isna().all()
    readiness = json.loads((folder / "readiness.json").read_text())
    assert readiness["eligible_rows"] == {"t1": 76, "t2": 76}
    assert readiness["real_fits"] == 0
    # Any payload corruption or added file invalidates the adapter's read.
    (folder / "extra").write_text("invalid")
    with pytest.raises(DatasetError, match="membership"):
        datasets["stage2_bundle"].load()
