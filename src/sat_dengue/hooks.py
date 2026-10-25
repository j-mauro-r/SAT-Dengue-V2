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
        from sat_dengue.configuration import validate_parameters

        parameters = catalog.load("parameters")
        selected = run_params.get("pipeline_names") or [run_params.get("pipeline_name")]
        pipeline = selected[0] if len(selected) == 1 else None
        if pipeline in {"replay", "replay_synthetic"}:
            parameters = {**parameters, "profile": pipeline}
        parameters = validate_parameters(parameters)
        if parameters["tracking"] == "disabled":
            return
        if parameters["tracking"] != "enabled":
            raise ValueError("Tracking must be explicitly enabled or disabled")
        from sat_dengue.tracking.local import LocalTracking

        profile = parameters["profile"]
        if pipeline in {"replay", "replay_synthetic"}:
            profile = pipeline
        if profile not in {
            "replay",
            "replay_synthetic",
            "training_replay",
            "training_synthetic",
            "evaluation_replay",
            "evaluation_synthetic",
        }:
            raise ValueError("Enabled tracking requires a training/evaluation publication profile")
        self.output = "training_bundle" if profile.startswith("training_") else "evaluation_bundle"
        if profile in {"replay", "replay_synthetic"}:
            self.output = "replay_bundle"
        pipeline = pipeline or profile
        self.tracker = LocalTracking(
            pipeline,
            run_params.get("session_id", run_params.get("run_id", "execution")),
            experiment_id=parameters.get("experiment_id"),
        )

    @hook_impl
    def after_pipeline_run(self, catalog: Any) -> None:
        if self.tracker is None:
            return
        try:
            published = catalog.load(self.output)
            if self.output == "replay_bundle":
                published = published["stages"]["evaluation"]
            self.tracker.finish(published)
        except BaseException:
            self.tracker.fail()
            raise

    @hook_impl
    def on_pipeline_error(self, error: BaseException) -> None:
        if self.tracker is not None:
            self.tracker.fail(aborted=isinstance(error, (KeyboardInterrupt, SystemExit)))
