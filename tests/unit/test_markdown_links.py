"""Working-tree link validation must distinguish deletions from broken targets."""

import importlib.util
import subprocess
from pathlib import Path


def test_deleted_new_and_broken_markdown(tmp_path: Path) -> None:
    """Inspect new docs, ignore removed sources, and still reject dangling links."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "check_markdown_links.py"
    spec = importlib.util.spec_from_file_location("markdown_checker", script)
    assert spec is not None and spec.loader is not None
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)

    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    docs = tmp_path / "docs"
    docs.mkdir()
    removed = docs / "removed.md"
    removed.write_text("# Historical entry\n", encoding="utf-8")
    subprocess.run(["git", "add", "docs/removed.md"], cwd=tmp_path, check=True)
    removed.unlink()
    current = docs / "new.md"
    current.write_text("[Target](target.md)\n", encoding="utf-8")

    assert checker.tracked_markdown_files(tmp_path) == [current]
    # main resolves the repository from its script location; isolate it in this fixture.
    checker.__file__ = str(tmp_path / "scripts" / "check_markdown_links.py")
    assert checker.main() == 1
    (docs / "target.md").write_text("# Target\n", encoding="utf-8")
    assert checker.main() == 0
