"""Safe terminal EXP03 persistence and the separate consumed-year inference boundary.

Native model bytes and JSON state are used throughout. Loading never unpickles
objects or calls a fitting/calibration/threshold-selection interface.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> bytes:
    return canonical_bytes(value)


def _support(frame: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in frame:
        values = frame[name].dropna()
        if pd.api.types.is_numeric_dtype(frame[name]):
            result[name] = {
                "kind": "numeric",
                "min": float(values.min()),
                "max": float(values.max()),
            }
        else:
            result[name] = {"kind": "categorical", "seen": sorted(values.astype(str).unique())}
    return result


@dataclass
class NativePredictor:
    """Portable fitted family, original feature order and training support audit."""

    family: str
    model: Any
    columns: list[str]
    envelope_columns: list[str]
    support: dict[str, Any]

    def envelope(self, frame: pd.DataFrame) -> pd.DataFrame:
        if list(frame.columns) != self.columns:
            raise ValueError("Frozen predictor feature schema/order changed")
        clean = frame.copy()
        clean.attrs = {}
        renamed = clean.rename(columns={"municipality_code_feature": "municipality_code"})
        return renamed.reindex(columns=self.envelope_columns)

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        return self.model.predict(self.envelope(frame))

    def audit_support(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Report extrapolation; the unchanged preparer still governs prediction."""
        self.envelope(frame)
        frame = frame.copy()
        frame.attrs = {}
        audit = pd.DataFrame(index=frame.index)
        for name, rule in self.support.items():
            if rule["kind"] == "numeric":
                audit[name] = (frame[name] < rule["min"]) | (frame[name] > rule["max"])
            else:
                audit[name] = ~frame[name].astype(str).isin(rule["seen"])
        audit["unsupported"] = audit.any(axis=1)
        return audit


def fit_native(
    family: str, X: pd.DataFrame, y: pd.Series, parameters: dict[str, Any], seed: int
) -> NativePredictor:
    """Fit the fixed family on supplied training rows, including its train-only preparer.

    This function has no source reader and is not reachable from benchmark scoring.
    Its caller owns scientific authorization; generated-data tests may call it.
    """
    from sat_dengue.model_training.candidate_families import fit_model
    from sat_dengue.training_preparation.preprocessing import CATEGORICAL

    columns = list(X.columns)
    clean = X.copy()
    clean.attrs = {}
    envelope = clean.rename(columns={"municipality_code_feature": "municipality_code"})
    excluded = [name for name in CATEGORICAL if name not in envelope]
    for name in excluded:
        envelope[name] = pd.NA
    fitted = fit_model(family, envelope, y, parameters, seed=seed, threads=1, excluded=excluded)
    return NativePredictor(family, fitted, columns, list(envelope.columns), _support(clean))


@dataclass(frozen=True)
class SigmoidCalibrator:
    """Same single-score logistic transform as Stage 5, stored as two numbers."""

    coefficient: float
    intercept: float

    def __call__(self, scores: pd.Series) -> pd.Series:
        values = scores.to_numpy(dtype=float)
        if not np.isfinite(values).all() or not ((values >= 0) & (values <= 1)).all():
            raise ValueError("Sigmoid input must be finite probabilities")
        z = values * self.coefficient + self.intercept
        # Stable sigmoid, including very large finite logits.
        result = np.exp(-np.logaddexp(0.0, -z))
        return pd.Series(result, index=scores.index, dtype="Float64")


def fit_calibration(scores: pd.Series, truth: pd.Series, seed: int) -> SigmoidCalibrator:
    from sat_dengue.model_evaluation.calibration import _fit_sigmoid

    if (
        not scores.index.equals(truth.index)
        or truth.isna().any()
        or set(truth.unique()) != {0, 1}
        or not np.isfinite(scores.to_numpy(dtype=float)).all()
        or not scores.between(0, 1).all()
    ):
        raise ValueError("Sigmoid calibration requires aligned complete binary classes")
    fitted = _fit_sigmoid(scores, truth, seed)
    if fitted is None:
        raise ValueError("Sigmoid calibration unavailable; identity fallback forbidden")
    return SigmoidCalibrator(float(fitted.coef_[0, 0]), float(fitted.intercept_[0]))


