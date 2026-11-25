"""Run Lighthouse accessibility audit against local SaansPlan server."""

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PORT = 8092
BASE_URL = f"http://127.0.0.1:{PORT}"


def main():
    project_root = Path(__file__).resolve().parent.parent
    project_python = project_root / ".venv" / "bin" / "python"
    py_exec = str(project_python) if project_python.exists() else sys.executable

    print(f"Starting server for Lighthouse on port {PORT}...")
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
    )

    try:
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
            raise RuntimeError("Server failed to start for Lighthouse.")

        print("Server ready. Running Lighthouse...")
        report_path = "/tmp/lighthouse_accessibility.json"
        lh_bin = "/tmp/lh/node_modules/.bin/lighthouse"
        cmd = [lh_bin] if Path(lh_bin).exists() else ["npx", "--yes", "lighthouse@12.8.2"]

        cmd.extend(
            [
                f"{BASE_URL}/",
                "--only-categories=accessibility",
                "--output=json",
                f"--output-path={report_path}",
                "--chrome-flags=--headless --no-sandbox --disable-gpu",
                "--quiet",
            ]
        )

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
        print(f"Lighthouse exited with code: {res.returncode}")
        if res.returncode != 0:
            print("Lighthouse stderr:\n", res.stderr)

        with open(report_path, encoding="utf-8") as f:
            data = json.load(f)

        score = data["categories"]["accessibility"]["score"] * 100
        print("\n==========================================")
        print(f"LIGHTHOUSE ACCESSIBILITY SCORE: {score:.0f} / 100")
        print("==========================================")

        # Print audit results
        audits = data.get("audits", {})
        failing_audits = []
        for audit_id, audit in audits.items():
            if audit.get("score") is not None and audit["score"] < 1:
                failing_audits.append((audit.get("title", audit_id), audit.get("description", "")))

        if failing_audits:
            print("\nFailing or warning audits:")
            for title, _desc in failing_audits:
                print(f"- {title}")
        else:
            print("Zero failing accessibility audits!")

    finally:
        server.terminate()
        server.wait(timeout=3)


if __name__ == "__main__":
    main()
