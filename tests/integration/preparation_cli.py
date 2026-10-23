"""Run the actual preparation CLI with call-level real-fit denial."""

from __future__ import annotations

import sys
from types import FrameType
from typing import Any

from sat_dengue.pipeline_registry import register_pipelines


def deny_fits(frame: FrameType, event: str, arg: Any) -> None:
    if event == "call" and frame.f_code.co_name.startswith(("fit", "_fit")):
        raise AssertionError(f"Real model/preparer fit forbidden: {frame.f_code.co_name}")


if __name__ == "__main__":
    from kedro.framework.cli import main

    # Initialize registered modules before guarding execution, including sklearn decorators.
    register_pipelines()
    sys.setprofile(deny_fits)
    sys.argv = ["kedro", "run", "--pipeline=preparation", "--params=profile=preparation"]
    main()
