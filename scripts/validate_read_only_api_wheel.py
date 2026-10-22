"""Validate the Stage 7 wheel from an isolated installation.

This script is intentionally separate from the unit suite because it creates a
temporary virtual environment and installs a built distribution. It must be run
from the repository environment with one wheel path as its argument.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

EXPECTED_PACKAGE_FILES = {
    "scripts/read_only_api/__init__.py",
    "scripts/read_only_api/api.py",
    "scripts/read_only_api/errors.py",
    "scripts/read_only_api/loader.py",
    "scripts/read_only_api/repository.py",
    "scripts/read_only_api/schemas.py",
    "scripts/read_only_api/service.py",
    "scripts/read_only_api/fixtures/dashboard_meta.json",
    "scripts/read_only_api/fixtures/dashboard_tolima.json",
}

PROBE = r"""from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from scripts.read_only_api import DEMONSTRATIVE_RESULT_PATHS, create_app


async def request(params: dict[str, str]) -> tuple[int, dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    request_sent = False

    async def receive() -> dict[str, Any]:
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/dashboard",
        "raw_path": b"/api/dashboard",
        "query_string": urlencode(params).encode("ascii"),
        "root_path": "",
        "headers": [],
        "client": ("127.0.0.1", 1),
        "server": ("testserver", 80),
    }
    await create_app()(scope, receive, send)
    status = next(
        message["status"]
        for message in messages
        if message["type"] == "http.response.start"
    )
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return status, json.loads(body)


package_root = Path(__import__("scripts.read_only_api", fromlist=["x"]).__file__).resolve().parent
source_checkout = Path(os.environ["SAT_DENGUE_SOURCE_CHECKOUT"]).resolve()
assert "site-packages" in package_root.parts, package_root
assert Path.cwd() not in package_root.parents
assert source_checkout not in package_root.parents
assert source_checkout not in {Path(entry).resolve() for entry in sys.path if entry}

before = {
    str(path): (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
    for path in DEMONSTRATIVE_RESULT_PATHS.values()
}

tolima_status, tolima = asyncio.run(request({"department_code": "73", "period": "2026-09"}))
meta_status, meta = asyncio.run(request({"department_code": "50", "period": "2026-12"}))
missing_status, missing = asyncio.run(request({"department_code": "73", "period": "2026-12"}))
invalid_status, invalid = asyncio.run(request({"department_code": "76", "period": "2026-09"}))

assert tolima_status == 200
assert meta_status == 200
assert missing_status == 404
assert missing["error_code"] == "DASHBOARD_DATA_NOT_FOUND"
assert invalid_status == 400
assert invalid["error_code"] == "INVALID_DEPARTMENT_CODE"

for body in (tolima, meta):
    assert body["governance"]["governance_status"] == "NOT_APPROVED"
    assert body["governance"]["champion_status"] == "NOT_SELECTED"
    roles = {
        result["model_role"]
        for municipality in body["municipalities"]
        for result in municipality["results"]
        if result["model_role"] is not None
    }
    assert roles == {"PROVISIONAL_CANDIDATE"}

after = {
    str(path): (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
    for path in DEMONSTRATIVE_RESULT_PATHS.values()
}
assert after == before

for forbidden in (
    "kedro",
    "scripts.training_preparation",
    "scripts.model_training",
    "scripts.model_evaluation",
):
    assert not any(
        name == forbidden or name.startswith(f"{forbidden}.") for name in sys.modules
    )

print(json.dumps({
    "import_root": str(package_root),
    "statuses": {
        "tolima": tolima_status,
        "meta": meta_status,
        "missing": missing_status,
        "invalid": invalid_status,
    },
    "governance": {
        "G5": "NOT_APPROVED",
        "Champion": "NOT_SELECTED",
        "model_role": "PROVISIONAL_CANDIDATE",
    },
    "fixtures_unchanged": True,
    "scientific_runtime_imports": False,
}, sort_keys=True))
"""


def _inspect_wheel(wheel: Path) -> list[str]:
    """Return wheel members after enforcing the bounded package contents.

    Args:
        wheel: Built wheel to inspect.

    Returns:
        Sorted archive member names.

    Raises:
        AssertionError: If required files are absent or excluded surfaces exist.
    """
    with ZipFile(wheel) as archive:
        names = sorted(archive.namelist())

    payload = {name for name in names if ".dist-info/" not in name}
    assert payload == EXPECTED_PACKAGE_FILES
    return names


def validate_wheel(wheel: Path) -> dict[str, object]:
    """Install and probe a wheel from outside the source checkout.

    Args:
        wheel: Wheel produced from the current Stage 7 tree.

    Returns:
        Inspectable validation evidence.

    Raises:
        FileNotFoundError: If ``wheel`` does not exist.
        subprocess.CalledProcessError: If environment creation, installation, or
            the isolated probe fails.
    """
    wheel = wheel.resolve(strict=True)
    members = _inspect_wheel(wheel)
    source_checkout = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="sat-dengue-stage7-smoke-") as temporary:
        root = Path(temporary)
        environment = root / "venv"
        workdir = root / "outside-checkout"
        workdir.mkdir()
        probe = workdir / "probe.py"
        probe.write_text(PROBE, encoding="utf-8")

        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
        python = environment / "bin" / "python"
        subprocess.run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", str(wheel)],
            check=True,
            cwd=workdir,
        )
        completed = subprocess.run(
            [str(python), "-I", str(probe)],
            check=True,
            cwd=workdir,
            capture_output=True,
            text=True,
            env={"SAT_DENGUE_SOURCE_CHECKOUT": str(source_checkout)},
        )

    return {
        "wheel": wheel.name,
        "wheel_members": members,
        "probe": json.loads(completed.stdout),
    }


def main() -> int:
    """Run the validator and print its JSON evidence."""
    if len(sys.argv) != 2:
        print("usage: validate_read_only_api_wheel.py PATH_TO_WHEEL", file=sys.stderr)
        return 2
    evidence = validate_wheel(Path(sys.argv[1]))
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
