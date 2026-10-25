"""Shared isolated fixtures for public synthetic integration tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def synthetic_experiments(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the real resolver with isolated registered synthetic protocols."""
    from sat_dengue.configuration import canonical_bytes
    from sat_dengue.tracking import experiments

    registry = yaml.safe_load(experiments.REGISTRY.read_text())
    original = registry["experiments"][0]
    protocol = json.loads(Path(original["protocol"]).read_text())
    entries = []
    base = (repo_tmp_path / "docs/product/experiments").relative_to(ROOT)
    for identifier in ("EXP91", "EXP92", "EXP93"):
        entry = dict(original)
        document = json.loads(json.dumps(protocol))
        for target in (entry, document, document["mlflow"]["required_conceptual_tags"]):
            target.update(
                experiment_id=identifier,
                hypothesis_id=identifier + "-H0",
                experiment_slug="synthetic_tracking_fixture",
            )
        document["execution"]["kedro_pipeline"] = (
            "replay_synthetic" if identifier == "EXP93" else "evaluation_synthetic"
        )
        entry["pipeline"] = document["execution"]["kedro_pipeline"]
        path = base / identifier / "protocol.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(canonical_bytes(document))
        entry["protocol"] = str(path)
        entry["conclusions"] = str(path.with_name("CONCLUSIONS.md"))
        entry["protocol_sha256"] = hashlib.sha256(canonical_bytes(document)).hexdigest()
        entries.append(entry)
    registry["experiments"] = entries
    path = base / "experiment-registry.yml"
    path.write_text(yaml.safe_dump(registry))
    monkeypatch.setattr(experiments, "REGISTRY", path)
