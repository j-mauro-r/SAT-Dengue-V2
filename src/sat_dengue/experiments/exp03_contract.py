"""Check or regenerate the revised frozen matrix from the canonical recipe source."""

from __future__ import annotations

import argparse
import json
from typing import Any

import yaml  # type: ignore[import-untyped]

from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03 import PROTOCOL
from sat_dengue.experiments.exp03_revision import build_design, cell_counts, validate_design


def matrix(protocol: dict[str, Any]) -> dict[str, Any]:
    design = protocol["design"]
    validate_design(design)
    return {
        "schema": "exp03-ablation-matrix-v2",
        "protocol_sha256": digest(protocol),
        "revision": design["revision"],
        "groups": design["groups"],
        "variants": design["variants"],
        "contrasts": design["contrasts"],
        "derived_counts": cell_counts(design),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    protocol = json.loads(PROTOCOL.read_text())
    canonical = build_design(protocol["design"])
    # A separately chosen real budget is not invented or overwritten by generation.
    for key in ("B_primary", "budget_units", "budget_rationale"):
        canonical[key] = protocol["design"][key]
    if canonical != protocol["design"]:
        raise ValueError(
            "Protocol design differs from canonical source; review revision before regeneration"
        )
    target = PROTOCOL.with_name("ablation-matrix.frozen.yml")
    expected = matrix(protocol)
    if args.check:
        if yaml.safe_load(target.read_text()) != expected:
            raise ValueError("Frozen matrix differs from canonical protocol/design")
    else:
        target.write_text(yaml.safe_dump(expected, sort_keys=False, allow_unicode=True))
    print(json.dumps({"protocol_sha256": digest(protocol), "counts": cell_counts(canonical)}))


if __name__ == "__main__":
    main()
