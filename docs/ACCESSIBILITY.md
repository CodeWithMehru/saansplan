# Accessibility

## Target

WCAG 2.2 AA, keyboard operation, text alternatives, visible focus and 200% reflow.

## Implemented

- Skip link and semantic landmarks in `app/static/index.html`
- Visible labels and fieldsets for form controls
- `aria-live` loading, result and error regions
- English, Hinglish and Hindi locale parity test
- Text/table alternative for hourly data with caption and scoped headers
- text-size controls saved in localStorage
- prefers-reduced-motion and prefers-color-scheme styles
- no untrusted `innerHTML`; DOM text is set through `textContent`

## Automated evidence

- Static markup audit: `tests/a11y/test_static_markup.py`
- i18n key parity: `app/static/tests/i18n.test.js`
- Browser flow and CSP console capture: Playwright evidence in final report

## Manual status

Automated Chromium/axe status must be recorded before final submission. NVDA/JAWS/Orca hardware screen-reader testing was not claimable by this agent unless explicitly run. Keyboard-only and 360px reflow were exercised through Playwright in prior proof; a manual product check is still recommended before submission.
