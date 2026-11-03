#!/usr/bin/env python3
"""Run the controlled EXP-DELTA02-R1 procedure after its gates are implemented."""

from __future__ import annotations

import argparse

from sat_dengue.experiments.exp_delta02_r1 import feature_self_check


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if not args.self_check:
        parser.error("candidate execution is not implemented until the next authorized task")
    feature_self_check()
    print("PASS: MGN edge/point/self and exact T-1 feature controls")


if __name__ == "__main__":
    main()
