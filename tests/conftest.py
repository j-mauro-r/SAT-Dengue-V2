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
