"""Run the installed Kedro project from its repository root."""

from pathlib import Path

from kedro.framework.cli.utils import find_run_command
from kedro.framework.startup import bootstrap_project


def main() -> None:
    """Dispatch the standard Kedro project command."""
    bootstrap_project(Path.cwd())
    find_run_command("sat_dengue")()


if __name__ == "__main__":
    main()
