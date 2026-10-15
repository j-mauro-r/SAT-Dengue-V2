#!/usr/bin/env python3
"""Validate local Markdown links for repository-tracked .md files."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")


def tracked_markdown_files(repo_root: Path) -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "AGENTS.md",
            "README.md",
            "docs/**/*.md",
            ".github/pull_request_template.md",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return [repo_root / rel for rel in files]


def normalized_target(source: Path, target: str, repo_root: Path) -> Path | None:
    cleaned = target.strip()
    if not cleaned or cleaned.startswith(SKIP_PREFIXES):
        return None

    cleaned = cleaned.split("#", 1)[0].split("?", 1)[0].strip()
    if not cleaned:
        return None

    cleaned = unquote(cleaned)

    if cleaned.startswith("/"):
        resolved = repo_root / cleaned.lstrip("/")
    else:
        resolved = (source.parent / cleaned).resolve()

    return resolved


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    failures: list[tuple[Path, str]] = []

    for md_file in tracked_markdown_files(repo_root):
        text = md_file.read_text(encoding="utf-8")
        for raw_target in LINK_RE.findall(text):
            target_path = normalized_target(md_file, raw_target, repo_root)
            if target_path is None:
                continue
            if not target_path.exists():
                failures.append((md_file.relative_to(repo_root), raw_target))

    if failures:
        print("Broken markdown links found:")
        for source, target in failures:
            print(f"- {source}: {target}")
        return 1

    print("Markdown link check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
