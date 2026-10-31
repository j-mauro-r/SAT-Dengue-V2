from __future__ import annotations

import hashlib
import json

from sat_dengue.experiments.exp04_contract import ROOT, protocol


def test_design() -> None:
    """Control 1: bind the technical slice to the full design and user decisions."""
    p = protocol()
    assert json.loads((ROOT / "protocol.json").read_text()) == p
    assert hashlib.sha256((ROOT / "DESING.md").read_bytes()).hexdigest() == p["design_sha256"]
    assert set(p["arms"]) == {"A0", "A1", "A2", "A3", "A4", "B0", "B1", "B2", "C0", "C1", "C2", "D"}
    assert [p["arms"][a]["window_months"] for a in ("A1", "A2", "A3")] == [12, 24, 36]
    assert p["contrasts"]["H1b"] == [["B1", "B0"], ["B2", "B0"]]
    assert p["contrasts"]["H1c"] == [["C1", "C0"], ["C2", "C0"]]
    assert p["objectives"] == {"onset": [1, 2], "excess_control": [2]}
    assert p["baseline"]["source_variant"] == "M00"
    assert not any(
        p["baseline"][k]
        for k in ("allow_refit", "allow_substitution", "allow_probability_inversion")
    )
    assert p["exposure"]["primary"] == "common"
    assert p["exposure"]["historical_rate_is_not_primary"]
    assert p["cuts"]["not_evaluable"] == [2025]
    assert p["unresolved_scientific_inputs"]
    assert p["scientific_execution_authorized"] is False
    assert (p["G5"], p["champion"]) == ("NOT_APPROVED", "not_selected")
