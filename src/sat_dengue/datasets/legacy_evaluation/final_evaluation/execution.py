"""Fresh-kernel notebook08 execution with an explicit, separately authorized science mode."""

from __future__ import annotations

import json
from typing import Any

from sat_dengue.datasets.evaluation_cli import main as main


def extract_summary(notebook: dict[str, Any]) -> dict[str, Any]:
    """Extract exactly one successful sequential code-only notebook result.

    Args:
        notebook: Notebook document with saved execution outputs.

    Returns:
        Machine-readable readiness or scientific-run summary.
    """
    cells = notebook["cells"]
    if (
        not cells
        or any(c["cell_type"] != "code" for c in cells)
        or [c.get("execution_count") for c in cells] != list(range(1, len(cells) + 1))
    ):
        raise ValueError("Expected successful sequential code-only notebook")
    found = []
    for cell in cells:
        for output in cell.get("outputs", []):
            if output["output_type"] == "error":
                raise ValueError("Notebook contains errors")
            if output["output_type"] == "stream":
                text = "".join(output.get("text", []))
                if '"final_evaluation_run"' in text:
                    found.append(json.loads(text)["final_evaluation_run"])
    if len(found) != 1:
        raise ValueError("Exactly one notebook summary required")
    return found[0]


if __name__ == "__main__":
    main()
