"""Equal-window development comparisons, support and paired sensitivity intervals."""

from __future__ import annotations

from itertools import product
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .policy import utility


def summarize(metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Aggregate complete four-window populations without available-only averages.

    Args:
        metrics: One record per candidate, window and approved metric.

    Returns:
        Metric means/support, separate utility/ranking, descriptive paired intervals.
    """
    records: list[dict[str, Any]] = []
    for (candidate, horizon, metric), group in metrics.groupby(["candidate", "horizon", "metric"]):
        if len(group) != 4 or group.window_id.nunique() != 4:
            raise ValueError("Exactly four unique windows are required")
        available = group.evaluable.astype(bool) & group.value.notna()
        records.append(
            dict(
                candidate=candidate,
                horizon=horizon,
                metric=metric,
                value=float(group.value.mean()) if available.all() else None,
                evaluable_windows=int(available.sum()),
                expected_windows=4,
                numerator_sum=float(group.numerator.sum()),
                denominator_sum=float(group.denominator.sum()),
                aggregation="equal_window_mean; counts summed separately, not used as weights",
            )
        )
    summary = pd.DataFrame(records)
    draws = np.array(list(product(range(4), repeat=4)))
    intervals: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for horizon in (1, 2):
        wide = summary[summary.horizon.eq(horizon)].pivot(
            index="candidate", columns="metric", values="value"
        )
        ranking = wide.drop(index="persistence").average_precision.rank(
            ascending=False, method="min"
        )
        for candidate in sorted(set(metrics.candidate) - {"persistence"}):
            gain = (
                wide.loc[candidate, "onset_sensitivity"]
                - wide.loc["persistence", "onset_sensitivity"]
            )
            increase = (
                wide.loc[candidate, "false_alarm_ratio"]
                - wide.loc["persistence", "false_alarm_ratio"]
            )
            decisions.append(
                dict(
                    candidate=candidate,
                    horizon=horizon,
                    descriptive_ap_rank=ranking[candidate],
                    onset_gain_pp=100 * gain,
                    false_alarm_increase_pp=100 * increase,
                    point_utility=utility(gain, increase),
                    research_acceptance="not_determined_by_development_point_estimates",
                )
            )
            for metric in sorted(metrics.metric.unique()):
                subset = metrics[metrics.horizon.eq(horizon) & metrics.metric.eq(metric)]
                values = subset.pivot(
                    index="window_id", columns="candidate", values="value"
                ).sort_index()
                for comparison in ("candidate", "difference_vs_persistence"):
                    vector = values[candidate].to_numpy(dtype=float)
                    if comparison == "difference_vs_persistence":
                        vector = vector - values.persistence.to_numpy(dtype=float)
                    samples = vector[draws].mean(axis=1)
                    valid = np.isfinite(samples)
                    bounds = np.quantile(samples, [0.025, 0.975]) if valid.all() else [None, None]
                    intervals.append(
                        dict(
                            candidate=candidate,
                            horizon=horizon,
                            metric=metric,
                            comparison=comparison,
                            lower=bounds[0],
                            upper=bounds[1],
                            valid_draws=int(valid.sum()),
                            total_draws=256,
                            method="paired_whole_window_bootstrap_all_ordered_draws",
                            interpretation="descriptive_sensitivity_only_four_clusters_not_calibrated_CI",
                        )
                    )
    return summary, pd.DataFrame(decisions), pd.DataFrame(intervals)