@dataclass
class FrozenCell:
    """One immutable terminal fit with all interpretation and identity state."""

    cell_id: str
    metadata: dict[str, Any]
    predictor: NativePredictor
    calibrator: SigmoidCalibrator
    threshold: float | None
    budget: float
    profiles: dict[str, Any]
    provenance: dict[str, Any]

    def state(self) -> dict[str, Any]:
        if not math.isfinite(self.budget) or self.budget < 0:
            raise ValueError("Frozen cell requires explicit finite B_primary")
        if self.threshold is not None and not math.isfinite(self.threshold):
            raise ValueError("Use null for the no-alert threshold")
        return {
            "schema": "exp03-terminal-cell-v2",
            "cell_id": self.cell_id,
            "metadata": self.metadata,
            "family": self.predictor.family,
            "columns": self.predictor.columns,
            "envelope_columns": self.predictor.envelope_columns,
            "support": self.predictor.support,
            "preparer": self.predictor.model.preparer,
            "calibrator": {
                "coefficient": self.calibrator.coefficient,
                "intercept": self.calibrator.intercept,
            },
            "threshold": self.threshold,
            "B_primary": self.budget,
            "budget_units": "false_onset_alerts_per_monitored_municipality_year",
            "profiles": self.profiles,
            "provenance": self.provenance,
        }

    def identity(self) -> str:
        return _hash(_json(self.state()) + self.predictor.model.model_bytes())

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        raw = self.predictor.predict(frame)
        calibrated = self.calibrator(raw)
        return pd.DataFrame(
            {
                "raw_score": raw,
                "score": calibrated,
                "alert": False if self.threshold is None else calibrated >= self.threshold,
                "unsupported": self.predictor.audit_support(frame).unsupported,
            },
            index=frame.index,
        )


def _safe_directory(path: Path, *, create: bool = False) -> Path:
    """Native private artifacts stay beneath repository tmp, never a symlink."""
    path = Path(path)
    root = Path.cwd().resolve() / "tmp"
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError("EXP03 frozen artifacts require a repository-local tmp directory")
    if create:
        resolved.mkdir(parents=True, exist_ok=False)
    return resolved


def save_cell(cell: FrozenCell, path: Path) -> str:
    directory = _safe_directory(path, create=True)
    model = cell.predictor.model.model_bytes()
    state = _json(cell.state())
    (directory / "model.native").write_bytes(model)
    (directory / "state.json").write_bytes(state)
    manifest = {"model.native": _hash(model), "state.json": _hash(state)}
    (directory / "checksums.json").write_bytes(_json(manifest))
    return cell.identity()


def load_cell(path: Path) -> FrozenCell:
    from sat_dengue.model_training.candidate_families import restore_model

    directory = _safe_directory(path)
    if {p.name for p in directory.iterdir()} != {"model.native", "state.json", "checksums.json"}:
        raise ValueError("Frozen cell file membership changed")
    if any(p.is_symlink() for p in directory.iterdir()):
        raise ValueError("Symlink in frozen artifact")
    hashes = json.loads((directory / "checksums.json").read_bytes())
    if set(hashes) != {"model.native", "state.json"}:
        raise ValueError("Frozen cell checksum membership changed")
    for name, expected in hashes.items():
        if _hash((directory / name).read_bytes()) != expected:
            raise ValueError("Frozen cell bytes changed: " + name)
    state = json.loads((directory / "state.json").read_bytes())
    if state["schema"] != "exp03-terminal-cell-v2":
        raise ValueError("Legacy terminal artifact rejected")
    model = restore_model(
        state["family"], (directory / "model.native").read_bytes(), state["preparer"]
    )
    predictor = NativePredictor(
        state["family"], model, state["columns"], state["envelope_columns"], state["support"]
    )
    return FrozenCell(
        state["cell_id"],
        state["metadata"],
        predictor,
        SigmoidCalibrator(**state["calibrator"]),
        state["threshold"],
        state["B_primary"],
        state["profiles"],
        state["provenance"],
    )


def verify_reload(
    cell: FrozenCell, frame: pd.DataFrame, path: Path, *, atol: float = 1e-12
) -> dict[str, Any]:
    """Compare saved/reloaded predictions on pre-evaluation selection predictors.

    No labels or fitting interfaces enter this check. The absolute tolerance is
    declared before prediction and shared across raw and calibrated probabilities.
    """
    if frame.empty or atol != 1e-12:
        raise ValueError("Reload verification requires selection rows and tolerance 1e-12")
    restored = load_cell(path)
    if restored.identity() != cell.identity():
        raise ValueError("Reload identity differs")
    before = cell.predict(frame)
    after = restored.predict(frame)
    maximum = 0.0
    for name in ("raw_score", "score"):
        a = before[name].to_numpy(dtype=float)
        b = after[name].to_numpy(dtype=float)
        if (
            not np.isfinite(a).all()
            or not np.isfinite(b).all()
            or not np.allclose(a, b, atol=atol, rtol=0)
        ):
            raise ValueError("Reload prediction differs: " + name)
        maximum = max(maximum, float(np.max(np.abs(a - b))))
    for name in ("alert", "unsupported"):
        if not before[name].equals(after[name]):
            raise ValueError("Reload action/support differs: " + name)
    return {
        "status": "pass",
        "rows": len(frame),
        "absolute_tolerance": atol,
        "relative_tolerance": 0,
        "maximum_probability_difference": maximum,
        "role": "selection",
        "cell_id": cell.cell_id,
    }


