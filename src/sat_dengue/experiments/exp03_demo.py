"""Generate the complete EXP03 example from generated inputs, with no tracking."""

from __future__ import annotations

import argparse
from pathlib import Path

from sat_dengue.experiments.exp03 import load_protocol, synthetic_run
from sat_dengue.experiments.exp03_reporting import write_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="tmp/exp03-generated-example")
    args = parser.parse_args()
    protocol = load_protocol()
    result = synthetic_run()
    provenance = result["synthetic_provenance"]
    manifest = write_bundle(Path(args.output), result, provenance, protocol["design"])
    print(f"SYNTHETIC ONLY: {args.output}/report.md; bundle {manifest['bundle_id']}")


if __name__ == "__main__":
    main()
