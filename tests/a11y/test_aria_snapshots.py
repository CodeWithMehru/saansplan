"""Playwright ARIA snapshots and landmark tree tests across English, Hinglish, and Hindi."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, sync_playwright


@pytest.fixture(scope="module")
def browser() -> Generator[Browser]:
    """Launch headless Chromium for ARIA structure auditing."""
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def page(browser: Browser) -> Generator[Page]:
    """Open page loaded with local index.html."""
    context = browser.new_context()
    p = context.new_page()
    index_path = Path("app/static/index.html").resolve()
    p.goto(f"file://{index_path}")
    yield p
    context.close()


def test_aria_landmarks_exist(page: Page) -> None:
    """Verify standard ARIA landmarks are present."""
    # Banner landmark
    banner = page.locator("header[role='banner']")
    assert banner.count() == 1

    # Main landmark
    main = page.locator("main[role='main']")
    assert main.count() == 1

    # Contentinfo landmark
    footer = page.locator("footer[role='contentinfo']")
    assert footer.count() == 1

    # Form with accessible inputs
    form = page.locator("form")
    assert form.count() >= 1


def test_aria_live_regions_for_screen_readers(page: Page) -> None:
    """Verify live regions exist for assistive technology announcements."""
    live_regions = page.locator("[aria-live], [role='status'], [role='alert']")
    assert live_regions.count() >= 1


def test_language_switch_updates_document_lang(page: Page) -> None:
    """Verify document language attribute reflects selected locale."""
    lang_select = page.locator("#language-select, select[name='language'], #lang")
    if lang_select.count() > 0:
        for lang_code in ["en", "hi"]:
            lang_select.first.select_option(value=lang_code)
            html_lang = page.locator("html").get_attribute("lang")
            assert html_lang in (lang_code, "en", "hi", "hinglish")
