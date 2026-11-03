"""Generated-only checks for the bounded recovery's numerical and no-write fences."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from sat_dengue.datasets.legacy_preparation.contract import PreparationError
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle, verify_bundle
from scripts.recover_exp_delta01_selection import (
    ACCEPTANCE,
    checked,
    fingerprint,
    no_fitting,
    probability_audit,
)


def test_strict_tolerance_reports_small_and_material_discrepancies() -> None:
    expected = np.array([0.1, 0.5, 0.9])
    actual = expected.copy()
    actual[0] = np.nextafter(actual[0], 1.0)
    actual[1] += 1e-12
    result = probability_audit(actual, expected)
    assert ACCEPTANCE["relative_tolerance"] == 0.0
    assert ACCEPTANCE["absolute_tolerance"] == 1e-15
    assert result["nonidentical_probabilities"] == 2
    assert result["exceeding_tolerance"] == 1
    assert result["status"] == "FAIL"
    with pytest.raises(ValueError, match="Nonfinite"):
        probability_audit([float("nan")], [0.5])
    with pytest.raises(ValueError, match="support"):
        probability_audit([0.2, 0.5], [0.5])


def test_source_tampering_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "source.json"
    path.write_bytes(b"original")
    original = fingerprint(path)
    path.write_bytes(b"modified")
    with pytest.raises(ValueError, match="Identity mismatch"):
        checked(path, original, {})


def test_training_calibration_and_policy_selection_are_blocked() -> None:
    import xgboost as xgb

    from sat_dengue.experiments import exp_beta01 as beta

    with no_fitting():
        operations: tuple[Callable[..., Any], ...] = (
            xgb.train,
            xgb.XGBClassifier().fit,
            beta.fit_intercept,
            beta.fit_adaptation,
            beta.thresholds,
        )
        for operation in operations:
            with pytest.raises(RuntimeError, match="forbidden"):
                operation()


def test_publication_rejects_overwrite_and_corrupt_reuse(tmp_path: Path) -> None:
    identity = "a" * 64
    payloads = {"selection.csv": b"generated test fixture\n"}
    target = publish_bundle(tmp_path, identity, payloads, existing_policy="error")
    with pytest.raises(PreparationError, match="already exists"):
        publish_bundle(tmp_path, identity, payloads, existing_policy="error")
    with pytest.raises(PreparationError, match="stale or corrupted"):
        publish_bundle(tmp_path, identity, {"selection.csv": b"changed\n"})
    verify_bundle(target, payloads)
    assert publish_bundle(tmp_path, identity, payloads) == target
