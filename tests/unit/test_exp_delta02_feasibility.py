"""Generated-only source fences for the bounded spatial admission audit."""

import json
from pathlib import Path

import pytest

from sat_dengue.datasets.stage2 import identity
from scripts.audit_exp_delta02_feasibility import verified_bundle


@pytest.mark.parametrize("corruption", ["payload", "manifest", "extra"])
def test_geography_publication_tampering_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    monkeypatch.chdir(tmp_path)
    root = Path("source")
    root.mkdir()
    payload = root / "source.json"
    payload.write_text('{"official":true}')
    manifest = root / "manifest.json"
    manifest.write_text(json.dumps({"files": {payload.name: identity(payload)}}))
    pinned = {"path": str(root), "manifest_sha256": identity(manifest)["sha256"]}
    verified_bundle(pinned)
    if corruption == "extra":
        (root / "unexpected").write_bytes(b"extra")
    else:
        (payload if corruption == "payload" else manifest).write_text("changed")
    with pytest.raises(ValueError, match="changed|inventory"):
        verified_bundle(pinned)