def freeze_terminal(
    cells: list[FrozenCell],
    root: Path,
    expected_ids: list[str],
    provenance: dict[str, Any],
    *,
    validation_frames: dict[str, pd.DataFrame] | None = None,
) -> dict[str, Any]:
    """Freeze the complete declared grid before either stress or benchmark scoring."""
    if len(expected_ids) != len(set(expected_ids)) or not expected_ids:
        raise ValueError("Expected terminal cell identities must be unique")
    if len(cells) != len(expected_ids) or {c.cell_id for c in cells} != set(expected_ids):
        raise ValueError("Incomplete or duplicate terminal grid; no shortlist benchmark")
    if validation_frames is not None and set(validation_frames) != set(expected_ids):
        raise ValueError("Reload verification requires every terminal selection frame")
    if any(c.metadata.get("window") != "stress_2024" for c in cells):
        raise ValueError(
            "Terminal fits must use the stress_2024 training/calibration/selection roles"
        )
    directory = _safe_directory(root, create=True)
    identities = {}
    reload_checks = []
    for i, cell in enumerate(sorted(cells, key=lambda c: c.cell_id)):
        name = f"cell_{i:03d}"
        identity = save_cell(cell, directory / name)
        if load_cell(directory / name).identity() != identity:
            raise ValueError("Terminal native reload identity differs before evaluation")
        if validation_frames is not None:
            reload_checks.append(
                verify_reload(cell, validation_frames[cell.cell_id], directory / name)
            )
        identities[cell.cell_id] = {
            "directory": name,
            "identity": identity,
        }
    manifest = {
        "schema": "exp03-terminal-freeze-v2",
        "frozen_at": datetime.now(UTC).isoformat(),
        "provenance": provenance,
        "cells": identities,
        "terminal_cell_count": len(cells),
        "evaluation_outputs_opened": False,
        "reload_verification": reload_checks,
    }
    (directory / "terminal_manifest.json").write_bytes(_json(manifest))
    return {**manifest, "manifest_sha256": _hash(_json(manifest))}


def _load_terminal(root: Path) -> tuple[dict[str, Any], dict[str, FrozenCell], str]:
    directory = _safe_directory(root)
    raw = (directory / "terminal_manifest.json").read_bytes()
    manifest = json.loads(raw)
    if manifest.get("schema") != "exp03-terminal-freeze-v2":
        raise ValueError("Legacy terminal freeze rejected")
    cells = {}
    for cell_id, record in manifest["cells"].items():
        name = record["directory"]
        if not isinstance(name, str) or Path(name).name != name:
            raise ValueError("Invalid frozen cell directory")
        cell = load_cell(directory / name)
        if cell.cell_id != cell_id or cell.identity() != record["identity"]:
            raise ValueError("Frozen terminal identity changed")
        cells[cell_id] = cell
    if len(cells) != manifest["terminal_cell_count"]:
        raise ValueError("Terminal count mismatch")
    return manifest, cells, _hash(raw)


def _profile_mapping(profiles: dict[str, Any]) -> dict[str, str]:
    if "membership" not in profiles:
        if any(not isinstance(value, str) for value in profiles.values()):
            raise ValueError("Flat frozen profiles must map municipality to profile strings")
        return dict(profiles)
    membership = profiles["membership"]
    if not isinstance(membership, list):
        raise ValueError("Structured frozen profile membership must be a row list")
    result = {}
    for row in membership:
        municipality, profile = row.get("municipality_code"), row.get("transmission_profile")
        if not isinstance(municipality, str) or not isinstance(profile, str):
            raise ValueError("Invalid frozen profile membership row")
        if municipality in result:
            raise ValueError("Duplicate frozen municipality profile membership")
        result[municipality] = profile
    return result


