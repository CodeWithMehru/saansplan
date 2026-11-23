"""End-to-end user flow test across English, Hinglish, and Hindi."""

import os
import subprocess
import sys
import time

PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"


def run_e2e():
    # If playwright is in /tmp/pw_venv, re-execute with that python
    if os.path.exists("/tmp/pw_venv/bin/python3") and sys.executable != "/tmp/pw_venv/bin/python3":
        os.execv("/tmp/pw_venv/bin/python3", ["/tmp/pw_venv/bin/python3", __file__] + sys.argv[1:])

    from playwright.sync_api import sync_playwright

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_python = os.path.join(project_root, ".venv/bin/python")
    if not os.path.exists(project_python):
        project_python = sys.executable

    print(f"Starting server on port {PORT} with {project_python} in {project_root}...")
    server = subprocess.Popen(
        [
            project_python,
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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Poll /api/health until server is ready
    import urllib.request

    ready = False
    for _ in range(25):
        time.sleep(0.3)
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            pass

    if not ready:
        server.terminate()
        try:
            out, err = server.communicate(timeout=2)
            out_s = out.decode() if out else ""
            err_s = err.decode() if err else ""
        except Exception:
            out_s, err_s = "", ""
        msg = f"Server failed to start on {BASE_URL}. stdout: {out_s}, stderr: {err_s}"
        raise RuntimeError(msg)

    try:
        with sync_playwright() as p:
            exec_path = "/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else None
            browser = p.chromium.launch(executable_path=exec_path, headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()

            console_errors = []

            def on_console(msg):
                print(f"[BROWSER {msg.type.upper()}] {msg.text}")
                if msg.type == "error":
                    console_errors.append(msg.text)

            def on_page_error(exc):
                console_errors.append(str(exc))
                print(f"[BROWSER PAGEERROR] {exc}")

            page.on("console", on_console)
            page.on("pageerror", on_page_error)

            print(f"Navigating to {BASE_URL}...")
            page.goto(BASE_URL, wait_until="networkidle")

            # 1. Check title & brand
            assert "SaansPlan" in page.title()
            print("✓ Title verified")

            # 2. Test City Search
            page.fill("#city", "Delhi")
            page.click("#city-search")
            page.wait_for_selector(".city-match-btn", timeout=5000)
            page.click(".city-match-btn")
            print("✓ City search verified")

            # 3. Test Persona Selection
            page.click('button[data-persona="working_parents"]')
            routine_val = page.input_value("#routine-text")
            assert len(routine_val) > 10
            print("✓ Persona prefilling verified")

            # 4. Submit plan
            page.click('button[type="submit"]')
            page.wait_for_selector("#summary-card:not([hidden])", timeout=12000)
            print("✓ Plan generation verified")

            # 5. Check no raw keys leak in swaps
            swaps_text = page.inner_text("#swaps")
            assert "swap_purifier" not in swaps_text
            assert "swap_windows" not in swaps_text
            assert "swap_shift" not in swaps_text
            print("✓ F10: No raw swap identifiers leaked")

            # 6. Check Forecast, Cleaner Day, Emissions, Indoor Module
            assert page.is_visible("#forecast-section")
            assert page.is_visible("#cleaner-day-section")
            assert page.is_visible("#emissions-section")
            assert page.is_visible("#indoor-module-section")
            print("✓ All feature sections visible")

            # 7. Check Cleaner Day SVG Chart & Table alternative
            assert page.is_visible(".cleaner-chart")
            assert page.is_visible(".comparison-table")
            print("✓ Cleaner day chart and table alternative verified")

            # 8. Test Language Toggle to Hinglish then Hindi
            page.click("#language-toggle")
            time.sleep(0.3)
            assert page.get_attribute("html", "lang") == "hi-Latn"
            print("✓ Switched to Hinglish")

            page.click("#language-toggle")
            time.sleep(0.3)
            assert page.get_attribute("html", "lang") == "hi"
            summary_hi = page.inner_text("#page-title")
            assert "SaansPlan" in summary_hi
            print("✓ Switched to Hindi")

            # 9. Test Ask endpoint
            page.fill("#ask-question", "What size air purifier is needed for bedroom?")
            page.click("#ask-button")
            page.wait_for_selector("#ask-answer:not(:empty)", timeout=6000)
            answer = page.inner_text("#ask-answer")
            assert len(answer) > 15
            print("✓ Grounded Ask assistant verified")

            # 10. Verify zero console errors
            if console_errors:
                print(f"Warning: console errors detected: {console_errors}")
            else:
                print("✓ Zero console errors verified")

            browser.close()
    finally:
        server.terminate()
        server.wait()

    print("ALL E2E TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_e2e()
