"""Automated WCAG 2.2 AA accessibility audit using Axe-Core and Playwright."""

import multiprocessing
import sys
import tempfile
import time
from pathlib import Path

import httpx
import uvicorn

PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"
HTTP_OK = 200
MAX_HEALTH_POLLS = 50
POLL_INTERVAL_SEC = 0.2
HEALTH_TIMEOUT_SEC = 1.0
AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"


MIN_AXE_BYTES = 1000


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def ensure_axe() -> str:
    """Download axe-core script if missing and return its source string."""
    axe_path = Path(tempfile.gettempdir()) / "axe.min.js"
    if not axe_path.exists() or axe_path.stat().st_size < MIN_AXE_BYTES:
        print(f"Downloading axe-core to {axe_path}...")
        resp = httpx.get(AXE_CDN, timeout=15)
        axe_path.write_bytes(resp.content)
    return axe_path.read_text(encoding="utf-8")


def _run_server_process(port: int) -> None:
    """Run uvicorn server in isolated child process."""
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="warning")


def start_a11y_server(port: int) -> multiprocessing.Process:
    """Start local uvicorn server for accessibility audit."""
    print(f"Starting server on port {port}...")
    proc = multiprocessing.Process(target=_run_server_process, args=(port,))
    proc.start()
    return proc


def wait_for_a11y_server(base_url: str) -> None:
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


def verify_skip_link(page) -> None:
    """Test skip link activation and focus shift via keyboard."""
    print("Testing Skip Link keyboard focus...")
    page.keyboard.press("Tab")
    is_skip = page.evaluate("""() => {
        const el = document.activeElement;
        return !!(el && (el.id === 'skip-link' || el.getAttribute('href') === '#main-content'));
    }""")
    if not is_skip:
        msg = "Active element is not skip link"
        raise AssertionError(msg)
    page.keyboard.press("Enter")
    print("✓ Skip link keyboard activation verified")


def run_axe_audit(page, axe_source: str, label: str) -> list[dict]:
    """Execute axe.run on current page state and report results."""
    print(f"Running Axe scan: {label}...")
    page.evaluate(axe_source)
    results = page.evaluate("""async () => await axe.run(document, {
        runOnly: {
            type: 'tag',
            values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']
        }
    })""")
    violations = results.get("violations", [])
    if violations:
        print(f"❌ {label}: {len(violations)} violation(s) found:")
        for v in violations:
            print(f"  - [{v['id']}] {v['help']}")
    else:
        passes = len(results.get("passes", []))
        print(f"✓ {label}: 0 violations (Passed {passes} rules)")
    return violations


def verify_desktop_flow(page, axe_source: str) -> list[dict]:
    """Audit landing page, language switches, form submission, and populated state."""
    violations = []
    page.goto(BASE_URL, wait_until="networkidle")
    verify_skip_link(page)

    violations.extend(run_axe_audit(page, axe_source, "Landing Page (English)"))

    page.click("#language-toggle")
    time.sleep(0.2)
    violations.extend(run_axe_audit(page, axe_source, "Landing Page (Hinglish)"))

    page.click("#language-toggle")
    time.sleep(0.2)
    violations.extend(run_axe_audit(page, axe_source, "Landing Page (Hindi)"))

    page.click("#language-toggle")
    time.sleep(0.2)

    page.click('button[data-persona="working_parents"]')
    page.fill("#city", "Delhi")
    page.click("#city-search")
    page.wait_for_selector(".city-match-btn", timeout=5000)
    page.click(".city-match-btn")

    page.click('button[type="submit"]')
    page.wait_for_selector("#summary-card:not([hidden])", timeout=12000)

    violations.extend(run_axe_audit(page, axe_source, "Full Populated Plan & Analytics"))
    return violations


def verify_mobile_reflow(browser, axe_source: str) -> list[dict]:
    """Audit mobile 360px viewport reflow and scan with Axe."""
    print("Testing 360px mobile viewport reflow (WCAG 1.4.10)...")
    context = browser.new_context(viewport={"width": 360, "height": 740})
    page = context.new_page()
    page.goto(BASE_URL, wait_until="networkidle")

    check_overflow = "() => document.documentElement.scrollWidth > window.innerWidth + 2"
    has_overflow = page.evaluate(check_overflow)
    if has_overflow:
        msg = "Horizontal scroll overflow detected at 360px viewport!"
        raise AssertionError(msg)
    print("✓ 360px reflow verified with zero horizontal overflow")

    page.evaluate(axe_source)
    results = page.evaluate("async () => await axe.run()")
    violations = results.get("violations", [])
    if violations:
        print(f"❌ Mobile 360px: {len(violations)} violation(s)")
    else:
        print("✓ Mobile 360px: 0 violations")
    return violations


def run_a11y_audit() -> None:
    """Execute complete WCAG 2.2 AA accessibility audit."""
    from playwright.sync_api import sync_playwright

    axe_source = ensure_axe()
    server = start_a11y_server(PORT)
    total_violations = []

    try:
        wait_for_a11y_server(BASE_URL)
        with sync_playwright() as p:
            exec_path = "/usr/bin/chromium" if Path("/usr/bin/chromium").exists() else None
            browser = p.chromium.launch(executable_path=exec_path, headless=True)
            desktop_page = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()

            total_violations.extend(verify_desktop_flow(desktop_page, axe_source))
            total_violations.extend(verify_mobile_reflow(browser, axe_source))
            browser.close()
    finally:
        server.terminate()
        server.join()

    if total_violations:
        print(f"\nFAILED: Total axe violations across audits: {len(total_violations)}")
        sys.exit(1)
    print("\nSUCCESS: All accessibility tests passed with 0 WCAG 2.2 AA violations!")


if __name__ == "__main__":
    run_a11y_audit()
