"""Protected, inspectable EXP03 scientific delivery; no tracking side effects.

CSV is the native equivalent of the protocol's parquet tables. Undefined values
remain null in JSON and empty in CSV; an explicit non-evaluable row is required
instead of silently omitting a prescribed comparison. SVG figures have adjacent
source tables and require no plotting dependency in the base installation.
"""

from __future__ import annotations

import csv
import html
import io
import json
import math
import re
from pathlib import Path
from typing import Any

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp01 import digest
from sat_dengue.training_preparation.serialization import bytes_record

SCHEMA = "exp03-scientific-bundle-v2"
TABLES = {
    "oof_predictions": ("oof_predictions", "oof_audit"),
    "selection_predictions": ("selection_predictions",),
    "primary_contrasts": ("primary_contrasts",),
    "secondary_contrasts": ("secondary_contrasts",),
    "performance_by_group": ("performance_by_group", "groups"),
    "coverage_and_exclusions": ("coverage_and_exclusions", "coverage", "operational_coverage"),
    "exposure_by_cluster": ("exposure_by_cluster", "exposures"),
    "error_types_and_delay": ("error_types_and_delay", "diagnostics"),
    "transport_2024_2025": ("transport_2024_2025", "transport"),
}
PREDICTION_KEYS = (
    "municipality_code",
    "target_month",
    "horizon",
    "window",
    "objective",
    "variant",
    "family",
)
COUNTERS = (
    "real_model_fits",
    "real_preparer_refits",
    "calibrator_fits",
    "synthetic_interface_fits",
    "model_fits",
    "preparer_fits",
    "searches",
    "threshold_selections",
)
SAFE_CELL = {
    "cell_id",
    "variant",
    "family",
    "horizon",
    "window",
    "objective",
    "status",
    "reason",
    "number_of_variables",
    "average_precision",
    "brier",
    "auroc",
    "onset_sensitivity",
    "false_alerts",
    "monitored_exposure",
    "false_alerts_per_monitored_municipality_year",
}
SAFE_CONTRAST = {
    "contrast_id",
    "id",
    "family",
    "horizon",
    "window",
    "left_variant",
    "right_variant",
    "left",
    "right",
    "objective",
    "status",
    "reason",
    "evidence_type",
    "evidence_level",
    "sensitivity_difference",
    "false_alert_rate_difference",
    "paired_sensitivity_difference",
    "paired_burden_difference",
    "benefit",
    "burden",
    "department_guardrail",
    "profile_guardrail",
    "support",
    "recommendation",
}
PROVENANCE_KEYS = (
    "scope_sha256",
    "protocol_sha256",
    "matrix_sha256",
    "git_revision",
    "data_sha256",
    "environment_sha256",
    "configuration_sha256",
    "freeze_timestamp",
)


def _protected(root: Path) -> Path:
    """Reject symlinks and paths outside the repository-local ignored tmp tree."""
    repository = Path.cwd().resolve()
    if ".." in root.parts:
        raise ValueError("Traversal in EXP03 native bundle path")
    absolute = root.absolute()
    allowed = (repository / "tmp").resolve()
    if not absolute.resolve().is_relative_to(allowed):
        raise ValueError("EXP03 native bundle must remain in protected repository tmp")
    if any(p.is_symlink() for p in [absolute, *absolute.parents] if p != p.parent):
        raise ValueError("Symlink in EXP03 native bundle path")
    if absolute.exists() and any(p.is_symlink() for p in absolute.rglob("*")):
        raise ValueError("Symlink descendant in EXP03 native bundle")
    return absolute


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "item"):
        return _jsonable(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _rows(result: dict[str, Any], name: str) -> list[dict[str, Any]]:
    for alias in TABLES[name]:
        if alias in result:
            value = result[alias]
            if hasattr(value, "to_dict"):
                value = value.to_dict(orient="records")
            if not isinstance(value, list) or any(not isinstance(r, dict) for r in value):
                raise ValueError(f"Invalid native table {name}")
            return _jsonable(value)
    if name in {"primary_contrasts", "secondary_contrasts"}:
        primary = name == "primary_contrasts"
        return [
            r
            for r in result.get("contrasts", [])
            if str(r.get("contrast_id", r.get("id", ""))).startswith("P") == primary
        ]
    return []


def _csv(rows: list[dict[str, Any]]) -> bytes:
    if not rows:
        raise ValueError("Empty templates do not constitute EXP03 deliverables")
    columns = sorted(set().union(*(r.keys() for r in rows)))
    if not columns:
        raise ValueError("Empty row in scientific table")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                k: json.dumps(v, sort_keys=True, allow_nan=False)
                if isinstance(v, (dict, list))
                else v
                for k, v in row.items()
            }
        )
    return stream.getvalue().encode()


