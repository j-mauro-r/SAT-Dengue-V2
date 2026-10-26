"""Only the two approved EXP01 path representations may reach publication."""

from pathlib import Path

import pytest

from sat_dengue.datasets.exp01 import Exp01BundleDataset
from sat_dengue.experiments.exp01_preflight import OUTPUT_ROOT, safe_path


@pytest.fixture
def project(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = repo_tmp_path / "project"
    root.mkdir()
    (root / "AGENTS.md").write_text("Generated test project")
    (root / "pyproject.toml").write_text("# Generated test project")
    monkeypatch.chdir(root)
    return root


@pytest.mark.parametrize("absolute", [False, True])
def test_exact_relative_and_canonical_absolute_paths_are_equivalent(
    project: Path, absolute: bool
) -> None:
    path = str(project / OUTPUT_ROOT) if absolute else OUTPUT_ROOT
    dataset = Exp01BundleDataset(path)
    assert dataset._describe()["filepath"] == OUTPUT_ROOT
    assert not (project / OUTPUT_ROOT).exists()


@pytest.mark.parametrize(
    "path",
    [
        "",
        "tmp/kedro-migration/exp01-runs-neighbor",
        "tmp/exp01-runs",
        "data/exp01-runs",
        "tmp/kedro-migration/elsewhere",
        "tmp/kedro-migration/x/../exp01-runs",
        "./tmp/kedro-migration/exp01-runs",
        "https://example.com/exp01-runs",
        "s3://bucket/exp01-runs",
        "file:///tmp/kedro-migration/exp01-runs",
    ],
)
def test_alternative_relative_uri_and_traversal_paths_are_rejected(
    project: Path, path: str
) -> None:
    with pytest.raises(ValueError, match="fixed catalog"):
        Exp01BundleDataset(path)


@pytest.mark.parametrize(
    "kind", ["external", "neighbor", "outside_tmp", "other_directory", "traversal"]
)
def test_absolute_paths_must_match_exact_canonical_location(project: Path, kind: str) -> None:
    paths = {
        "external": project.parent / "external/exp01-runs",
        "neighbor": project / (OUTPUT_ROOT + "-neighbor"),
        "outside_tmp": project / "data/exp01-runs",
        "other_directory": project / "tmp/kedro-migration/other",
        "traversal": project / "tmp/kedro-migration/x/../exp01-runs",
    }
    with pytest.raises(ValueError, match="fixed catalog"):
        Exp01BundleDataset(str(paths[kind]))


@pytest.mark.parametrize("absolute", [False, True])
@pytest.mark.parametrize("component", ["ancestor", "output"])
def test_symlink_in_output_ancestry_is_rejected(
    project: Path, absolute: bool, component: str
) -> None:
    target = project / "generated-target"
    target.mkdir()
    if component == "ancestor":
        (project / "tmp").symlink_to(target, target_is_directory=True)
    else:
        (project / OUTPUT_ROOT).parent.mkdir(parents=True)
        (project / OUTPUT_ROOT).symlink_to(target, target_is_directory=True)
    path = str(project / OUTPUT_ROOT) if absolute else OUTPUT_ROOT
    with pytest.raises(ValueError, match="fixed catalog"):
        Exp01BundleDataset(path)


def test_global_safe_path_still_rejects_absolute_paths(project: Path) -> None:
    with pytest.raises(ValueError, match="repository-local"):
        safe_path(str(project / OUTPUT_ROOT), temporary=True)


def test_unsafe_catalog_materialization_stops_preflight_before_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sat_dengue.experiments import exp01_preflight as checks

    descriptor = {"schema": "exp01-source-descriptor-v1", "files": {}}
    monkeypatch.setattr(checks, "source_metadata", lambda: descriptor)

    def unsafe_catalog() -> None:
        raise ValueError("Unsafe publication catalog")

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("Execution beyond invalid materialization")

    monkeypatch.setattr(checks, "materialize_publication_dataset", unsafe_catalog)
    monkeypatch.setattr(checks, "runtime_versions", forbidden)
    monkeypatch.setattr(checks, "authorize", forbidden)
    with pytest.raises(ValueError, match="Unsafe publication catalog"):
        checks.preflight(
            {"profile": "exp01_preflight", "tracking": "enabled", "experiment_id": "EXP01"},
            descriptor,
        )
