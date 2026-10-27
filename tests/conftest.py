"""Keep private migration acceptance explicit and fail closed when it is requested."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--require-migration-evidence",
        action="store_true",
        help="Require protected local migration inputs, runtimes and eligible comparisons.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "migration_evidence: requires immutable private migration evidence"
    )


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    private = [item for item in items if item.get_closest_marker("migration_evidence")]
    if config.getoption("--require-migration-evidence"):
        if not private:
            raise pytest.UsageError(
                "--require-migration-evidence selected zero eligible migration comparisons"
            )
    elif private:
        items[:] = [item for item in items if item not in private]
        config.hook.pytest_deselected(items=private)


@pytest.fixture
def repo_tmp_path() -> Iterator[Path]:
    """Own one isolated repository-local workspace, independently of checkout state."""
    parent = Path(__file__).resolve().parents[1] / "tmp"
    created = False
    try:
        parent.mkdir()
        created = True
    except FileExistsError:
        pass
    try:
        with TemporaryDirectory(dir=parent, prefix="pytest-workspace-") as directory:
            yield Path(directory)
    finally:
        if created:
            try:
                parent.rmdir()  # Never remove another test/process's content.
            except OSError:
                pass


@pytest.fixture(scope="session")
def exp03_generated_result() -> dict:
    """Generated native fits cached by scientific code fingerprint, never private sources."""
    import base64
    import hashlib
    import json

    from exp03_fixture_cache import fixture_fingerprint, load_cached_result

    from sat_dengue.experiments.exp01_preflight import execution_metadata, git_identity
    from sat_dengue.experiments.exp03 import load_protocol, synthetic_run

    # These validations run on every session, including cache hits. Freeze time
    # remains the producer's; provenance changes invalidate rather than relabel it.
    protocol = load_protocol()
    fingerprint = fixture_fingerprint(
        Path.cwd(),
        {
            "protocol": protocol,
            "execution": execution_metadata(),
            "git": git_identity(),
        },
    )
    cache = Path("tmp/exp03-generated-fixtures") / fingerprint
    cache.mkdir(parents=True, exist_ok=True)
    saved = cache / "generated-result.json"
    cached = load_cached_result(cache)
    if cached is not None:
        return cached
    value = synthetic_run()
    encoded = {
        **value,
        "model_artifacts": {
            k: base64.b64encode(v).decode("ascii") for k, v in value["model_artifacts"].items()
        },
    }
    saved.write_text(json.dumps(encoded, allow_nan=False))
    (cache / "payload.sha256").write_text(hashlib.sha256(saved.read_bytes()).hexdigest())
    return value