def _feature_provenance(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate optional native-only, per-origin source-date evidence."""
    rows = _jsonable(result.get("feature_provenance", []))
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Invalid feature provenance table")
    keys = ("municipality_code", "year_month", "target_month", "horizon", "window", "role")
    seen = set()
    for row in rows:
        if not set(keys) <= row.keys():
            raise ValueError("Feature provenance lacks origin/role identity")
        identity = tuple(row[key] for key in keys)
        if identity in seen:
            raise ValueError("Duplicate feature provenance origin/role")
        seen.add(identity)
        latest, events = row.get("source_months"), row.get("source_event_months")
        if (
            not isinstance(latest, dict)
            or not isinstance(events, dict)
            or set(latest) != set(events)
        ):
            raise ValueError("Feature provenance source recipes disagree")
        origin = str(row["year_month"])
        for feature, dates in events.items():
            if not isinstance(dates, list):
                raise ValueError("Feature provenance requires all source event months")
            for value in dates:
                if not isinstance(value, str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
                    raise ValueError("Invalid source event month")
                if value > origin:
                    raise ValueError("Future source event in per-origin feature provenance")
            if latest[feature] != (max(dates) if dates else None):
                raise ValueError("Latest source month disagrees with actual event months")
    return rows


def _prediction_validation(rows: list[dict[str, Any]], role: str) -> None:
    seen: set[tuple[Any, ...]] = set()
    for row in rows:
        if row.get("status") in {"not_evaluable", "non_evaluable"}:
            if not row.get("reason"):
                raise ValueError(f"Unexplained non-evaluable {role} row")
            continue
        required = set(PREDICTION_KEYS) | {"onset_target", "excess_target", "raw_score", "score"}
        if role == "evaluation":
            required |= {"alert", "threshold"}
        if not required <= row.keys() or not ("origin" in row or "year_month" in row):
            raise ValueError(f"Incomplete {role} prediction audit")
        key = tuple(row[k] for k in PREDICTION_KEYS)
        if key in seen:
            raise ValueError(f"Duplicate native {role} prediction key")
        seen.add(key)
        if row["objective"] == "excess" and row["horizon"] != 2:
            raise ValueError("Duplicate T+1 excess objective")
        for field in ("raw_score", "score"):
            value = row[field]
            if value is not None and not 0 <= float(value) <= 1:
                raise ValueError("Probability outside [0,1]")


def _validate_tables(tables: dict[str, list[dict[str, Any]]], design: dict[str, Any]) -> None:
    for name, rows in tables.items():
        if not rows or any(not row for row in rows):
            raise ValueError(f"Missing substantive scientific deliverable: {name}")
    _prediction_validation(tables["oof_predictions"], "evaluation")
    _prediction_validation(tables["selection_predictions"], "selection")
    expected = {str(c["id"]) for c in design.get("contrasts", [])}
    expected.update("O" + str(i) for i, _ in enumerate(design.get("excess_controls", []), 1))
    actual = {
        str(r.get("contrast_id", r.get("id", "")))
        for name in ("primary_contrasts", "secondary_contrasts")
        for r in tables[name]
    }
    if not expected <= actual:
        raise ValueError("Missing prescribed contrasts in scientific delivery")
    for row in tables["transport_2024_2025"]:
        _validate_transport(row)


def _validate_transport(row: dict[str, Any]) -> None:
    """Fail closed on canonical period, evidence class and inference-only counters.

    Legacy year-only rows are deliberately unsupported. A redundant year alias
    may accompany target_year only when its explicitly normalized identity agrees.
    JSON integers and their exact string forms are accepted; booleans, floating
    years and coercible/partial spellings are not temporal identities.
    """

    def period(value: Any) -> str:
        if (type(value) is int and value in (2024, 2025)) or (
            type(value) is str and value in ("2024", "2025", "2024-2025")
        ):
            return str(value)
        raise ValueError("Invalid or missing transport temporal identity: target_year required")

    target_year = period(row.get("target_year"))
    if "year" in row and period(row["year"]) != target_year:
        raise ValueError("Conflicting transport target_year and year identities")
    if "target_months" in row:
        months = row["target_months"]
        allowed_years = {"2024", "2025"} if target_year == "2024-2025" else {target_year}
        if not isinstance(months, list) or any(
            not isinstance(month, str)
            or re.fullmatch(r"(?:2024|2025)-(?:0[1-9]|1[0-2])", month) is None
            or month[:4] not in allowed_years
            for month in months
        ):
            raise ValueError("Transport target_months contradicts temporal identity")
    pooled = target_year == "2024-2025"
    view = row.get("view", "annual")
    if (pooled and view != "count_pooled_descriptive") or (
        not pooled and view not in ("annual", "common_calendar_months")
    ):
        raise ValueError("Transport view contradicts target_year identity")
    evidence = {
        "2024": "retrospective_stress",
        "2025": "consumed_retrospective_benchmark",
        "2024-2025": "descriptive_consumed_2024_2025_context",
    }[target_year]
    if row.get("evidence_type") != evidence or (
        "evidence_level" in row and row["evidence_level"] != evidence
    ):
        raise ValueError(f"{target_year} transport must be labelled {evidence}")
    for key in (
        "model_fits",
        "preparer_fits",
        "calibrator_fits",
        "searches",
        "threshold_selections",
    ):
        if type(row.get(key)) is not int or row[key] != 0:
            raise ValueError(
                f"Benchmark must record explicit integer zero execution counters: {key}"
            )


def _validate_thresholds(rows: list[dict[str, Any]], thresholds: list[dict[str, Any]]) -> None:
    """Reconstruct the optimal whole-tie policy directly from protected rows."""
    from sat_dengue.experiments.exp03_evaluation import select_threshold

    keys = ("variant", "family", "horizon", "window", "objective")
    seen = set()
    for record in thresholds:
        if any(key not in record for key in keys):
            raise ValueError("Threshold evidence lacks cell identity")
        identity = tuple(record[key] for key in keys)
        if identity in seen:
            raise ValueError("Duplicate threshold evidence cell")
        seen.add(identity)
        selected = [r for r in rows if tuple(r.get(key) for key in keys) == identity]
        if not selected:
            raise ValueError("Threshold evidence has no native selection rows")
        expected = select_threshold(
            [r["onset_target"] for r in selected],
            [r["score"] for r in selected],
            record.get("B_primary"),
            record.get("monitored_exposure", 0),
        )
        for field in (
            "threshold",
            "selection_false_alert_cap",
            "detected_onsets",
            "false_alerts",
            "emitted_alerts",
            "underspend",
            "threshold_tie_size",
            "whole_score_ties",
        ):
            if record.get(field) != expected[field]:
                raise ValueError(f"Native selection rows do not reconstruct threshold {field}")
    predicted = {
        tuple(row.get(key) for key in keys)
        for row in rows
        if row.get("status") not in {"not_evaluable", "non_evaluable"}
    }
    if seen != predicted:
        raise ValueError("Native selection rows lack threshold evidence")


def _validate_metrics(result: dict[str, Any], tables: dict[str, list[dict[str, Any]]]) -> None:
    """Independent reconstruction of headline cell and paired contrast metrics."""
    import pandas as pd  # type: ignore[import-untyped]

    from sat_dengue.experiments.exp03_evaluation import metrics

    predictions, exposures = tables["oof_predictions"], tables["exposure_by_cluster"]
    fields = (
        "real_onsets",
        "detected_onsets",
        "missed_onsets",
        "emitted_alerts",
        "false_alerts",
        "onset_sensitivity",
        "onset_precision",
        "false_alarm_ratio",
        "false_positive_rate",
        "false_alerts_per_monitored_municipality_year",
        "false_alerts_per_eligible_municipality_year",
        "brier",
        "average_precision",
        "covered_onsets",
        "eligible_onsets",
        "common_onsets",
        "eligible_onsets_excluded_from_common",
        "coverage_adjusted_sensitivity",
    )

    def reconstruct(identity: dict[str, Any], cuts: list[str]) -> dict[str, Any]:
        rows = [
            r
            for r in predictions
            if r.get("window") in cuts
            and all(
                r.get(k) == identity.get(k) for k in ("variant", "objective", "family", "horizon")
            )
        ]
        ledger = [
            e
            for e in exposures
            if e.get("window") in cuts
            and e.get("role", "evaluation") == "evaluation"
            and e.get("horizon") == identity.get("horizon")
        ]
        frame = pd.DataFrame(rows)
        if frame.empty:
            raise ValueError("Reported metric has no native prediction rows")
        if ledger and all("known_eligible_onsets" in e for e in ledger):
            frame.attrs["eligible_onsets"] = sum(e["known_eligible_onsets"] for e in ledger)
            frame.attrs["coverage_denominator_source"] = "pre_gate_exposure_ledger"
        if ledger and all("known_covered_onsets" in e for e in ledger):
            frame.attrs["covered_onsets"] = sum(e["known_covered_onsets"] for e in ledger)
        return metrics(
            frame,
            frame.alert,
            sum(e["monitored_exposure"] for e in ledger),
            sum(e["eligible_exposure"] for e in ledger),
            frame.score,
            identity["objective"],
        )

    def compare(expected: dict[str, Any], actual: dict[str, Any]) -> None:
        for field in fields:
            a, b = expected.get(field), actual.get(field)
            if a is None and b is None:
                continue
            if a is None or b is None or not math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-10):
                raise ValueError(f"Native predictions do not reconstruct metric {field}")

    for child in result.get("children", []):
        micro = child.get("summaries", {}).get("micro")
        if micro is not None:
            compare(micro, reconstruct(child, [child["window"]]))
    for row in result.get("contrasts", []):
        if row.get("status") != "evaluable" or "left_metrics" not in row:
            continue
        actual = []
        for side in ("left", "right"):
            identity = {
                "variant": row[side + "_variant"],
                "objective": row[side + "_objective"],
                "family": row["family"],
                "horizon": row["horizon"],
            }
            actual.append(reconstruct(identity, row["source_cuts"]))
            compare(row[side + "_metrics"], actual[-1])
        for name, field in (
            ("paired_sensitivity_difference", "onset_sensitivity"),
            ("paired_burden_difference", "false_alerts_per_monitored_municipality_year"),
        ):
            a, b = actual[0][field], actual[1][field]
            expected = None if a is None or b is None else a - b
            value = row.get(name)
            if expected is None and value is None:
                continue
            if (
                expected is None
                or value is None
                or not math.isclose(expected, value, rel_tol=1e-8, abs_tol=1e-10)
            ):
                raise ValueError(f"Native predictions do not reconstruct contrast {name}")


def _number(row: dict[str, Any], *names: str) -> float | None:
    for name in names:
        value = row.get(name)
        if isinstance(value, dict):
            value = value.get("estimate", value.get("value"))
        if isinstance(value, (int, float)) and math.isfinite(value):
            return float(value)
    return None


def _interval(row: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    for name in names:
        if isinstance(row.get(name), dict):
            return row[name]
    key = (
        "sensitivity_difference"
        if any("sensitivity" in n for n in names)
        else "false_alert_rate_difference"
    )
    value = row.get("paired_interval", {}).get(key, {})
    return value if isinstance(value, dict) else {}


def _reliability(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[tuple[float, int]]] = {}
    for row in rows:
        if row.get("status") in {"not_evaluable", "non_evaluable"}:
            continue
        truth = row.get("excess_target" if row.get("objective") == "excess" else "onset_target")
        if truth not in (0, 1):
            continue
        for stage, column in (("raw", "raw_score"), ("calibrated", "score")):
            score = row.get(column)
            if score is None:
                continue
            bucket = min(9, int(float(score) * 10))
            key = tuple(
                row.get(k) for k in ("variant", "family", "horizon", "window", "objective")
            ) + (stage, bucket)
            grouped.setdefault(key, []).append((float(score), int(truth)))
    output = []
    for key, values in grouped.items():
        row = dict(
            zip(
                ("variant", "family", "horizon", "window", "objective", "stage", "bin"),
                key,
                strict=True,
            )
        )
        row.update(
            count=len(values),
            mean_probability=sum(v[0] for v in values) / len(values),
            observed_fraction=sum(v[1] for v in values) / len(values),
        )
        output.append(row)
    return output or [{"status": "not_evaluable", "reason": "no_known_labels_and_scores"}]


def _joint_effects(
    predictions: list[dict[str, Any]], exposures: list[dict[str, Any]], design: dict[str, Any]
) -> list[dict[str, Any]]:
    """Reconstruct year-by-territory/profile paired effects with pre-gate D."""
    cells: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in predictions:
        if row.get("status") in {"not_evaluable", "non_evaluable"}:
            continue
        cell = tuple(row.get(k) for k in ("variant", "objective", "family", "horizon", "window"))
        cells.setdefault(cell, []).append(row)
    comparisons = [
        dict(c, left_objective="onset", right_objective="onset")
        for c in design.get("contrasts", [])
    ]
    comparisons += [
        {
            "id": "O" + str(i),
            "left": v,
            "right": v,
            "left_objective": "onset",
            "right_objective": "excess",
        }
        for i, v in enumerate(design.get("excess_controls", []), 1)
    ]
    output = []
    for comparison in comparisons:
        for cell, left in cells.items():
            variant, objective, family, horizon, window = cell
            if variant != comparison["left"] or objective != comparison["left_objective"]:
                continue
            right = cells.get(
                (comparison["right"], comparison["right_objective"], family, horizon, window)
            )
            if right is None:
                continue

            def key(r: dict[str, Any]) -> tuple[Any, Any]:
                return r["municipality_code"], r["target_month"]

            lookup = {key(r): r for r in right}
            if set(lookup) != {key(r) for r in left}:
                raise ValueError("Joint effects require identical paired prediction keys")
            groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
            for row in left:
                if row["onset_target"] != lookup[key(row)]["onset_target"]:
                    raise ValueError("Joint effects require paired onset labels")
                year = str(row["target_month"])[:4]
                profile = str(row.get("transmission_profile", row.get("profile", "unknown")))
                for dimension, group in (
                    ("department", str(row["municipality_code"])[:2]),
                    ("transmission_profile", profile),
                ):
                    groups.setdefault((year, dimension, group), []).append(row)
            for (year, dimension, group), rows in groups.items():
                paired = [lookup[key(r)] for r in rows]
                onsets = sum(int(r["onset_target"]) for r in rows)
                tp = [
                    sum(bool(r["alert"]) and r["onset_target"] == 1 for r in side)
                    for side in (rows, paired)
                ]
                fp = [
                    sum(bool(r["alert"]) and r["onset_target"] == 0 for r in side)
                    for side in (rows, paired)
                ]
                matching = []
                for exposure in exposures:
                    exposure_year = str(exposure.get("target_year", exposure.get("year", "")))
                    if exposure_year != year or exposure.get("window", window) != window:
                        continue
                    if exposure.get("horizon", horizon) != horizon:
                        continue
                    if exposure.get("role", "evaluation") != "evaluation":
                        continue
                    value = (
                        str(exposure.get("municipality_code", ""))[:2]
                        if dimension == "department"
                        else str(
                            exposure.get("transmission_profile", exposure.get("profile", "unknown"))
                        )
                    )
                    if value == group:
                        matching.append(exposure)
                denominator = sum(float(e.get("monitored_exposure", 0)) for e in matching)
                output.append(
                    {
                        "contrast_id": comparison["id"],
                        "family": family,
                        "horizon": horizon,
                        "window": window,
                        "year": year,
                        "dimension": dimension,
                        "group": group,
                        "onsets": onsets,
                        "municipalities": len({r["municipality_code"] for r in rows}),
                        "years_with_onsets": int(onsets > 0),
                        "monitored_exposure": denominator,
                        "left_detected_onsets": tp[0],
                        "right_detected_onsets": tp[1],
                        "left_false_alerts": fp[0],
                        "right_false_alerts": fp[1],
                        "sensitivity_difference": (tp[0] - tp[1]) / onsets if onsets else None,
                        "false_alert_rate_difference": (fp[0] - fp[1]) / denominator
                        if denominator
                        else None,
                        "support": "unknown_single_year",
                        "uncertainty_status": "unavailable_single_year",
                        "source_table": "oof_predictions.csv;exposure_by_cluster.csv",
                    }
                )
    return output or [{"status": "not_evaluable", "reason": "no_paired_cell_predictions"}]


def _matrix_svg(rows: list[dict[str, Any]], synthetic: bool) -> bytes:
    """Year-by-group effect matrix, showing onset support in each cell."""
    keys = ("contrast_id", "family", "horizon", "dimension", "group")
    years = sorted({str(r["year"]) for r in rows if "year" in r})
    groups = sorted({tuple(str(r[k]) for k in keys) for r in rows if "year" in r})
    lookup = {(tuple(str(r[k]) for k in keys), str(r["year"])): r for r in rows if "year" in r}
    height = 100 + max(1, len(groups)) * 30
    width = 620 + max(1, len(years)) * 170
    title = ("SYNTHETIC — " if synthetic else "") + "P1–P4 year × department/profile effects"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f"<title>{html.escape(title)}</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="sans-serif" font-size="11" fill="#172638">',
        f'<text x="15" y="22" font-size="16">{html.escape(title)}</text>',
        '<text x="15" y="41">Primary contrasts shown; all primary/secondary rows: '
        "group_effects.csv. Cells: Δsensitivity / Δburden; "
        "n=onsets; single-year support unknown.</text>",
    ]
    for j, year in enumerate(years):
        parts.append(f'<text x="{600 + j * 170}" y="65">{year}</text>')
    for i, group in enumerate(groups):
        y = 85 + 30 * i
        parts.append(f'<text x="15" y="{y}">{html.escape(" / ".join(group))}</text>')
        for j, year in enumerate(years):
            row = lookup.get((group, year), {})
            sensitivity, burden = (
                row.get("sensitivity_difference"),
                row.get("false_alert_rate_difference"),
            )
            color = (
                "#f0f0f0" if sensitivity is None else "#f7dfdf" if sensitivity < 0 else "#dceef2"
            )
            value = "N/A" if sensitivity is None else f"{sensitivity:.3g}"
            value += " / " + ("N/A" if burden is None else f"{burden:.3g}")
            value += f"; n={row.get('onsets', 'N/A')}"
            x = 590 + j * 170
            parts.append(f'<rect x="{x}" y="{y - 15}" width="166" height="25" fill="{color}"/>')
            parts.append(f'<text x="{x + 4}" y="{y}">{value}</text>')
    if not groups:
        parts.append('<text x="20" y="85">N/A: no paired cell predictions</text>')
    return ("\n".join(parts) + "</g></svg>\n").encode()


def _reliability_svg(rows: list[dict[str, Any]], synthetic: bool) -> bytes:
    title = ("SYNTHETIC — " if synthetic else "") + "Reliability by frozen cell and score stage"
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="740" height="730" role="img">',
        f"<title>{html.escape(title)}</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="sans-serif" font-size="12" fill="#172638">',
        f'<text x="30" y="28" font-size="17">{html.escape(title)}</text>',
        '<text x="30" y="48">Source: reliability_bins.csv; '
        "raw: orange, calibrated: blue; bin count retained in source.</text>",
        '<path d="M80 80V630H630" stroke="#172638" fill="none"/>',
        '<path d="M80 630L630 80" stroke="#8895a2" stroke-dasharray="4"/>',
        '<text x="285" y="680">Mean predicted probability</text>',
        '<text x="10" y="70">Observed fraction</text>',
    ]
    for value in (0, 0.25, 0.5, 0.75, 1):
        x, y = 80 + 550 * value, 630 - 550 * value
        parts.extend(
            [f'<text x="{x}" y="653">{value}</text>', f'<text x="44" y="{y}">{value}</text>']
        )
    for row in rows:
        if "mean_probability" not in row:
            continue
        x, y = 80 + 550 * row["mean_probability"], 630 - 550 * row["observed_fraction"]
        color = "#167d9a" if row["stage"] == "calibrated" else "#c5701d"
        label = html.escape(json.dumps(row, sort_keys=True))
        parts.append(
            f'<circle cx="{x:.3f}" cy="{y:.3f}" r="3" opacity="0.5" fill="{color}">'
            f"<title>{label}</title></circle>"
        )
    return ("\n".join(parts) + "</g></svg>\n").encode()


def _svg(title: str, rows: list[dict[str, Any]], names: tuple[str, ...], source: str) -> bytes:
    """Render paired effects or explicit N/A, retaining every supplied row."""
    width, height = 1000, 100 + max(1, len(rows)) * 28
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img">',
        f"<title>{html.escape(title)}</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="sans-serif" font-size="12" fill="#172638">',
        f'<text x="20" y="25" font-size="18">{html.escape(title)}</text>',
        f'<text x="20" y="47">Source: {html.escape(source)}; '
        "N/A preserves unavailable evidence.</text>",
        f'<line x1="650" y1="60" x2="650" y2="{height - 20}" stroke="#8895a2"/>',
    ]
    values = [_number(row, *names) for row in rows]
    bounds = [
        float(v)
        for row in rows
        for k, v in _interval(row, names).items()
        if k in {"lower", "upper"} and isinstance(v, (float, int))
    ]
    span = max([abs(v) for v in values + bounds if v is not None] + [0.001])
    for i, (row, value) in enumerate(zip(rows, values, strict=True)):
        y = 78 + i * 28
        label = " / ".join(
            str(row[k])
            for k in (
                "contrast_id",
                "family",
                "horizon",
                "window",
                "objective",
                "left_objective",
                "right_objective",
                "year",
                "department",
                "profile",
                "group",
                "variant",
                "support",
            )
            if k in row
        )
        label = label or str(row.get("status", i))
        parts.append(f'<text x="20" y="{y}">{html.escape(label[:95])}</text>')
        if value is None:
            parts.append(f'<text x="660" y="{y}">N/A</text>')
        else:
            x = 650 + 240 * value / span
            color = "#a63d40" if value < 0 else "#167d9a"
            parts.append(f'<circle cx="{x:.2f}" cy="{y - 4}" r="4" fill="{color}"/>')
            parts.append(f'<text x="910" y="{y}">{value:.4g}</text>')
            entry = _interval(row, names)
            if entry and entry.get("lower") is not None and entry.get("upper") is not None:
                lo, hi = (650 + 240 * float(entry[n]) / span for n in ("lower", "upper"))
                parts.append(
                    f'<line x1="{lo:.2f}" x2="{hi:.2f}" '
                    f'y1="{y - 4}" y2="{y - 4}" stroke="#167d9a"/>'
                )
    return ("\n".join(parts) + "</g></svg>\n").encode()


def _report(tables: dict[str, list[dict[str, Any]]], synthetic: bool) -> bytes:
    label = (
        "SYNTHETIC GENERATED-DATA EXAMPLE — NOT SCIENTIFIC FINDINGS"
        if synthetic
        else "RETROSPECTIVE EXP03 SCIENTIFIC REPORT"
    )
    lines = [
        f"# {label}",
        "",
        "G5: `NOT_APPROVED`. Champion: `not_selected`.",
        "",
        "## Development decision table",
        "",
        "| Comparison | Family/horizon | Detection Δ pp [95% CI] | "
        "Burden Δ FP/monitored municipality-year [95% CI] | "
        "Onsets / aggregate support | Dept / profile guardrail | Disposition | Evidence |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, row in enumerate(tables["primary_contrasts"], 2):
        if row.get("window") == "stress_2024":
            continue
        sensitivity = _number(
            row,
            "paired_sensitivity_difference",
            "sensitivity_difference",
            "paired_onset_sensitivity_difference",
        )
        burden = _number(
            row, "paired_burden_difference", "false_alert_rate_difference", "burden_difference"
        )
        recommendation = row.get("recommendation", row.get("decision", "inconclusive"))
        if isinstance(recommendation, dict):
            recommendation = recommendation.get("recommendation", "inconclusive")
        decision = row.get("decision", {})
        support = decision.get("support", "unknown")
        department = decision.get("department_guardrail", "unknown")
        profile = decision.get("profile_guardrail", "unknown")
        onsets = row.get("left_metrics", {}).get("real_onsets", "N/A")
        evidence = decision.get("evidence_level", row.get("evidence_type"))
        if evidence is None:
            evidence = (
                "retrospective_development"
                if row.get("window") in {"pooled_development", "development_oof"}
                else "unknown"
            )

        def display(
            value: float | None,
            interval_key: str,
            factor: float = 1,
            record: dict[str, Any] = row,
        ) -> str:
            point = "N/A" if value is None else f"{value * factor:.4g}"
            interval = record.get("paired_interval", {}).get(interval_key, {})
            lower, upper = interval.get("lower"), interval.get("upper")
            bounds = (
                "N/A"
                if lower is None or upper is None
                else f"{lower * factor:.3g}, {upper * factor:.3g}"
            )
            return f"{point} [{bounds}]"

        lines.append(
            f"| {row.get('contrast_id', row.get('id'))} "
            f"([native row {index}](primary_contrasts.csv)) | "
            f"{row.get('family', 'N/A')}/T+{row.get('horizon', 'N/A')} | "
            f"{display(sensitivity, 'sensitivity_difference', 100)} | "
            f"{display(burden, 'false_alert_rate_difference')} | "
            f"{onsets} / {support} | {department} / {profile} | "
            f"{recommendation} | {evidence} |"
        )
    lines += [
        "",
        "## Questions and inspectable evidence",
        "",
        "This table contains every available primary development comparison. "
        "[All stress comparisons remain separate in the complete primary "
        "source](primary_contrasts.csv). Detection differences and their intervals "
        "are expressed in percentage points (pp); "
        "burden is false alerts per monitored municipality-year. "
        "Unknown intervals/support remain unavailable; no automatic selection follows.",
        "What helped and at what false-alert cost: assess detection and burden "
        "jointly in [all primary comparisons](primary_contrasts.csv) and [all "
        "secondary comparisons](secondary_contrasts.csv). Null and adverse results "
        "remain included.",
        "",
        "For whom and with what temporal stability: [group "
        "results](performance_by_group.csv) retain support and undefined groups; "
        "year, department and historical profile are descriptive slices. Development "
        "cuts share municipalities and training history.",
        "The [paired year-by-department/profile matrix](group_effects.csv) "
        "reconstructs every contrast from native predictions and pre-gate exposure. "
        "The figure displays P1–P4; the linked source retains the "
        "secondary/objective-control appendix.",
        "",
        "What disappeared under delay: [error and stale-input "
        "diagnostics](error_types_and_delay.csv). Conditional feature stress assumes "
        "Y(T) independently known; strict unavailability prevents establishing "
        "eligibility and requires abstention.",
        "",
        "Transport: [2024 and consumed 2025](transport_2024_2025.csv) use frozen "
        "terminal artifacts. The combined 2024–2025 view is descriptive; neither year"
        " enters development intervals or candidate selection.",
        "",
        "## Figures",
        "",
        "[Coverage summary](coverage_summary.csv) aggregates each evaluation ledger once. "
        "[Annual transport summary](transport_summary.csv) includes every frozen cell; "
        "common-month and pooled descriptive views stay in the full transport source.",
        "![Paired sensitivity](primary_effects.svg)",
        "",
        "![Paired burden](primary_burden.svg)",
        "",
        "![Year/department/profile support](group_effects.svg)",
        "",
        "![Reliability](reliability.svg)",
        "",
        "![Coverage and abstentions](coverage.svg)",
        "",
        "![Transport](transport.svg)",
        "",
        "## Findings, interpretations and limitations",
        "",
        "Confirmed engineering evidence consists of generated-data checks and "
        "artifact reconstruction only."
        if synthetic
        else "Confirmed scientific findings must be read from the prespecified "
        "comparison rows and their uncertainty/support, without selecting a favorable budget.",
        "",
        "Interpretations describe conditional predictive contributions; no feature "
        "ablation establishes biological causality. Unknown guardrails remain "
        "unknown. A non-significant difference does not establish equivalence.",
        "",
        "Limitations: three development-year clusters, overlapping training "
        "histories, multiple pointwise comparisons, complete-case selection, unknown "
        "historical publication dates and pending practical-effect margins. Actual "
        "issuance lead is unavailable without publication evidence.",
        "",
        "Next hypotheses require a separately versioned experiment and new "
        "authorization. No synthetic fixture establishes operational capacity, a "
        "champion, G5 approval or scientific execution authority.",
        "",
    ]
    return "\n".join(lines).encode()


def aggregate_projection(result: dict[str, Any]) -> dict[str, Any]:
    """Closed aggregate projection: never recursively copy native or group data."""

    def scalars(row: dict[str, Any], allow: set[str]) -> dict[str, Any]:
        return {
            k: _jsonable(v)
            for k, v in row.items()
            if k in allow and (v is None or isinstance(v, (str, int, float, bool)))
        }

    counters = {k: result.get(k) for k in COUNTERS}
    if any(v is not None and (type(v) is not int or v < 0) for v in counters.values()):
        raise ValueError("Invalid execution counter; absent is distinct from zero")
    return {
        "schema": "exp03-aggregate-v2",
        "experiment_id": "EXP03",
        "synthetic": bool(result.get("synthetic")),
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "counters": counters,
        "cells": [scalars(r, SAFE_CELL) for r in result.get("children", [])],
        "contrasts": [scalars(r, SAFE_CONTRAST) for r in result.get("contrasts", [])],
    }


def write_bundle(
    root: Path | str, result: dict[str, Any], provenance: dict[str, Any], design: dict[str, Any]
) -> dict[str, Any]:
    """Write a complete staging bundle; publication/MLflow remain the caller's job."""
    folder = _protected(Path(root))
    if (folder / "manifest.json").exists():
        raise FileExistsError("EXP03 native bundle already exists")
    tables = {name: _rows(result, name) for name in TABLES}
    _validate_tables(tables, design)
    _validate_metrics(result, tables)
    thresholds = result.get("thresholds", result.get("threshold_selection"))
    if not thresholds:
        raise ValueError("Missing native threshold-selection evidence")
    _validate_thresholds(tables["selection_predictions"], thresholds)
    synthetic = result.get("synthetic")
    if type(synthetic) is not bool:
        raise ValueError("Scientific evidence class must be explicit")
    if not synthetic:
        from sat_dengue.experiments.exp03_admission import validate_admission

        validate_admission(provenance)
    if not synthetic and any(not provenance.get(k) for k in PROVENANCE_KEYS):
        raise ValueError("Scientific execution requires complete scope/runtime/freeze identities")
    if (
        result.get("G5", "NOT_APPROVED") != "NOT_APPROVED"
        or result.get("champion", "not_selected") != "not_selected"
    ):
        raise ValueError("EXP03 does not authorize champion/G5 decisions")
    folder.mkdir(parents=True, exist_ok=True)
    models = folder / "model_artifacts"
    models.mkdir(exist_ok=True)
    for name, value in result.get("model_artifacts", {}).items():
        path = models / name
        if path.is_absolute() and not path.resolve().is_relative_to(models.resolve()):
            raise ValueError("Unsafe model artifact path")
        if not isinstance(value, bytes):
            raise ValueError("Model payload must be native bytes")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != value:
            raise FileExistsError("Refusing to replace persisted model artifact")
        path.write_bytes(value)
    if not any(p.is_file() for p in models.rglob("*")):
        raise ValueError("Missing persisted terminal model artifacts")
    saved_result = {k: v for k, v in result.items() if k != "model_artifacts"}
    saved_result["native_model_artifacts"] = sorted(
        str(p.relative_to(folder)) for p in models.rglob("*") if p.is_file()
    )
    payloads = {name + ".csv": _csv(rows) for name, rows in tables.items()}
    feature_provenance = _feature_provenance(result)
    if feature_provenance:
        payloads["feature_provenance.csv"] = _csv(feature_provenance)
    payloads.update(
        {
            "result.json": canonical_bytes(_jsonable(saved_result)),
            "provenance.json": canonical_bytes(_jsonable(provenance)),
            "threshold_selection.json": canonical_bytes(_jsonable(thresholds)),
        }
    )
    inventory = {
        "schema": "exp03-variant-inventory-v2",
        "variants": design.get("variants", {}),
        "variant_groups": design.get("variant_groups", {}),
        "recipes": design.get("inventory", {}),
        "unique_set_sha256": {k: digest(sorted(v)) for k, v in design.get("variants", {}).items()},
        "cell_identities": [
            {
                k: c.get(k)
                for k in (
                    "cell_id",
                    "variant",
                    "family",
                    "horizon",
                    "window",
                    "objective",
                    "status",
                )
            }
            for c in result.get("children", [])
        ],
        "contrasts": design.get("contrasts", []),
        "excess_controls": design.get("excess_controls", []),
        "aliases": {},
        "fit_reuse": "Contrasts and diagnostics reference cells; zero additional fits",
    }
    payloads["variant_inventory.json"] = canonical_bytes(_jsonable(inventory))
    receipt = {
        "schema": "exp03-scope-execution-receipt-v2",
        "experiment_id": "EXP03",
        "synthetic": synthetic,
        "evidence_class": "synthetic_generated_data"
        if synthetic
        else "retrospective_scientific_execution",
        "identities": {k: provenance.get(k) for k in PROVENANCE_KEYS},
        "missing_identities": [k for k in PROVENANCE_KEYS if not provenance.get(k)],
        "B_primary": result.get("B_primary", design.get("B_primary", design.get("budget"))),
        "counts_by_phase": {
            **{k: result.get(k) for k in COUNTERS},
            "phases": result.get("execution_counters"),
        },
        "exclusions": tables["coverage_and_exclusions"],
        "deviations": result.get("deviations", []),
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    payloads["scope_execution_receipt.json"] = canonical_bytes(_jsonable(receipt))
    payloads["report.md"] = _report(tables, synthetic)
    plot_specs = {
        "primary_effects": (
            "Paired onset sensitivity with pointwise uncertainty",
            "primary_contrasts",
            (
                "paired_sensitivity_difference",
                "sensitivity_difference",
                "paired_onset_sensitivity_difference",
            ),
        ),
        "primary_burden": (
            "Paired realized false-alert burden",
            "primary_contrasts",
            ("paired_burden_difference", "false_alert_rate_difference", "burden_difference"),
        ),
    }
    for name, (title, table, names) in plot_specs.items():
        payloads[name + ".svg"] = _svg(
            ("SYNTHETIC — " if synthetic else "") + title, tables[table], names, table + ".csv"
        )
    reliability = _reliability(tables["oof_predictions"])
    payloads["reliability_bins.csv"] = _csv(reliability)
    payloads["reliability.svg"] = _reliability_svg(reliability, synthetic)
    joint = _joint_effects(tables["oof_predictions"], tables["exposure_by_cluster"], design)
    payloads["group_effects.csv"] = _csv(joint)
    primary_joint = [r for r in joint if r.get("contrast_id") in {"P1", "P2", "P3", "P4"}]
    payloads["group_effects.svg"] = _matrix_svg(primary_joint, synthetic)
    coverage_summary = _coverage_summary(tables["exposure_by_cluster"])
    payloads["coverage_summary.csv"] = _csv(coverage_summary)
    payloads["coverage.svg"] = _coverage_svg(coverage_summary, synthetic)
    transport_summary = _transport_summary(tables["transport_2024_2025"])
    payloads["transport_summary.csv"] = _csv(transport_summary)
    payloads["transport.svg"] = _transport_svg(transport_summary, synthetic)
    for name, value in payloads.items():
        target = folder / name
        if target.exists():
            raise FileExistsError(f"Refusing to replace native payload {name}")
        target.write_bytes(value)
    files = {
        str(p.relative_to(folder)): bytes_record(p.read_bytes())
        for p in folder.rglob("*")
        if p.is_file()
    }
    body = {"schema": SCHEMA, "files": files, "synthetic": synthetic}
    manifest = {**body, "bundle_id": digest(body)}
    (folder / "manifest.json").write_bytes(canonical_bytes(manifest))
    validate_bundle(folder)
    return manifest


def validate_bundle(root: Path | str) -> dict[str, Any]:
    """Verify the entire closed native manifest, tables and no symlink escapes."""
    folder = _protected(Path(root))
    manifest = json.loads((folder / "manifest.json").read_text())
    if (
        set(manifest) != {"schema", "files", "synthetic", "bundle_id"}
        or manifest["schema"] != SCHEMA
    ):
        raise ValueError("Invalid scientific bundle schema")
    body = {k: v for k, v in manifest.items() if k != "bundle_id"}
    if manifest["bundle_id"] != digest(body):
        raise ValueError("Changed scientific bundle identity")
    paths = list(folder.rglob("*"))
    if any(p.is_symlink() for p in paths):
        raise ValueError("Symlink in native payload")
    actual = {str(p.relative_to(folder)) for p in paths if p.is_file()} - {"manifest.json"}
    required = {name + ".csv" for name in TABLES} | {
        "result.json",
        "provenance.json",
        "scope_execution_receipt.json",
        "variant_inventory.json",
        "threshold_selection.json",
        "report.md",
        "primary_effects.svg",
        "primary_burden.svg",
        "group_effects.svg",
        "reliability.svg",
        "coverage.svg",
        "transport.svg",
        "group_effects.csv",
        "reliability_bins.csv",
        "coverage_summary.csv",
        "transport_summary.csv",
    }
    if (
        actual != set(manifest["files"])
        or not required <= actual
        or not any(n.startswith("model_artifacts/") for n in actual)
        or not {n for n in actual if n.endswith(".csv")} <= required | {"feature_provenance.csv"}
    ):
        raise ValueError("Incomplete or unexpected scientific payloads")
    for name, record in manifest["files"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Unsafe manifest path")
        payload = (folder / name).read_bytes()
        if set(record) != {"sha256", "bytes"} or record != bytes_record(payload):
            raise ValueError(f"Changed native payload {name}")
    # Every CSV is compared with its nonempty canonical reconstruction below;
    # reparsing here would impose csv.reader's unrelated process-global field cap.
    receipt = json.loads((folder / "scope_execution_receipt.json").read_text())
    if (
        receipt["synthetic"] != manifest["synthetic"]
        or receipt["G5"] != "NOT_APPROVED"
        or receipt["champion"] != "not_selected"
    ):
        raise ValueError("Invalid evidence or approval status")
    result = json.loads((folder / "result.json").read_text())
    inventory = json.loads((folder / "variant_inventory.json").read_text())
    native_tables = {name: _rows(result, name) for name in TABLES}
    _validate_tables(native_tables, inventory)
    _validate_metrics(result, native_tables)
    for name, rows in native_tables.items():
        if (folder / (name + ".csv")).read_bytes() != _csv(rows):
            raise ValueError("Scientific table differs from protected native result")
    for name, rows in (
        ("coverage_summary", _coverage_summary(native_tables["exposure_by_cluster"])),
        ("transport_summary", _transport_summary(native_tables["transport_2024_2025"])),
        ("reliability_bins", _reliability(native_tables["oof_predictions"])),
        (
            "group_effects",
            _joint_effects(
                native_tables["oof_predictions"], native_tables["exposure_by_cluster"], inventory
            ),
        ),
    ):
        if (folder / (name + ".csv")).read_bytes() != _csv(rows):
            raise ValueError("Presentation summary differs from complete native source")
    feature_provenance = _feature_provenance(result)
    if feature_provenance:
        if "feature_provenance.csv" not in actual or (
            folder / "feature_provenance.csv"
        ).read_bytes() != _csv(feature_provenance):
            raise ValueError("Feature provenance differs from protected native result")
    elif "feature_provenance.csv" in actual:
        raise ValueError("Feature provenance table lacks protected native evidence")
    thresholds = json.loads((folder / "threshold_selection.json").read_text())
    _validate_thresholds(native_tables["selection_predictions"], thresholds)
    if receipt["counts_by_phase"] != {
        **{k: result.get(k) for k in COUNTERS},
        "phases": result.get("execution_counters"),
    }:
        raise ValueError("Execution receipt counters differ from native result")
    return manifest


def _coverage_summary(exposures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate evaluation exposure once, without variant/family multiplication."""
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    fields = (
        "monitored_exposure",
        "eligible_exposure",
        "common_exposure",
        "known_covered_onsets",
        "known_eligible_onsets",
        "excluded_onsets",
    )
    for row in exposures:
        if row.get("role", "evaluation") != "evaluation":
            continue
        key = tuple(row.get(k) for k in ("horizon", "window", "municipality_code", "target_year"))
        if key in unique:
            if any(unique[key].get(k) != row.get(k) for k in fields):
                raise ValueError("Conflicting duplicated coverage ledger cluster")
            continue
        unique[key] = row
    grouped: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
    for row in unique.values():
        grouped.setdefault((row.get("horizon"), row.get("window", "unknown")), []).append(row)
    output = []
    for (horizon, window), rows in sorted(grouped.items(), key=lambda x: str(x[0])):

        def total(name: str, ledger_rows: list[dict[str, Any]] = rows) -> float:
            return sum(float(r.get(name, 0)) for r in ledger_rows)

        monitored, eligible, common = (round(12 * total(k), 10) for k in fields[:3])
        output.append(
            {
                "horizon": horizon,
                "window": window,
                "role": "evaluation",
                "ledger_clusters": len(rows),
                "monitored_months": monitored,
                "eligible_months": eligible,
                "common_months": common,
                "ineligible_covered_months": monitored - eligible,
                "eligible_without_common_predictors_months": eligible - common,
                "known_covered_onsets": total("known_covered_onsets")
                if all("known_covered_onsets" in r for r in rows)
                else None,
                "known_eligible_onsets": total("known_eligible_onsets")
                if all("known_eligible_onsets" in r for r in rows)
                else None,
                "excluded_known_eligible_onsets": total("excluded_onsets")
                if all("excluded_onsets" in r for r in rows)
                else None,
                "source": "exposure_by_cluster.csv; evaluation ledger; "
                "no variant/family multiplier",
            }
        )
    return output or [{"status": "not_evaluable", "reason": "no_evaluation_exposure_ledger"}]


def _coverage_svg(rows: list[dict[str, Any]], synthetic: bool) -> bytes:
    height = 100 + len(rows) * 58
    title = ("SYNTHETIC — " if synthetic else "") + "Coverage by horizon and source cut"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{height}">',
        f"<title>{html.escape(title)}</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="sans-serif" font-size="12" fill="#172638">',
        f'<text x="15" y="24" font-size="18">{html.escape(title)}</text>',
        '<text x="15" y="46">Source: coverage_summary.csv. Municipality-target months; '
        "blue=common, amber=eligible outside common, gray=covered ineligible.</text>",
    ]
    maximum = max([float(r.get("monitored_months", 0)) for r in rows] + [1])
    for i, row in enumerate(rows):
        y = 78 + i * 58
        label = f"T+{row.get('horizon', 'N/A')} / {row.get('window', 'unknown')}"
        parts.append(f'<text x="15" y="{y}">{html.escape(label)}</text>')
        x = 310.0
        for key, color in (
            ("common_months", "#167d9a"),
            ("eligible_without_common_predictors_months", "#d49b3b"),
            ("ineligible_covered_months", "#c4ccd2"),
        ):
            width = 530 * float(row.get(key, 0)) / maximum
            parts.append(
                f'<rect x="{x:.2f}" y="{y - 13}" width="{width:.2f}" height="18" fill="{color}"/>'
            )
            x += width
        counts = " / ".join(
            str(row.get(k, "N/A")) for k in ("monitored_months", "eligible_months", "common_months")
        )
        parts.append(f'<text x="850" y="{y}">M/E/C: {counts}</text>')
        events = " / ".join(
            str(row.get(k) if row.get(k) is not None else "N/A")
            for k in (
                "known_covered_onsets",
                "known_eligible_onsets",
                "excluded_known_eligible_onsets",
            )
        )
        parts.append(
            f'<text x="310" y="{y + 23}">Known onsets covered / eligible / '
            f"excluded from common: {events}</text>"
        )
    return ("\n".join(parts) + "</g></svg>\n").encode()


def _transport_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten every annual frozen cell; pooled/common-month views stay native."""
    output = []
    for index, row in enumerate(rows, 2):
        year = row.get("target_year", row.get("year"))
        if row.get("view", "annual") != "annual" or str(year) not in {"2024", "2025"}:
            continue
        summary = {k: v for k, v in row.items() if not isinstance(v, (dict, list))}
        summary.update(
            {k: v for k, v in row.get("metrics", {}).items() if not isinstance(v, (dict, list))}
        )
        summary.update(
            target_year=int(str(year)),
            native_source_row=index,
            source="transport_2024_2025.csv; annual frozen-cell view",
        )
        output.append(summary)
    return output or [{"status": "not_evaluable", "reason": "no_annual_transport_rows"}]


def _transport_svg(rows: list[dict[str, Any]], synthetic: bool) -> bytes:
    families = sorted({str(r.get("family", "unknown")) for r in rows})
    strata = sorted(
        {(str(r.get("horizon", "N/A")), str(r.get("objective", "onset"))) for r in rows}
    )
    nvariants = max(
        [
            len(
                {
                    str(r.get("variant", "N/A"))
                    for r in rows
                    if (str(r.get("horizon", "N/A")), str(r.get("objective", "onset"))) == stratum
                }
            )
            for stratum in strata
        ]
        + [1]
    )
    panel_height = 95 + nvariants * 23
    height, width = 85 + len(strata) * panel_height, max(1, len(families)) * 520
    title = ("SYNTHETIC — " if synthetic else "") + "Frozen transport: all annual cells"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f"<title>{html.escape(title)}</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="sans-serif" font-size="11" fill="#172638">',
        f'<text x="15" y="24" font-size="18">{html.escape(title)}</text>',
        '<text x="15" y="45">2024 blue; 2025 orange. Every variant shown. '
        "Source: transport_summary.csv; common-month/pooled views: transport_2024_2025.csv.</text>",
    ]
    maximum = max(
        [_number(r, "false_alerts_per_monitored_municipality_year") or 0 for r in rows] + [1]
    )
    for i, (horizon, objective) in enumerate(strata):
        for j, family in enumerate(families):
            x, y = j * 520, 80 + i * panel_height
            selected = [
                r
                for r in rows
                if str(r.get("family", "unknown")) == family
                and str(r.get("horizon", "N/A")) == horizon
                and str(r.get("objective", "onset")) == objective
            ]
            variants = sorted({str(r.get("variant", "N/A")) for r in selected})
            parts.append(
                f'<text x="{x + 10}" y="{y}" font-size="14">'
                f"{html.escape(family)} / T+{horizon} / {html.escape(objective)}</text>"
            )
            parts.append(f'<text x="{x + 72}" y="{y + 21}">Sensitivity [0,1]</text>')
            parts.append(
                f'<text x="{x + 285}" y="{y + 21}">FP / monitored year [0,{maximum:.3g}]</text>'
            )
            for k, variant in enumerate(variants):
                row_y = y + 45 + 23 * k
                parts.append(f'<text x="{x + 10}" y="{row_y}">{html.escape(variant)}</text>')
                for metric, start, scale in (
                    ("onset_sensitivity", x + 78, 1),
                    ("false_alerts_per_monitored_municipality_year", x + 295, maximum),
                ):
                    parts.append(
                        f'<line x1="{start}" x2="{start + 160}" y1="{row_y - 3}" '
                        f'y2="{row_y - 3}" stroke="#e0e4e8"/>'
                    )
                    for year, offset, color in ((2024, -3, "#167d9a"), (2025, 3, "#c5701d")):
                        match = next(
                            (
                                r
                                for r in selected
                                if str(r.get("variant", "N/A")) == variant
                                and r.get("target_year") == year
                            ),
                            {},
                        )
                        value = _number(match, metric)
                        point_y = row_y - 3 + offset
                        if value is None:
                            parts.append(
                                f'<text x="{start + 164}" y="{point_y + 3}" '
                                f'fill="{color}">N/A</text>'
                            )
                        else:
                            point_x = start + 160 * value / scale
                            description = html.escape(
                                f"{variant} {year} {metric}={value:.5g}; "
                                f"native row {match.get('native_source_row')}"
                            )
                            parts.append(
                                f'<circle cx="{point_x:.2f}" cy="{point_y}" r="3" '
                                f'fill="{color}"><title>{description}</title></circle>'
                            )
    return ("\n".join(parts) + "</g></svg>\n").encode()
