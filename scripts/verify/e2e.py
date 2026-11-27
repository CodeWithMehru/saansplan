"""End-to-end user flow test across English, Hinglish, and Hindi."""

import multiprocessing
import sys
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
MIN_ROUTINE_LEN = 10
MIN_ANSWER_LEN = 15


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _run_server_process(port: int) -> None:
    """Run uvicorn server in isolated multiprocessing child."""
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="warning")


def start_e2e_server(port: int) -> multiprocessing.Process:
    """Start local uvicorn server for Playwright journey."""
    print(f"Starting server on port {port}...")
    proc = multiprocessing.Process(target=_run_server_process, args=(port,))
    proc.start()
    return proc


def wait_for_e2e_server(base_url: str) -> None:
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
    msg = f"Server failed to start on {base_url} for E2E."
    raise RuntimeError(msg)


def verify_plan_flow(page) -> None:
    """Verify city search, persona prefill, plan submission, and swap labels."""
    print(f"Navigating to {BASE_URL}...")
    page.goto(BASE_URL, wait_until="networkidle")
    if "SaansPlan" not in page.title():
        msg = f"Unexpected title: {page.title()}"
        raise AssertionError(msg)

    page.fill("#city", "Delhi")
    page.click("#city-search")
    page.wait_for_selector(".city-match-btn", timeout=5000)
    page.click(".city-match-btn")

    page.click('button[data-persona="working_parents"]')
    routine_val = page.input_value("#routine-text")
    if len(routine_val) <= MIN_ROUTINE_LEN:
        msg = f"Routine text too short: {routine_val}"
        raise AssertionError(msg)

    page.click('button[type="submit"]')
    page.wait_for_selector("#summary-card:not([hidden])", timeout=12000)

    swaps_text = page.inner_text("#swaps")
    if "swap_purifier" in swaps_text or "swap_windows" in swaps_text or "swap_shift" in swaps_text:
        msg = f"Raw swap identifiers leaked: {swaps_text}"
        raise AssertionError(msg)
    print("✓ Plan generation and clean swap labels verified")


def verify_features_and_i18n(page) -> None:
    """Verify all dashboard sections and language toggling."""
    sections = [
        "#forecast-section",
        "#cleaner-day-section",
        "#emissions-section",
        "#indoor-module-section",
        ".cleaner-chart",
        ".comparison-table",
    ]
    for sel in sections:
        if not page.is_visible(sel):
            msg = f"Dashboard section not visible: {sel}"
            raise AssertionError(msg)

    page.click("#language-toggle")
    time.sleep(0.3)
    if page.get_attribute("html", "lang") != "hi-Latn":
        msg = "Failed to switch to Hinglish"
        raise AssertionError(msg)

    page.click("#language-toggle")
    time.sleep(0.3)
    if page.get_attribute("html", "lang") != "hi":
        msg = "Failed to switch to Hindi"
        raise AssertionError(msg)
    if "SaansPlan" not in page.inner_text("#page-title"):
        msg = "Brand missing from Hindi title"
        raise AssertionError(msg)
    print("✓ Dashboard sections and multilingual toggling verified")


def verify_ask_flow(page) -> None:
    """Verify grounded Ask assistant answers queries."""
    page.fill("#ask-question", "What size air purifier is needed for bedroom?")
    page.click("#ask-button")
    page.wait_for_selector("#ask-answer:not(:empty)", timeout=6000)
    answer = page.inner_text("#ask-answer")
    if len(answer) <= MIN_ANSWER_LEN:
        msg = f"Answer text too short: {answer}"
        raise AssertionError(msg)
    print("✓ Grounded Ask assistant verified")


def run_e2e() -> None:
    """Execute complete end-to-end user journey in headless Chromium."""
    from playwright.sync_api import sync_playwright

    server = start_e2e_server(PORT)
    try:
        wait_for_e2e_server(BASE_URL)
        with sync_playwright() as p:
            exec_path = "/usr/bin/chromium" if Path("/usr/bin/chromium").exists() else None
            browser = p.chromium.launch(executable_path=exec_path, headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()

            verify_plan_flow(page)
            verify_features_and_i18n(page)
            verify_ask_flow(page)

            browser.close()
    finally:
        server.terminate()
        server.join()


if __name__ == "__main__":
    run_e2e()
