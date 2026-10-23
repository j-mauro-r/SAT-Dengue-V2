"""Kedro lifecycle boundary for explicitly enabled, optional local tracking."""

from __future__ import annotations

from typing import Any

from kedro.framework.hooks import hook_impl


class TrackingHooks:
    def __init__(self) -> None:
        self.tracker: Any = None

    @hook_impl
    def before_pipeline_run(self, run_params: dict[str, Any], catalog: Any) -> None:
        self.tracker = None
        parameters = catalog.load("parameters")
        if parameters["tracking"] == "disabled":
            return
        if parameters["tracking"] != "enabled":
            raise ValueError("Tracking must be explicitly enabled or disabled")
        from sat_dengue.tracking.local import LocalTracking

        profile = parameters["profile"]
        if profile not in {
            "training_replay",
            "training_synthetic",
            "evaluation_replay",
            "evaluation_synthetic",
        }:
            raise ValueError("Enabled tracking requires a training/evaluation publication profile")
        self.output = "training_bundle" if profile.startswith("training_") else "evaluation_bundle"
        pipeline = run_params.get("pipeline_name") or profile
        self.tracker = LocalTracking(
            pipeline, run_params.get("session_id", run_params.get("run_id", "execution"))
        )

    @hook_impl
    def after_pipeline_run(self, catalog: Any) -> None:
        if self.tracker is None:
            return
        try:
            self.tracker.finish(catalog.load(self.output))
        except BaseException:
            self.tracker.fail()
            raise

    @hook_impl
    def on_pipeline_error(self, error: BaseException) -> None:
        if self.tracker is not None:
            self.tracker.fail(aborted=isinstance(error, (KeyboardInterrupt, SystemExit)))
