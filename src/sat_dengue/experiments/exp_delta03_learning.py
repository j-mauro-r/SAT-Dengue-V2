"""Role-safe training inputs, scalar calibration and fixed-budget selection; no framework."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.exp_delta03 import KEYS, temporal_roles
from sat_dengue.data.exp_delta03_retrospective import row_hash, values_hash
from sat_dengue.experiments.exp_beta01 import fit_intercept, shifted, thresholds
from sat_dengue.experiments.exp_delta03_contract import ROLES, digest


def probabilities(scores: Any, truth: Any | None = None) -> np.ndarray:
    p = np.asarray(scores, dtype=float)
    if p.ndim != 1 or not len(p) or not np.isfinite(p).all() or not ((p >= 0) & (p <= 1)).all():
        raise ValueError("Invalid probability support")
    if truth is not None:
        y = np.asarray(truth)
        if y.shape != p.shape or not np.isin(y, [0, 1]).all():
            raise ValueError("Invalid aligned binary truth")
    return p


def validate_parts(cell: dict[str, Any], parts: dict[str, Any], minimum_per_class: int) -> None:
    """Exact original temporal assignment; IDs/labels never join X or change by arm."""
    if set(parts) != set(ROLES):
        raise ValueError("Required temporal roles missing")
    seen: set[tuple[str, str]] = set()
    boundaries = {}
    for role in ROLES:
        rows, x = parts[role]["rows"], parts[role]["X"]
        if rows.empty or rows.duplicated(KEYS).any() or not rows.index.equals(x.index):
            raise ValueError("Empty, duplicate or misaligned role")
        keys = set(rows[KEYS].itertuples(index=False, name=None))
        if seen & keys:
            raise ValueError("Overlapping temporal roles")
        seen |= keys
        if not temporal_roles(rows, cell["year"], cell["horizon"]).eq(role).all():
            raise ValueError("Wrong temporal role or excluded2025")
        target = pd.PeriodIndex(rows.periodo_mes, freq="M") + cell["horizon"]
        if not np.array_equal(target.astype(str), rows.target_month.to_numpy()):
            raise ValueError("Target/origin/horizon mismatch")
        if rows.truth.isna().any() or not rows.truth.isin([0, 1]).all():
            raise ValueError("Missing/nonbinary role labels")
        expected = cell["roles"][role]
        if (
            row_hash(rows, KEYS) != expected["key_sha256"]
            or row_hash(rows, KEYS + ["truth"]) != expected["key_label_sha256"]
            or values_hash(x) != expected["X_sha256"]
        ):
            raise ValueError("Role key/label/value identity changed")
        if list(x) != cell["columns"]:
            raise ValueError("Role feature order changed")
        if role in ("train", "calibration"):
            if min(int(rows.truth.sum()), int((1 - rows.truth).sum())) < minimum_per_class:
                raise ValueError("Insufficient class support")
        if not rows.divipola_departamento.eq(rows.divipola_municipio.str[:2]).all():
            raise ValueError("Department/key identity mismatch")
        regional = rows.divipola_departamento.isin(["50", "73"])
        if cell["reference"] == "transfer" and role != "evaluation" and regional.any():
            raise ValueError("Transfer learned held-out target territories")
        if cell["reference"] != "transfer" and role != "train" and not regional.all():
            raise ValueError("Frozen regional learned/evaluation geography changed")
        boundaries[role] = (pd.PeriodIndex(rows.periodo_mes, freq="M").min(), target.max())
    for previous, following in zip(ROLES, ROLES[1:], strict=False):
        if boundaries[previous][1] > boundaries[following][0]:
            raise ValueError("A learned outcome is later than its consumer origin")


def calibrate(
    scores: Any,
    truth: Any,
    *,
    role: str,
    model_sha256: str,
    cohort_sha256: str,
    specification: dict[str, Any],
) -> dict[str, Any]:
    if role != "calibration":
        raise ValueError("Calibration role required")
    p = probabilities(scores, truth)
    y = np.asarray(truth, dtype=int)
    if specification["method"] != "regularized_intercept":
        raise ValueError("Unsupported calibrator")
    if min(int(y.sum()), int((1 - y).sum())) < specification["minimum_per_class"]:
        raise ValueError("Insufficient calibration class support")
    penalty = specification["penalty"]
    if not np.isfinite(penalty) or penalty <= 0:
        raise ValueError("Invalid regularization penalty")
    offset = fit_intercept(p, y, penalty)
    fitted = shifted(p, offset)
    if abs(float((fitted - y).sum()) + penalty * offset) > 1e-5:
        raise ValueError("Calibrator did not reach a supported optimum")
    return {
        "schema": "exp-delta03-calibrator-v1",
        "method": "regularized_intercept",
        "penalty": penalty,
        "offset": offset,
        "model_sha256": model_sha256,
        "cohort_sha256": cohort_sha256,
        "score_sha256": digest(p.tolist()),
        "rows": len(y),
        "positive": int(y.sum()),
        "negative": int((1 - y).sum()),
        "brier_before": float(np.mean((p - y) ** 2)),
        "brier_after": float(np.mean((fitted - y) ** 2)),
        "base_model_changed": False,
    }


def calibrated(scores: Any, calibrator: dict[str, Any], *, model_sha256: str) -> np.ndarray:
    if (
        calibrator["schema"] != "exp-delta03-calibrator-v1"
        or calibrator["model_sha256"] != model_sha256
    ):
        raise ValueError("Calibrator/model identity mismatch")
    return shifted(probabilities(scores), calibrator["offset"])


def select_policy(
    scores: Any,
    truth: Any,
    *,
    role: str,
    cohort_sha256: str,
    calibrator_sha256: str,
    specification: dict[str, Any],
) -> dict[str, Any]:
    if role != "selection":
        raise ValueError("Selection role required")
    p = probabilities(scores, truth)
    y = np.asarray(truth, dtype=int)
    b = specification["B"]
    if not np.isfinite(b) or b < 0:
        raise ValueError("Invalid fixed false-alert budget")
    base = {
        "schema": "exp-delta03-policy-v1",
        "cohort_sha256": cohort_sha256,
        "calibrator_sha256": calibrator_sha256,
        "budget": b,
        "unit": "false_onset_alerts_per_eligible_municipality_year",
        "selection_rows": len(y),
    }
    if not y.sum():
        return {**base, "status": "NO_EVALUABLE_NO_SELECTION_ONSETS", "threshold": None}
    policy = thresholds(y, p, len(y) / 12, b)
    return {
        **base,
        **policy,
        "status": "NO_ALERT" if policy["threshold"] is None else "SELECTED",
        "score_sha256": digest(p.tolist()),
    }


def apply_policy(scores: Any, policy: dict[str, Any], *, calibrator_sha256: str) -> np.ndarray:
    if policy["calibrator_sha256"] != calibrator_sha256:
        raise ValueError("Policy/calibrator identity mismatch")
    if policy["status"].startswith("NO_EVALUABLE"):
        raise ValueError("Policy is not evaluable")
    p = probabilities(scores)
    return np.zeros(len(p), dtype=bool) if policy["threshold"] is None else p >= policy["threshold"]
