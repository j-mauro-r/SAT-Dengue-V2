"""Generated cache invalidation uses controlled inputs, with no estimator fitting."""

from pathlib import Path

import pytest
from exp03_fixture_cache import fixture_fingerprint


@pytest.mark.parametrize(
    "path",
    [
        "src/module.py",
        "docs/product/stage-3/training_preparation_contract_v1.json",
        "docs/product/experiments/EXP03_feature_ablation/protocol.json",
        "docs/product/experiments/EXP03_feature_ablation/alcance.md",
        "pyproject.toml",
    ],
)
def test_consumed_file_change_invalidates_fixture_cache(repo_tmp_path: Path, path: str) -> None:
    for name in (
        "src/module.py",
        "docs/product/stage-3/training_preparation_contract_v1.json",
        "docs/product/experiments/EXP03_feature_ablation/protocol.json",
        "docs/product/experiments/EXP03_feature_ablation/alcance.md",
        "pyproject.toml",
    ):
        file = repo_tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("initial")
    before = fixture_fingerprint(repo_tmp_path, {"runtime": "fixed"})
    assert before == fixture_fingerprint(repo_tmp_path, {"runtime": "fixed"})
    assert before != fixture_fingerprint(repo_tmp_path, {"runtime": "changed"})
    (repo_tmp_path / path).write_text("changed")
    assert before != fixture_fingerprint(repo_tmp_path, {"runtime": "fixed"})
    assert before != fixture_fingerprint(repo_tmp_path, {"runtime": "changed"})


def test_cached_payload_integrity_is_rechecked_on_every_hit(repo_tmp_path: Path) -> None:
    import hashlib
    import json

    from exp03_fixture_cache import load_cached_result

    assert load_cached_result(repo_tmp_path) is None
    saved = repo_tmp_path / "generated-result.json"
    saved.write_text(json.dumps({"model_artifacts": {"model": "eA=="}}))
    (repo_tmp_path / "payload.sha256").write_text(hashlib.sha256(saved.read_bytes()).hexdigest())
    assert load_cached_result(repo_tmp_path) == {"model_artifacts": {"model": b"x"}}
    saved.write_bytes(saved.read_bytes() + b" ")
    with pytest.raises(ValueError, match="cache changed"):
        load_cached_result(repo_tmp_path)
