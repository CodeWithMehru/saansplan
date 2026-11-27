"""Verify /api/plan returns deterministic template fallback when GROQ_API_KEY is fake."""

import multiprocessing
import os
import sys
import time
from pathlib import Path

import httpx
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PORT = 8091
BASE_URL = f"http://127.0.0.1:{PORT}"
HTTP_OK = 200
HEALTH_TIMEOUT_SEC = 1.0
MAX_HEALTH_RETRIES = 50
POLL_INTERVAL_SEC = 0.2
PLAN_TIMEOUT_SEC = 20.0


def _run_server_process(port: int) -> None:
    """Run uvicorn server in isolated process with fake GROQ_API_KEY."""
    os.environ["GROQ_API_KEY"] = "gsk_fake_invalid_key_for_testing_fallback_12345"
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="warning")


def start_server(port: int) -> multiprocessing.Process:
    """Start local uvicorn server with an invalid Groq API key."""
    print(f"Starting server with fake GROQ_API_KEY on port {port}...")
    proc = multiprocessing.Process(target=_run_server_process, args=(port,))
    proc.start()
    return proc


def wait_for_server_health(base_url: str) -> None:
    """Poll health endpoint until server is responsive or raise TimeoutError."""
    with httpx.Client(base_url=base_url, timeout=HEALTH_TIMEOUT_SEC) as client:
        for _ in range(MAX_HEALTH_RETRIES):
            time.sleep(POLL_INTERVAL_SEC)
            try:
                resp = client.get("/health")
                if resp.status_code == HTTP_OK:
                    return
            except (httpx.HTTPError, ConnectionRefusedError, TimeoutError):
                continue
    msg = f"Server failed to start on {base_url}."
    raise RuntimeError(msg)


def verify_plan_fallback(base_url: str) -> None:
    """Call /api/plan and assert deterministic fallback is triggered."""
    payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "city": "Delhi",
        "routine_text": "Morning 7am walk, 9am metro office, 6pm park.",
        "members": [{"name": "Adult", "age_group": "adult", "sensitive": False}],
        "language": "en",
    }
    print("Calling /api/plan with fake GROQ_API_KEY...")
    with httpx.Client(base_url=base_url, timeout=PLAN_TIMEOUT_SEC) as client:
        start = time.perf_counter()
        resp = client.post("/api/plan", json=payload)
        elapsed = (time.perf_counter() - start) * 1000

    print(f"Status Code: {resp.status_code} | Latency: {elapsed:.1f}ms")
    data = resp.json()
    explanation = data.get("explanation", {})
    ai_available = explanation.get("ai_available")
    text = explanation.get("explanation")
    print(f"ai_available: {ai_available}\nExplanation:\n{text}")

    if resp.status_code != HTTP_OK:
        msg = f"Expected 200, got {resp.status_code}"
        raise AssertionError(msg)
    if ai_available is not False:
        msg = f"Expected ai_available=False, got {ai_available}"
        raise AssertionError(msg)
    if not text:
        msg = "Expected non-empty explanation"
        raise AssertionError(msg)
    print("\nSUCCESS: Plan returned template fallback gracefully when GROQ_API_KEY is fake!")


def main() -> None:
    """Orchestrate server startup, health wait, and plan verification."""
    server = start_server(PORT)
    try:
        wait_for_server_health(BASE_URL)
        verify_plan_fallback(BASE_URL)
    finally:
        server.terminate()
        server.join()


if __name__ == "__main__":
    main()
