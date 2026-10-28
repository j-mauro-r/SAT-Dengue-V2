from __future__ import annotations

import copy
import json

import pytest
import yaml  # type: ignore[import-untyped]

from sat_dengue.experiments import exp03_1_contract as contract


def test_canonical_protocol_matrix_and_counts() -> None:
    protocol = contract.protocol()
    assert json.loads(contract.PROTOCOL.read_text()) == protocol
    assert yaml.safe_load(contract.MATRIX.read_text()) == contract.matrix(protocol)
    assert contract.counts(protocol) == {
        "onset_cells": 72,
        "excess_control_cells": 24,
        "maximum_refit_cells": 96,
        "terminal_cells": 24,
        "maximum_reused_m00_cells": 36,
        "maximum_new_fit_cells_with_complete_reuse": 60,
    }


def test_contract_has_no_redundant_predictors_or_2025() -> None:
    protocol = contract.protocol()
    assert protocol["experiment_id"] == "EXP031"
    assert protocol["scientific_id"] == "EXP03.1"
    predictors = protocol["predictors"]
    assert len(predictors["recent"] + predictors["change"]) == 6
    assert not set(predictors["forbidden"]) & set(predictors["recent"] + predictors["change"])
    assert protocol["governance"]["year_2025"] == "REJECTED"
    assert protocol["governance"]["G5"] == "NOT_APPROVED"
    assert protocol["governance"]["champion"] == "not_selected"


def test_tampered_contract_changes_identity_and_matrix() -> None:
    protocol = contract.protocol()
    changed = copy.deepcopy(protocol)
    changed["budget"]["B_primary"] = 2.0
    assert contract.digest(changed) != contract.digest(protocol)
    assert contract.matrix(changed)["protocol_sha256"] == contract.digest(changed)


@pytest.mark.parametrize("variant", ["M00", "M01", "M02"])
def test_each_variant_has_exact_onset_grid(variant: str) -> None:
    rows = [
        row for row in contract.cells() if row["variant"] == variant and row["objective"] == "onset"
    ]
    assert len(rows) == 24
