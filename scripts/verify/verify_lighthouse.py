"""Run Lighthouse accessibility audit against local SaansPlan server."""

import json
import multiprocessing
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PORT = 8092
BASE_URL = f"http://127.0.0.1:{PORT}"
HTTP_OK = 200
MAX_HEALTH_POLLS = 50
POLL_INTERVAL_SEC = 0.2
HEALTH_TIMEOUT_SEC = 1.0
LIGHTHOUSE_TIMEOUT_SEC = 120


def _run_server_process(port: int) -> None:
    """Run uvicorn server in isolated process for Lighthouse."""
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="warning")


def start_server(port: int) -> multiprocessing.Process:
    """Start local uvicorn server for Lighthouse audit."""
    print(f"Starting server for Lighthouse on port {port}...")
    proc = multiprocessing.Process(target=_run_server_process, args=(port,))
    proc.start()
    return proc


def wait_for_server(base_url: str) -> None:
    """Poll health endpoint until server is responsive."""
    with httpx.Client(base_url=base_url, timeout=HEALTH_TIMEOUT_SEC) as client:
        for _ in range(MAX_HEALTH_POLLS):
            time.sleep(POLL_INTERVAL_SEC)
            try:
                resp = client.get("/health")
                if resp.status_code == HTTP_OK:
                    return
            except (httpx.HTTPError, ConnectionRefusedError, TimeoutError):
                continue
    msg = f"Server failed to start on {base_url} for Lighthouse."
    raise RuntimeError(msg)


def run_lighthouse_audit(base_url: str, report_path: Path) -> int:
    """Invoke Lighthouse CLI with headless Chrome flags."""
    lh_bin = Path(tempfile.gettempdir()) / "lh" / "node_modules" / ".bin" / "lighthouse"
    cmd = [str(lh_bin)] if lh_bin.exists() else ["npx", "--yes", "lighthouse@12.8.2"]
    cmd.extend(
        [
            f"{base_url}/",
            "--only-categories=accessibility",
            "--output=json",
            f"--output-path={report_path}",
            "--chrome-flags=--headless --no-sandbox --disable-gpu",
            "--quiet",
        ]
    )
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=LIGHTHOUSE_TIMEOUT_SEC,
        check=False,
    )
    print(f"Lighthouse exited with code: {res.returncode}")
    if res.returncode != 0:
        print("Lighthouse stderr:\n", res.stderr)
    return res.returncode


def parse_lighthouse_report(report_path: Path) -> tuple[float, list[str]]:
    """Parse output report and collect accessibility score and failures."""
    data = json.loads(report_path.read_text(encoding="utf-8"))
    score = float(data["categories"]["accessibility"]["score"]) * 100.0
    audits = data.get("audits", {})
    failing: list[str] = [
        audit.get("title", audit_id)
        for audit_id, audit in audits.items()
        if audit.get("score") is not None and audit["score"] < 1
    ]
    return score, failing


def print_audit_results(score: float, failing_audits: list[str]) -> None:
    """Print formatted Lighthouse score and audit messages."""
    print("\n" + "=" * 42)
    print(f"LIGHTHOUSE ACCESSIBILITY SCORE: {score:.0f} / 100")
    print("=" * 42)
    if failing_audits:
        print("\nFailing or warning audits:")
        for title in failing_audits:
            print(f"- {title}")
    else:
        print("Zero failing accessibility audits!")


def main() -> None:
    """Orchestrate server lifecycle and Lighthouse accessibility audit."""
    server = start_server(PORT)
    report_path = Path(tempfile.gettempdir()) / "lighthouse_accessibility.json"
    try:
        wait_for_server(BASE_URL)
        print("Server ready. Running Lighthouse...")
        run_lighthouse_audit(BASE_URL, report_path)
        score, failing = parse_lighthouse_report(report_path)
        print_audit_results(score, failing)
    finally:
        server.terminate()
        server.join()


if __name__ == "__main__":
    main()
