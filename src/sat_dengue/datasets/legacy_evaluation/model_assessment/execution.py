"""Execute notebook08 from a fresh kernel or verify it without fitting."""

from __future__ import annotations

import json
from typing import Any

from sat_dengue.datasets.evaluation_cli import main as main


def extract_summary(notebook: dict[str, Any]) -> dict[str, Any]:
    """Require successful sequential code-only execution and one exact summary."""
    cells = notebook["cells"]
    if not cells or any(c["cell_type"] != "code" for c in cells):
        raise ValueError("Expected code-only notebook")
    if [c.get("execution_count") for c in cells] != list(range(1, len(cells) + 1)):
        raise ValueError("Notebook must execute all cells sequentially")
    outputs = [o for c in cells for o in c.get("outputs", [])]
    if any(o["output_type"] == "error" for o in outputs):
        raise ValueError("Notebook contains execution errors")
    summaries = []
    for output in outputs:
        if output.get("output_type") == "stream":
            text = "".join(output.get("text", []))
            if '"model_assessment_run"' in text:
                summaries.append(json.loads(text)["model_assessment_run"])
    if len(summaries) != 1:
        raise ValueError("Exactly one machine-readable summary required")
    return summaries[0]


if __name__ == "__main__":
    main()
