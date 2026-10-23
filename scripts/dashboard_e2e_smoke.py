"""Run the real Stage 7 API and dashboard proxy for a bounded E2E smoke."""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_ROOT = REPO_ROOT / "apps" / "dashboard"
TIMEOUT_SECONDS = 30.0


def _free_port() -> int:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return int(server.getsockname()[1])


def _wait_for_tcp(port: int, process: subprocess.Popen[bytes], label: str) -> None:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"{label} exited before becoming ready")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"{label} did not become ready within {TIMEOUT_SECONDS:.0f} seconds")


def _wait_for_dashboard(url: str, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("dashboard exited before serving its initial page")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200 and b"SAT-Dengue" in response.read():
                    return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.2)
    raise RuntimeError(
        f"dashboard did not serve its initial page within {TIMEOUT_SECONDS:.0f} seconds"
    )


def _request(url: str) -> tuple[int, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def _assert_dashboard_payload(payload: dict[str, Any], expected_count: int) -> None:
    assert len(payload["municipalities"]) == expected_count
    assert payload["governance"]["governance_gate"] == "G5"
    assert payload["governance"]["governance_status"] == "NOT_APPROVED"
    assert payload["governance"]["champion_status"] == "NOT_SELECTED"

    municipalities = payload["municipalities"]
    results = [result for municipality in municipalities for result in municipality["results"]]
    assert any(result["availability_status"] == "AVAILABLE" for result in results)
    assert any(result["availability_status"] != "AVAILABLE" for result in results)
    assert all(
        result["model_role"] == "PROVISIONAL_CANDIDATE"
        for result in results
        if result["availability_status"] == "AVAILABLE"
    )
    assert all("endemic_channel_series" in municipality for municipality in municipalities)
    assert any(municipality["endemic_channel_series"] for municipality in municipalities)


def _stop(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def main() -> int:
    bun = os.environ.get("BUN_BIN") or shutil.which("bun")
    local_bun = Path("/tmp/bun-runtime/bun-linux-x64/bun")
    if not bun and local_bun.is_file():
        bun = str(local_bun)
    if not bun:
        raise RuntimeError("Bun is required; install it or set BUN_BIN")

    api_port = _free_port()
    dashboard_port = _free_port()
    api_process: subprocess.Popen[bytes] | None = None
    dashboard_process: subprocess.Popen[bytes] | None = None

    with tempfile.TemporaryDirectory(prefix="sat-dengue-e2e-") as temp_dir:
        api_log_path = Path(temp_dir) / "api.log"
        dashboard_log_path = Path(temp_dir) / "dashboard.log"
        try:
            with api_log_path.open("wb") as api_log, dashboard_log_path.open("wb") as dashboard_log:
                api_process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "--factory",
                        "scripts.read_only_api.api:create_app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(api_port),
                    ],
                    cwd=REPO_ROOT,
                    stdout=api_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                _wait_for_tcp(api_port, api_process, "Stage 7 API")

                dashboard_env = os.environ.copy()
                dashboard_env["API_PROXY_TARGET"] = f"http://127.0.0.1:{api_port}"
                dashboard_process = subprocess.Popen(
                    [
                        bun,
                        "run",
                        "dev",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(dashboard_port),
                        "--strictPort",
                    ],
                    cwd=DASHBOARD_ROOT,
                    env=dashboard_env,
                    stdout=dashboard_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                _wait_for_tcp(dashboard_port, dashboard_process, "dashboard")

                dashboard_origin = f"http://127.0.0.1:{dashboard_port}"
                _wait_for_dashboard(dashboard_origin, dashboard_process)
                for department, period, expected_count in (
                    ("73", "2026-09", 47),
                    ("50", "2026-12", 29),
                ):
                    status, payload = _request(
                        f"{dashboard_origin}/api/dashboard"
                        f"?department_code={department}&period={period}"
                    )
                    assert status == 200
                    _assert_dashboard_payload(payload, expected_count)

                missing_status, missing_payload = _request(
                    f"{dashboard_origin}/api/dashboard?department_code=73&period=2026-12"
                )
                assert missing_status == 404
                assert missing_payload["error_code"] == "DASHBOARD_DATA_NOT_FOUND"
        except Exception:
            for label, path in (("API", api_log_path), ("dashboard", dashboard_log_path)):
                if path.exists():
                    print(f"--- {label} log ---", file=sys.stderr)
                    print(path.read_text(errors="replace"), file=sys.stderr)
            raise
        finally:
            _stop(dashboard_process)
            _stop(api_process)

    print(
        "E2E smoke PASS: dashboard-origin proxy served Tolima 47, Meta 29, "
        "availability/governance/series invariants, and contracted 404"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
