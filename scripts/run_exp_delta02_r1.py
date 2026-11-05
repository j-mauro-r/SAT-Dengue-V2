#!/usr/bin/env python3
"""Run the controlled EXP-DELTA02-R1 procedure after its gates are implemented."""

from __future__ import annotations

import argparse
import json

from sat_dengue.experiments.exp_delta02_r1 import (
    execute_real,
    feature_self_check,
    load_preflight,
    publish_real,
    reproduce_real,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--self-check", action="store_true")
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--publish", action="store_true")
    action.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        feature_self_check()
        print("PASS: MGN edge/point/self and exact T-1 feature controls")
        return
    if args.preflight:
        checked = load_preflight()
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "targets": int(checked["frame"].municipality_code.nunique()),
                    "graph_edges_directed": len(checked["graph"]),
                    "evaluation_rows": 2653,
                    "evaluation_onsets": 313,
                }
            )
        )
        return
    result, payloads = execute_real()
    path = publish_real(payloads) if args.publish else reproduce_real(payloads)
    print(
        json.dumps(
            {
                "status": "PUBLISHED" if args.publish else "REPRODUCTION_PASS",
                "path": str(path),
                "scientific_disposition": result["disposition"],
            }
        )
    )


if __name__ == "__main__":
    main()
