"""Fail-closed admission of rows to learned scientific roles."""

import pandas as pd  # type: ignore[import-untyped]

from .contract import PreparationError

LEARNED_ROLES = (
    "training",
    "preparer_fit",
    "learned_imputation",
    "learned_scaling",
    "feature_selection",
    "hyperparameter_selection",
    "calibration",
    "threshold_selection",
    "champion_selection",
)


def require_learnable(frame: pd.DataFrame, horizon: int, role: str) -> None:
    """Refuse 2025 origins/targets regardless of labels, policy overrides or metadata.

    Legacy V2 controls have no V4 metadata; their exact origin/target calendar is
    still mandatory. Metadata, when present, can only tighten admission.
    """
    target_name = f"target_period_t{horizon}"
    if (
        role not in LEARNED_ROLES
        or horizon not in (1, 2)
        or not {"year_month", target_name} <= set(frame)
    ):
        raise PreparationError("Learned role requires known role, origin, target and horizon")
    origin, target = frame.year_month, frame[target_name]
    if (
        origin.isna().any()
        or target.isna().any()
        or not origin.str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all()
        or not target.str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all()
    ):
        raise PreparationError("Unknown learned-role chronology")
    expected = (pd.PeriodIndex(origin, freq="M") + horizon).astype(str)
    if (origin >= "2025-01").any() or (target >= "2025-01").any() or not target.eq(expected).all():
        raise PreparationError("Consumed 2025 evidence cannot enter any learned role")
    for name, allowed in (
        ("origin_scientific_role", "historical_development_evidence"),
        (f"scientific_role_t{horizon}", "historical_development_evidence"),
        (f"maturity_t{horizon}", "mature"),
    ):
        if name in frame and not frame[name].eq(allowed).fillna(False).all():
            raise PreparationError("Unknown or consumed learned-role metadata")
