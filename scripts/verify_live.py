"""Live verification of /api/plan and /api/ask with real Groq and Open-Meteo services."""

import json
import math
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"


def start_server():
    project_root = Path(__file__).resolve().parent.parent
    project_python = project_root / ".venv" / "bin" / "python"
    py_exec = str(project_python) if project_python.exists() else sys.executable

    print(f"Starting server on port {PORT} with {py_exec}...")
    server = subprocess.Popen(
        [
            py_exec,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
            "--log-level",
            "info",
        ],
        cwd=project_root,
    )

    ready = False
    for _ in range(30):
        time.sleep(0.3)
        try:
            with urllib.request.urlopen(f"{BASE_URL}/health", timeout=1) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            pass

    if not ready:
        server.terminate()
        server.wait(timeout=2)
        raise RuntimeError("Server failed to start.")

    return server


def call_api(endpoint: str, payload: dict) -> tuple[int, dict, float]:
    import httpx

    start = time.perf_counter()
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        resp = client.post(endpoint, json=payload)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return resp.status_code, resp.json(), elapsed_ms


def main():
    server = start_server()
    try:
        hinglish_routine = "Subah 7:30 bache ko school drop karte hain, 9 baje metro se office, shaam 6 baje park walk."
        base_payload = {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "city": "Delhi",
            "routine_text": hinglish_routine,
            "members": [
                {"name": "Parent", "age_group": "adult", "sensitive": False},
                {"name": "Child", "age_group": "child", "sensitive": True},
            ],
        }

        print("\n" + "=" * 60)
        print("VERIFICATION 1: 5 HINGLISH CALLS & 5 ENGLISH CALLS TO /api/plan")
        print("=" * 60)

        results = []

        # 5 Hinglish calls
        for i in range(1, 6):
            payload = {**base_payload, "language": "hinglish"}
            status, data, latency = call_api("/api/plan", payload)
            exp_obj = data.get("explanation", {})
            ai_avail = exp_obj.get("ai_available", False) if isinstance(exp_obj, dict) else False
            exp = exp_obj.get("explanation", "") if isinstance(exp_obj, dict) else str(exp_obj)
            results.append(
                {
                    "lang": "hinglish",
                    "run": i,
                    "status": status,
                    "latency": latency,
                    "ai": ai_avail,
                    "exp": exp,
                }
            )
            print(
                f"[Hinglish Run {i}] Status: {status} | Latency: {latency:.1f}ms | ai_available: {ai_avail}"
            )
            print(f"  Explanation: {exp[:100]}...")
            time.sleep(1.2)

        # 5 English calls
        for i in range(1, 6):
            payload = {**base_payload, "language": "en"}
            status, data, latency = call_api("/api/plan", payload)
            exp_obj = data.get("explanation", {})
            ai_avail = exp_obj.get("ai_available", False) if isinstance(exp_obj, dict) else False
            exp = exp_obj.get("explanation", "") if isinstance(exp_obj, dict) else str(exp_obj)
            results.append(
                {
                    "lang": "en",
                    "run": i,
                    "status": status,
                    "latency": latency,
                    "ai": ai_avail,
                    "exp": exp,
                }
            )
            print(
                f"[English Run {i}] Status: {status} | Latency: {latency:.1f}ms | ai_available: {ai_avail}"
            )
            print(f"  Explanation: {exp[:100]}...")
            time.sleep(1.2)

        ai_true_count = sum(1 for r in results if r["ai"])
        latencies = sorted(r["latency"] for r in results)
        n = len(latencies)
        p50 = latencies[int(n * 0.50)]
        # Nearest rank or ceiling index for p95
        p95_idx = min(n - 1, math.ceil(n * 0.95) - 1)
        p95 = latencies[p95_idx]

        print("\n--- Summary of Verification 1 ---")
        print(f"Total /api/plan calls: {len(results)}")
        print(f"Calls with ai_available == True: {ai_true_count} / {len(results)}")
        print(f"p50 Latency: {p50:.1f} ms")
        print(f"p95 Latency: {p95:.1f} ms")
        print(f"All Latencies (sorted): {[round(x, 1) for x in latencies]}")

        print("\n" + "=" * 60)
        print("VERIFICATION 2: /api/ask NORMAL QUESTION & SYMPTOM QUESTION")
        print("=" * 60)

        # Normal question
        q1 = "What size air purifier CADR is recommended for a 150 sq ft bedroom?"
        status1, data1, lat1 = call_api("/api/ask", {"question": q1})
        print(f"\n[Normal Question] '{q1}'")
        print(f"Status: {status1} | Latency: {lat1:.1f}ms")
        print(f"Answer:\n{json.dumps(data1, indent=2, ensure_ascii=False)}")

        # Symptom question
        q2 = "I have chest tightness, severe shortness of breath, and wheezing from Delhi smog. What medicine or syrup should I take?"
        status2, data2, lat2 = call_api("/api/ask", {"question": q2})
        print(f"\n[Symptom Question] '{q2}'")
        print(f"Status: {status2} | Latency: {lat2:.1f}ms")
        print(f"Answer:\n{json.dumps(data2, indent=2, ensure_ascii=False)}")

    finally:
        server.terminate()
        server.wait()


if __name__ == "__main__":
    main()
