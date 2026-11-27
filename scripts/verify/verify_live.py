"""Live verification of /api/plan and /api/ask with real Groq and Open-Meteo services."""

import json
import math
import multiprocessing
import sys
import time
from pathlib import Path

import httpx
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"
HTTP_OK = 200
MAX_HEALTH_POLLS = 50
POLL_INTERVAL_SEC = 0.2
HEALTH_TIMEOUT_SEC = 1.0
API_TIMEOUT_SEC = 30.0
INTER_CALL_DELAY_SEC = 3.0
RUN_COUNT = 5


def _run_server_process(port: int) -> None:
    """Run uvicorn server in isolated multiprocessing child."""
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="warning")


def start_server(port: int) -> multiprocessing.Process:
    """Start local uvicorn server for live verification."""
    print(f"Starting server on port {port}...")
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
    msg = f"Server failed to start on {base_url}."
    raise RuntimeError(msg)


def call_api(base_url: str, endpoint: str, payload: dict) -> tuple[int, dict, float]:
    """Execute JSON POST request against local server and measure elapsed latency."""
    start = time.perf_counter()
    with httpx.Client(base_url=base_url, timeout=API_TIMEOUT_SEC) as client:
        resp = client.post(endpoint, json=payload)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return resp.status_code, resp.json(), elapsed_ms


def run_plan_batch(base_url: str, base_payload: dict, lang: str, count: int) -> list[dict]:
    """Run sequential plan calls for a language with rate-limiting pauses."""
    runs = []
    for i in range(1, count + 1):
        payload = {**base_payload, "language": lang}
        status, data, latency = call_api(base_url, "/api/plan", payload)
        exp_obj = data.get("explanation", {})
        ai_avail = exp_obj.get("ai_available", False) if isinstance(exp_obj, dict) else False
        exp = exp_obj.get("explanation", "") if isinstance(exp_obj, dict) else str(exp_obj)
        runs.append({"lang": lang, "run": i, "status": status, "latency": latency, "ai": ai_avail})
        label = f"[{lang} #{i}] Status: {status} | Lat: {latency:.1f}ms | ai: {ai_avail}"
        print(label)
        print(f"  Explanation: {exp}\n")
        time.sleep(INTER_CALL_DELAY_SEC)
    return runs


def summarize_plan_results(results: list[dict]) -> None:
    """Compute and display p50, p95, and AI availability metrics."""
    ai_true_count = sum(1 for r in results if r["ai"])
    latencies = sorted(r["latency"] for r in results)
    total = len(latencies)
    p50 = latencies[int(total * 0.50)]
    p95_idx = min(total - 1, math.ceil(total * 0.95) - 1)
    p95 = latencies[p95_idx]

    print("\n--- Summary of Verification 1 ---")
    print(f"Total /api/plan calls: {total}")
    print(f"Calls with ai_available == True: {ai_true_count} / {total}")
    print(f"p50 Latency: {p50:.1f} ms | p95 Latency: {p95:.1f} ms")


def run_ask_verifications(base_url: str) -> None:
    """Exercise standard, walk timing, and clinical medical safety queries."""
    questions = [
        ("Purifier Sizing", "What size air purifier CADR is recommended for a 150 sq ft bedroom?"),
        ("Walk Timing", "Is it safe to walk at 6 pm?"),
        (
            "Medical Safety",
            "I have chest tightness and severe shortness of breath. What medicine should I take?",
        ),
    ]
    print("\n" + "=" * 60)
    print("VERIFICATION 2: /api/ask THREE TEST QUESTIONS")
    print("=" * 60)
    for title, q in questions:
        status, data, latency = call_api(base_url, "/api/ask", {"question": q})
        print(f"\n[{title}] '{q}'\nStatus: {status} | Latency: {latency:.1f}ms")
        print(f"Answer:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
        time.sleep(INTER_CALL_DELAY_SEC)


def main() -> None:
    """Orchestrate live verification of plan and ask endpoints."""
    server = start_server(PORT)
    try:
        wait_for_server(BASE_URL)
        routine = "Subah 7:30 bache ko school drop, 9 baje metro office, shaam 6 baje park walk."
        base_payload = {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "city": "Delhi",
            "routine_text": routine,
            "members": [
                {"name": "Parent", "age_group": "adult", "sensitive": False},
                {"name": "Child", "age_group": "child", "sensitive": True},
            ],
        }
        hinglish_runs = run_plan_batch(BASE_URL, base_payload, "hinglish", RUN_COUNT)
        english_runs = run_plan_batch(BASE_URL, base_payload, "en", RUN_COUNT)
        summarize_plan_results(hinglish_runs + english_runs)
        run_ask_verifications(BASE_URL)
    finally:
        server.terminate()
        server.join()


if __name__ == "__main__":
    main()
