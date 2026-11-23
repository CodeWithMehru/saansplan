"""Verify /api/plan returns deterministic template fallback when GROQ_API_KEY is fake."""

import os
import subprocess
import sys
import time
import httpx
from pathlib import Path

PORT = 8091
BASE_URL = f"http://127.0.0.1:{PORT}"

def main():
    project_root = Path(__file__).resolve().parent.parent
    project_python = project_root / ".venv" / "bin" / "python"
    py_exec = str(project_python) if project_python.exists() else sys.executable

    env = os.environ.copy()
    env["GROQ_API_KEY"] = "gsk_fake_invalid_key_for_testing_fallback_12345"

    print(f"Starting server with fake GROQ_API_KEY on port {PORT}...")
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
            "warning",
        ],
        cwd=project_root,
        env=env,
    )

    try:
        # Wait for health
        ready = False
        with httpx.Client(base_url=BASE_URL, timeout=1.0) as client:
            for _ in range(30):
                time.sleep(0.3)
                try:
                    r = client.get("/health")
                    if r.status_code == 200:
                        ready = True
                        break
                except Exception:
                    pass

        if not ready:
            raise RuntimeError("Server failed to start with fake key.")

        payload = {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "city": "Delhi",
            "routine_text": "Morning 7am walk, 9am metro office, 6pm park.",
            "members": [
                {"name": "Adult", "age_group": "adult", "sensitive": False}
            ],
            "language": "en"
        }

        print("Calling /api/plan with fake GROQ_API_KEY...")
        with httpx.Client(base_url=BASE_URL, timeout=20.0) as client:
            start = time.perf_counter()
            resp = client.post("/api/plan", json=payload)
            elapsed = (time.perf_counter() - start) * 1000

        print(f"Status Code: {resp.status_code}")
        print(f"Response Latency: {elapsed:.1f}ms")
        data = resp.json()
        explanation = data.get("explanation", {})
        ai_available = explanation.get("ai_available")
        text = explanation.get("explanation")
        print(f"ai_available: {ai_available}")
        print(f"Explanation text:\n{text}")

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert ai_available is False, f"Expected ai_available=False, got {ai_available}"
        assert text, "Expected non-empty explanation"
        print("\nSUCCESS: Plan returned template fallback gracefully when GROQ_API_KEY is fake!")

    finally:
        server.terminate()
        server.wait(timeout=3)

if __name__ == "__main__":
    main()