def consumed_2025_benchmark(
    root: Path,
    frames_by_cell: dict[str, pd.DataFrame],
    coverage_metadata: dict[str, Any],
    *,
    expected_manifest_sha256: str,
) -> dict[str, Any]:
    """Score already-prepared, governed 2024/2025 rows with immutable terminal cells.

    The caller must verify data provenance and prepare each row as of its origin.
    Every row requires `latest_source_month` and the primary `eligible_at_t` gate;
    this boundary checks calendar admission again. Missing coverage/maturity evidence
    makes the benchmark explicitly not_evaluable, without predicting anything.
    """
    manifest, cells, before = _load_terminal(root)
    if before != expected_manifest_sha256:
        raise ValueError("Terminal freeze manifest changed")
    counters = dict(
        model_fits=0, preparer_fits=0, calibrator_fits=0, searches=0, threshold_selections=0
    )
    result: dict[str, Any] = {
        "schema": "exp03-consumed-benchmark-v2",
        "evidence_type": "consumed_retrospective_benchmark",
        "execution_counters": counters,
        "manifest_sha256": before,
        "status": "not_evaluable",
        "reason": None,
        "annual": [],
        "predictions": {},
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    if not all(
        coverage_metadata.get(k)
        for k in ("governed_coverage", "maturity_verified", "provenance_sha256")
    ):
        result["reason"] = "governed_coverage_or_maturity_unverified"
        return result
    if set(frames_by_cell) != set(cells):
        raise ValueError("Benchmark must include every frozen terminal cell")
    for cell_id, cell in cells.items():
        frame = frames_by_cell[cell_id]
        required = {
            "municipality_code",
            "year_month",
            "target_month",
            "eligible_at_t",
            "latest_source_month",
            *cell.predictor.columns,
        }
        if not required <= set(frame):
            raise ValueError("Benchmark missing keys, eligibility or as-of evidence")
        if frame.duplicated(["municipality_code", "target_month"]).any():
            raise ValueError("Duplicate benchmark action")
        horizon = cell.metadata["horizon"]
        origin = pd.PeriodIndex(frame.year_month, freq="M")
        target = pd.PeriodIndex(frame.target_month, freq="M")
        if horizon not in (1, 2) or not (target == origin + horizon).all():
            raise ValueError("Benchmark target/origin/horizon mismatch")
        if not frame.target_month.str[:4].isin(["2024", "2025"]).all():
            raise ValueError("Benchmark admits only separate 2024/2025 targets")
        if (
            frame.latest_source_month.isna().any()
            or not (pd.PeriodIndex(frame.latest_source_month, freq="M") <= origin).all()
        ):
            raise ValueError("Future or unknown predictor source in benchmark")
        if not (origin >= pd.Period("2023-12", freq="M")).all():
            raise ValueError("Benchmark violates terminal selection-origin embargo")
        # Eligibility remains the original Y(T)=0 gate. Unknown is abstention.
        eligible = frame.eligible_at_t.eq(True).fillna(False)
        available = frame[cell.predictor.columns].notna().all(axis=1)
        scoreable = frame.loc[eligible & available]
        prediction = frame[["municipality_code", "year_month", "target_month"]].copy()
        prediction["cell_id"] = cell_id
        prediction["alert"] = False
        prediction["raw_score"] = np.nan
        prediction["score"] = np.nan
        prediction["unsupported"] = False
        prediction["abstention"] = ~(eligible & available)
        if not scoreable.empty:
            scored = cell.predict(scoreable[cell.predictor.columns])
            for column in scored:
                prediction.loc[scoreable.index, column] = scored[column]
        prediction["profile"] = frame.municipality_code.map(_profile_mapping(cell.profiles))
        result["predictions"][cell_id] = prediction
        months = {}
        for year in ("2024", "2025"):
            mask = frame.target_month.str.startswith(year)
            actual = sorted(frame.loc[mask, "target_month"].unique())
            months[year] = {m[-2:] for m in actual}
            result["annual"].append(
                {
                    "cell_id": cell_id,
                    "year": int(year),
                    "target_months": actual,
                    "rows": int(mask.sum()),
                    "scored_rows": int((mask & eligible & available).sum()),
                    "abstentions": int((mask & ~(eligible & available)).sum()),
                    "alerts": int(prediction.loc[mask, "alert"].sum()),
                    "full_year_coverage": len(actual) == 12,
                    "artifact_identity": manifest["cells"][cell_id]["identity"],
                    "evidence_type": "retrospective_stress"
                    if year == "2024"
                    else "consumed_retrospective_benchmark",
                    **counters,
                }
            )
        common = sorted(months["2024"] & months["2025"])
        for row in result["annual"][-2:]:
            row["common_calendar_months"] = common
    _, after_cells, after = _load_terminal(root)
    if before != after or any(c.identity() != after_cells[k].identity() for k, c in cells.items()):
        raise ValueError("Terminal artifacts changed during benchmark")
    result.update(status="evaluable", reason=None, identities_verified_before_after=True)
    return result
