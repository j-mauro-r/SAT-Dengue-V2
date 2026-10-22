"""Subprocess entry point: import historical code, deny fits/writes, verify saved replay."""

from __future__ import annotations

import importlib.metadata
import json
import os
import sys
from pathlib import Path
from types import FrameType
from typing import Any

from migration_support import (
    BASELINE_SHA256,
    FINAL_PATH,
    active_chain,
    approved_scope,
    fingerprint,
    require_records,
    source_records,
    verify_native_bundle,
)


def deny_fitting(frame: FrameType, event: str, arg: Any) -> None:
    """Catch aliases as well as direct estimator/preparer fitting calls."""
    if event != "call":
        return
    name = frame.f_code.co_name
    if name.startswith(("fit", "_fit")) or name in {
        "select_threshold",
        "_select_threshold",
        "publish_bundle",
        "publish_artifacts",
    }:
        raise AssertionError(f"Forbidden fit/selection/publication during replay: {name}")


def deny_writes(event: str, args: tuple[Any, ...]) -> None:
    if event == "open" and isinstance(args[0], (str, bytes)):
        flags = args[2]
        if isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            raise AssertionError("Replay must not write files")


def main() -> None:
    if not __debug__:
        raise RuntimeError("Optimized Python disables required replay assertions")
    root, snapshot = Path(sys.argv[1]), Path(sys.argv[2])
    expected_version = sys.argv[3]
    assert importlib.metadata.version("lightgbm") == expected_version
    baseline_path = root / "tmp/kedro-migration/baseline.json"
    assert fingerprint(baseline_path)["sha256"] == BASELINE_SHA256
    baseline = json.loads(baseline_path.read_text())
    require_records(root, {name: baseline["protected"][name] for name in baseline["bundles"]})
    manifest = verify_native_bundle(root / FINAL_PATH)
    identity = manifest["identity"]
    for name, version in identity["versions"].items():
        assert importlib.metadata.version(name) == (
            expected_version if name == "lightgbm" else version
        ), f"Unexpected runtime drift: {name}"
    require_records(root, identity["inputs"])
    # The native final engine is recovered from its file hashes, not assumed from HEAD.
    for name, expected in identity["code"].items():
        if name.endswith(".py"):
            assert fingerprint(snapshot / name) == expected, f"Historical source changed: {name}"

    from scripts.final_evaluation.cohorts import load_cohorts
    from scripts.final_evaluation.pipeline import execute_bundle
    from scripts.final_evaluation.protocol import PROPOSAL_BUNDLE, PROPOSAL_SHA

    proposal_path = root / PROPOSAL_BUNDLE / "freeze_proposal.json"
    assert fingerprint(proposal_path)["sha256"] == PROPOSAL_SHA
    assert fingerprint(root / PROPOSAL_BUNDLE / "manifest.json") == identity["proposal_manifest"]
    verify_native_bundle(root / PROPOSAL_BUNDLE)
    proposal = json.loads(proposal_path.read_text())
    # Verify every loaded repository module against a historical identity, not live code.
    historical_hashes: dict[str, set[str]] = {}
    for name in baseline["bundles"]:
        source = json.loads((root / name).read_text()).get("identity", {})
        for group in ("code", "stage4_code"):
            for path, value in source.get(group, {}).items():
                if isinstance(value, dict) and "sha256" in value:
                    historical_hashes.setdefault(path, set()).add(value["sha256"])
    for module_name, module in list(sys.modules.items()):
        module_file = getattr(module, "__file__", None)
        if module_name.startswith("scripts.") and module_file:
            path = Path(module_file).resolve()
            assert path.is_relative_to(snapshot), "Imported live rather than historical source"
            relative = str(path.relative_to(snapshot))
            assert fingerprint(path)["sha256"] in historical_hashes.get(relative, set()), (
                f"Imported source has no historical hash: {relative}"
            )
    # Only approved active bundles may support equivalence; historical exceptions cannot.
    scope = approved_scope(root)
    visited = active_chain(root, baseline, str(FINAL_PATH / "manifest.json"))
    assert sorted(visited) == scope["active_chain"]
    assert not visited.intersection(scope["historical_bundles"])
    active_sources: dict[str, set[str]] = {}
    for name in visited:
        source = json.loads((root / name).read_text()).get("identity", {})
        for path, sha in source_records(source):
            active_sources.setdefault(path, set()).add(sha)
    checked: set[str] = set()
    source_prefix = str(snapshot / "scripts") + os.sep

    def guard(frame: FrameType, event: str, arg: Any) -> None:
        if event != "call":
            return
        deny_fitting(frame, event, arg)
        name = frame.f_code.co_filename
        if name.startswith(source_prefix) and name not in checked:
            relative = str(Path(name).relative_to(snapshot))
            assert fingerprint(Path(name))["sha256"] in active_sources.get(relative, set()), (
                f"Executed code differs from the active scientific chain: {relative}"
            )
            checked.add(name)

    sys.setprofile(guard)
    sys.addaudithook(deny_writes)
    print("Verifying complete historical cohorts and native saved components", file=sys.stderr)
    cohorts, inputs = load_cohorts(root, proposal)
    assert inputs == identity["inputs"]
    assert set(cohorts) == {1, 2}
    assert all(len(c.X) == 912 and len(c.X.columns) == 29 for c in cohorts.values())
    # Native verification also compares regenerated predictions, metrics, masks, alerts,
    # decisions, context, resampling draws and preparer identities byte for byte.
    result = execute_bundle(root, proposal, cohorts, identity, verify_only=True)
    assert result["new_model_fits"] == result["new_preparer_fits"] == 0
    summary = result["summary"]
    assert summary["G5"] == "NOT_APPROVED" and summary["champion"] == "not_selected"
    assert len(summary["comparison"]) == 8
    assert {(row["candidate"], row["horizon"]) for row in summary["comparison"]} == {
        (family, h) for family in ("persistence", "xgboost", "lightgbm", "gam") for h in (1, 2)
    }
    assert all(
        row["result"] == "does_not_meet"
        for row in summary["comparison"]
        if row["candidate"] != "persistence"
    )
    print(
        json.dumps(
            dict(
                version=expected_version,
                models=6,
                predictions=5472,
                new_fits=0,
                native_payloads=len(manifest["files"]),
                dependency_bundles=len(visited),
                equivalence_bundles=sorted(visited),
                full_historical_reproducibility=False,
                consumed_2025=True,
                allow_2025_selection_tuning_training=False,
                new_real_fits=result["new_model_fits"] + result["new_preparer_fits"],
                executed_source_files=len(checked),
                G5=summary["G5"],
                champion=summary["champion"],
            )
        )
    )


if __name__ == "__main__":
    main()
