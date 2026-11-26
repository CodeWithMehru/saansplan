"""Automated WCAG 2.2 AA accessibility audit using Axe-Core and Playwright."""

import os
import subprocess
import sys
import time
import urllib.request

PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"
AXE_PATH = "/tmp/axe.min.js"
AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"


def ensure_axe():
    if not os.path.exists(AXE_PATH) or os.path.getsize(AXE_PATH) < 1000:
        print(f"Downloading axe-core to {AXE_PATH}...")
        urllib.request.urlretrieve(AXE_CDN, AXE_PATH)
    with open(AXE_PATH, encoding="utf-8") as f:
        return f.read()


def run_a11y_audit():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_venv_py = os.path.join(project_root, ".venv", "bin", "python3")
    if os.path.exists(local_venv_py) and sys.executable != local_venv_py:
        os.execv(local_venv_py, [local_venv_py, __file__] + sys.argv[1:])
    elif (
        os.path.exists("/tmp/pw_venv/bin/python3") and sys.executable != "/tmp/pw_venv/bin/python3"
    ):
        os.execv("/tmp/pw_venv/bin/python3", ["/tmp/pw_venv/bin/python3", __file__] + sys.argv[1:])

    from playwright.sync_api import sync_playwright

    axe_source = ensure_axe()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_python = os.path.join(project_root, ".venv/bin/python")
    if not os.path.exists(project_python):
        project_python = sys.executable

    print(f"Starting server on port {PORT}...")
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

    ready = False
    for _ in range(25):
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
        try:
            out, err = server.communicate(timeout=2)
            out_s, err_s = out.decode() if out else "", err.decode() if err else ""
        except Exception:
            out_s, err_s = "", ""
        server.terminate()
        msg = f"Server failed to start on {BASE_URL}. stdout: {out_s}, stderr: {err_s}"
        raise RuntimeError(msg)

    total_violations = []

    try:
        with sync_playwright() as p:
            exec_path = "/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else None
            browser = p.chromium.launch(executable_path=exec_path, headless=True)

            # Test 1: Desktop Full Audit (English, Hinglish, Hindi)
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()

            print(f"Loading {BASE_URL} for initial a11y audit...")
            page.goto(BASE_URL, wait_until="networkidle")

            # Test 0: Keyboard Skip Link on initial fresh load
            print("Testing Skip Link keyboard focus...")
            page.keyboard.press("Tab")
            is_skip = page.evaluate("""() => {
                const el = document.activeElement;
                if (!el) return false;
                return (
                    el.id === 'skip-link' ||
                    el.classList.contains('skip-link') ||
                    el.getAttribute('href') === '#main-content'
                );
            }""")
            tag = page.evaluate("document.activeElement ? document.activeElement.tagName : ''")
            assert is_skip, f"Active element is not skip link: {tag}"
            page.keyboard.press("Enter")
            focused_main = page.evaluate("document.activeElement.id")
            assert focused_main == "main-content" or tag in ["MAIN", "DIV"]
            print("✓ Skip link keyboard activation verified")

            def run_axe(label):
                print(f"Running Axe scan: {label}...")
                page.evaluate(axe_source)
                results = page.evaluate("""
                    async () => {
                        return await axe.run(document, {
                            runOnly: {
                                type: 'tag',
                                values: [
                                    'wcag2a', 'wcag2aa', 'wcag21a',
                                    'wcag21aa', 'wcag22aa', 'best-practice'
                                ]
                            }
                        });
                    }
                """)
                violations = results.get("violations", [])
                if violations:
                    print(f"❌ {label}: {len(violations)} violation(s) found:")
                    for v in violations:
                        print(f"  - [{v['id']}] {v['help']} (impact: {v['impact']})")
                        for node in v.get("nodes", []):
                            print(f"    Target: {node.get('target')}")
                            print(f"    Summary: {node.get('failureSummary')}")
                else:
                    passes = len(results.get("passes", []))
                    print(f"✓ {label}: 0 violations (Passed {passes} rules)")
                return violations

            # Scan initial state
            v1 = run_axe("Landing Page (English)")
            total_violations.extend(v1)

            # Switch language to Hinglish
            page.click("#language-toggle")
            time.sleep(0.2)
            v2 = run_axe("Landing Page (Hinglish)")
            total_violations.extend(v2)

            # Switch language to Hindi
            page.click("#language-toggle")
            time.sleep(0.2)
            v3 = run_axe("Landing Page (Hindi)")
            total_violations.extend(v3)

            # Switch back to English and fill & submit form
            page.click("#language-toggle")
            time.sleep(0.2)

            # Use persona preset
            page.click('button[data-persona="working_parents"]')
            page.fill("#city", "Delhi")
            page.click("#city-search")
            page.wait_for_selector(".city-match-btn", timeout=5000)
            page.click(".city-match-btn")

            # Submit form to get full populated UI
            page.click('button[type="submit"]')
            page.wait_for_selector("#summary-card:not([hidden])", timeout=12000)

            # Scan populated results page
            v4 = run_axe("Full Populated Plan & Analytics")
            total_violations.extend(v4)

            # Test 3: Text Scale A-, A, A+
            print("Testing Text Size controls...")
            page.click("#text-larger")
            saved_scale = page.evaluate("localStorage.getItem('saansplan-text-scale')")
            assert saved_scale == "110", f"Unexpected saved scale: {saved_scale}"
            print("✓ Text scale control verified")

            # Test 4: Mobile 360px Reflow Audit (No horizontal overflow)
            print("Testing 360px mobile viewport reflow (WCAG 1.4.10)...")
            mobile_context = browser.new_context(viewport={"width": 360, "height": 740})
            mobile_page = mobile_context.new_page()
            mobile_page.goto(BASE_URL, wait_until="networkidle")

            has_overflow = mobile_page.evaluate("""
                () => document.documentElement.scrollWidth > window.innerWidth + 2
            """)
            assert not has_overflow, "Horizontal scroll overflow detected at 360px viewport!"
            print("✓ 360px reflow verified with zero horizontal overflow")

            # Scan mobile page with axe
            mobile_page.evaluate(axe_source)
            mobile_results = mobile_page.evaluate("async () => await axe.run()")
            v_mobile = mobile_results.get("violations", [])
            if v_mobile:
                print(f"❌ Mobile 360px: {len(v_mobile)} violation(s)")
                total_violations.extend(v_mobile)
            else:
                print("✓ Mobile 360px: 0 violations")

            browser.close()
    finally:
        server.terminate()
        server.wait()

    if total_violations:
        print(f"\nFAILED: Total axe violations across audits: {len(total_violations)}")
        sys.exit(1)
    else:
        print("\nSUCCESS: All accessibility tests passed with 0 WCAG 2.2 AA violations!")


if __name__ == "__main__":
    run_a11y_audit()
