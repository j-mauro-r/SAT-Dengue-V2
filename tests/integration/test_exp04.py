from __future__ import annotations

import json
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments.exp04_baseline import audit_baseline, common_exposure, paired_support


def score_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "municipality_code": ["50001", "73001", "50001", "73001"],
            "target_month": ["2019-01", "2019-01", "2019-02", "2019-02"],
            "raw_score": [0.1, 0.3, 0.6, 0.8],
            "truth": [0, 0, 1, 1],
            "error_class": ["no_excess", "no_excess", "onset", "onset"],
        }
    )


def test_baseline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Control 2: preserve mandatory M00 and identical common-cohort exposure."""
    monkeypatch.chdir(tmp_path)
    missing = audit_baseline()
    assert missing["status"] == "BLOCKED_BASELINE"
    assert missing["reconstruction_identity"] is None
    directory = Path("tmp/baseline")
    directory.mkdir(parents=True)
    (directory / "bundle.json").write_text(json.dumps({"source_variant": "M00"}))
    (directory / "manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="exact original"):
        audit_baseline(directory)
    with pytest.raises(ValueError, match="repository-local"):
        audit_baseline(Path("/etc"))
    frame = score_frame()
    assert common_exposure(frame) == 4 / 12
    assert paired_support(frame, frame.iloc[::-1])["common_exposure"] == 4 / 12
    assert paired_support(frame, frame.iloc[:3])["status"] == "NOT_EVALUABLE"
    changed = frame.copy()
    changed.loc[0, "truth"] = 1
    assert paired_support(frame, changed)["status"] == "NOT_EVALUABLE"
    with pytest.raises(ValueError, match="duplicate"):
        common_exposure(pd.concat([frame, frame]))
    later = frame.copy()
    later.loc[0, "target_month"] = "2025-01"
    with pytest.raises(ValueError, match="2025"):
        common_exposure(later)
