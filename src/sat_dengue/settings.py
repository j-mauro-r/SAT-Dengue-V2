"""Register the validated operational configuration loader."""

from sat_dengue.config_loader import ValidatedConfigLoader

CONFIG_LOADER_CLASS = ValidatedConfigLoader
CONFIG_LOADER_ARGS = {"base_env": "base", "default_run_env": "base"}
DISABLE_HOOKS_FOR_PLUGINS = ("kedro-telemetry",)
