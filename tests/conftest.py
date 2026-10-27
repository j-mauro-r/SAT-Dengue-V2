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
    import importlib.metadata
    import json
    import sys

    from sat_dengue.experiments.exp03 import synthetic_run

    files = sorted(Path("src").rglob("*.py"))
    files += sorted(Path("docs/product/experiments").rglob("protocol.json"))
    files += [Path("pyproject.toml")]
    versions = sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions())
    fingerprint = hashlib.sha256(
        b"".join(str(p).encode() + p.read_bytes() for p in files)
        + json.dumps(versions).encode()
        + sys.version.encode()
    ).hexdigest()
    cache = Path("tmp/exp03-generated-fixtures") / fingerprint
    cache.mkdir(parents=True, exist_ok=True)
    saved = cache / "generated-result.json"
    if saved.exists():
        if (cache / "payload.sha256").read_text() != hashlib.sha256(saved.read_bytes()).hexdigest():
            raise ValueError("Generated fixture cache changed")
        value = json.loads(saved.read_text())
        value["model_artifacts"] = {
            k: base64.b64decode(v) for k, v in value["model_artifacts"].items()
        }
        return value
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
