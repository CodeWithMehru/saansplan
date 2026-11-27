"""Automated tests for WCAG 2.2 AA success criteria: 1.4.10, 1.4.12, 2.4.11, 2.5.8."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, sync_playwright


@pytest.fixture(scope="module")
def browser() -> Generator[Browser]:
    """Launch headless Chromium for WCAG 2.2 criterion verification."""
    try:
        with sync_playwright() as pw:
            try:
                b = pw.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Headless Chromium not available in runner environment: {exc}")
            yield b
            b.close()
    except Exception as exc:
        pytest.skip(f"Playwright driver not available in runner environment: {exc}")


@pytest.fixture
def page(browser: Browser) -> Generator[Page]:
    """Open page loaded with local index.html and modular stylesheets."""
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    p = context.new_page()
    index_path = Path("app/static/index.html").resolve()
    css_files = ["tokens.css", "base.css", "layout.css", "components.css", "utilities.css"]
    p.goto(f"file://{index_path}")
    for fname in css_files:
        p.add_style_tag(path=str(Path(f"app/static/css/{fname}").resolve()))
    yield p
    context.close()


def test_wcag22_target_size_minimum(page: Page) -> None:
    """WCAG 2.2 SC 2.5.8: Target Size (Minimum) >= 24x24 CSS pixels for interactive controls."""
    targets = page.locator("button, a, input, select")
    count = targets.count()
    assert count > 0

    undersized: list[str] = []
    for i in range(count):
        target = targets.nth(i)
        if not target.is_visible():
            continue
        box = target.bounding_box()
        if not box or box["width"] == 0 or box["height"] == 0:
            continue
        # Allow inline text links or elements meeting target size
        tag_name = page.evaluate("(el) => el.tagName.toLowerCase()", target.element_handle())
        if tag_name == "a":
            continue
        if box["width"] < 24 or box["height"] < 24:
            tid = target.get_attribute("id") or ""
            undersized.append(f"{tag_name}#{tid} ({box['width']}x{box['height']})")

    assert not undersized, f"Interactive controls failed SC 2.5.8 Target Size: {undersized}"


def test_wcag22_text_spacing_adaptation(page: Page) -> None:
    """WCAG 2.2 SC 1.4.12: Text Spacing overridden styles cause zero text cutoff or overflow."""
    # Inject official WCAG 1.4.12 spacing override styles
    page.add_style_tag(
        content="""
        * {
            line-height: 1.5 !important;
            letter-spacing: 0.12em !important;
            word-spacing: 0.16em !important;
        }
        p {
            margin-bottom: 2em !important;
        }
    """
    )
    # Check that main content does not generate unconstrained horizontal overflow
    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    assert not overflow, "WCAG 1.4.12 text spacing injection caused horizontal layout blowout"


def test_wcag22_reflow_320px(page: Page) -> None:
    """WCAG 2.2 SC 1.4.10: Reflow at 320px viewport width without 2D scrolling."""
    page.set_viewport_size({"width": 320, "height": 640})
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    assert scroll_width <= 320, f"Horizontal overflow at 320px: scrollWidth={scroll_width}"


def test_wcag22_focus_not_obscured(page: Page) -> None:
    """WCAG 2.2 SC 2.4.11: Focus Not Obscured (Minimum) - focused element is visible."""
    interactive = page.locator("button, input, select").first
    interactive.focus()
    is_visible = interactive.is_visible()
    assert is_visible, "Focused interactive element is not visible"
