"""Non-scientific generated-fixture identity; never loads private inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def fixture_fingerprint(root: Path, identity: dict[str, Any]) -> str:
    """Bind numeric inputs and the public provenance actually consumed by synthetic_run."""
    files = sorted(root.joinpath("src").rglob("*.py"))
    files += sorted(root.joinpath("docs/product/experiments").rglob("protocol.json"))
    files += [
        root / "pyproject.toml",
        root / "docs/product/stage-3/training_preparation_contract_v1.json",
        root / "docs/product/experiments/EXP03_feature_ablation/alcance.md",
    ]
    return hashlib.sha256(
        b"".join(str(p.relative_to(root)).encode() + p.read_bytes() for p in files)
        + json.dumps(identity, sort_keys=True).encode()
    ).hexdigest()


def load_cached_result(cache: Path) -> dict[str, Any] | None:
    """A cache hit never bypasses payload integrity; serialized bytes are non-executable."""
    import base64

    saved = cache / "generated-result.json"
    if not saved.exists():
        return None
    if (cache / "payload.sha256").read_text() != hashlib.sha256(saved.read_bytes()).hexdigest():
        raise ValueError("Generated fixture cache changed")
    value: dict[str, Any] = json.loads(saved.read_text())
    value["model_artifacts"] = {
        key: base64.b64decode(payload, validate=True)
        for key, payload in value["model_artifacts"].items()
    }
    return value
