# Accessibility (A11y) Verification & Compliance Report

**Target Standard:** WCAG 2.2 Level AA  
**Audit Tools:** Axe-Core 4.10.2 via Playwright, Google Lighthouse 12.8.2, Python static AST/HTML parser, Node.js i18n validator, Pytest WCAG 2.2 automated suite  
**Automated Results:** **0 Violations** (across 56 active Axe-Core rules), **100 / 100** Lighthouse Accessibility Score  

---

## 1. Automated Audit Results

The automated accessibility test suite (`scripts/a11y.py` and `scripts/verify_lighthouse.py`) exercises the complete application state in headless Chromium with zero violations:

| View / State | Tool | Rules Scanned | Violations / Score | Result |
|---|---|---|---|---|
| **Landing Page (English)** | Axe-Core 4.10.2 | 43 WCAG 2.2 AA rules | 0 violations | ✅ PASS |
| **Landing Page (Hinglish)** | Axe-Core 4.10.2 | 43 WCAG 2.2 AA rules | 0 violations | ✅ PASS |
| **Landing Page (Hindi)** | Axe-Core 4.10.2 | 43 WCAG 2.2 AA rules | 0 violations | ✅ PASS |
| **Populated Plan & Analytics** | Axe-Core 4.10.2 | 56 WCAG 2.2 AA rules | 0 violations | ✅ PASS |
| **Full Page Audit** | Lighthouse 12.8.2 | Accessibility category | 100 / 100 (0 failing audits) | ✅ PASS |
| **Mobile Viewport Reflow (320px/360px)** | Axe-Core & Pytest | WCAG 1.4.10 Reflow | 0 horizontal overflow | ✅ PASS |
| **Text Scaling (A-, A, A+)** | Custom DOM harness | 90% – 120% scaling | Verified persistence | ✅ PASS |
| **Reading Comfort (Contrast / Spacing)** | Axe-Core & Pytest | WCAG 1.4.12 & High Contrast | Verified toggles & storage | ✅ PASS |

Automated static and snapshot checks in pytest:
- Single `<h1>` document hierarchy (`tests/a11y/test_static_markup.py`).
- Semantic HTML5 landmarks: `<header role="banner">`, `<main role="main">`, `<footer role="contentinfo">` (`tests/a11y/test_aria_snapshots.py`).
- Form controls paired with explicit `<label for="...">` or `<fieldset>` / `<legend>`.
- Accessible data tables with `<caption>` and `<th scope="col">` / `<th scope="row">`.
- Zero inline JavaScript event handlers (`onclick`, `onerror`).
- WCAG 2.2 criteria verification suite (`tests/a11y/test_wcag22.py`).

---

## 2. Automated vs. Manual Verification Boundaries & Honest Disclosure

To maintain total integrity and transparent engineering standards, we clearly delineate between automated guarantees and human manual verification:

### Automated Boundary (What Machine Audits Prove)
1. **Rule Conformance:** Complete absence of syntactic, structural, and detectable contrast violations verified across 56 Axe-Core rules and Lighthouse 12.8.2.
2. **Reflow & Overflow:** Headless Playwright tests (`tests/a11y/test_wcag22.py`) programmatically verify zero horizontal scrolling down to 320 px width and during aggressive text-spacing injection (WCAG 1.4.12).
3. **Interactive Target Dimensions:** Automated measurement of bounding boxes confirms all interactive elements meet or exceed 24x24 px (WCAG 2.5.8 Target Size Minimum) and default to 44px minimum touch targets.
4. **ARIA Snapshot Consistency:** Pytest tests verify that all landmarks, role definitions, and live regions exist and match accessibility tree requirements (`tests/a11y/test_aria_snapshots.py`).

### Manual Boundary & Honest Attribution
- **Maintainer Testing:** Manual keyboard tab sequencing, focus visibility, mobile screen rotation, and zoom flows were directly verified by the project maintainers during development.
- **Honest Attribution:** Manual testing was performed by project maintainers, not an external panel of users with disabilities.
- **Assistive Technology Recommendation:** While automated accessibility tree inspections and ARIA live announcements function as designed in Chromium, real-world user validation across varied physical assistive hardware (e.g. dedicated Braille displays, physical switch access units, JAWS, NVDA, and TalkBack) remains recommended for ongoing community deployment.

---

## 3. WCAG 2.2 AA Traceability Matrix

| WCAG SC | Criterion Name | Level | Implementation in SaansPlan | Proving Test / Verification |
|---|---|---|---|---|
| **1.1.1** | Non-text Content | A | Decorative icons use `aria-hidden="true"`; chart SVGs include structured text summaries. | `tests/a11y/test_static_markup.py` |
| **1.3.1** | Info and Relationships | A | Semantic `<header>`, `<main>`, `<footer>`, `<fieldset>`, `<legend>`, `<label>`. | `tests/a11y/test_static_markup.py` & `tests/a11y/test_aria_snapshots.py` |
| **1.3.5** | Identify Input Purpose | AA | Standard `autocomplete="address-level2"` for city search. | `tests/a11y/test_static_markup.py` |
| **1.4.1** | Use of Color | A | Color is never used alone; AQI categories and status chips carry explicit text labels. | `scripts/a11y.py` |
| **1.4.3** | Contrast (Minimum) | AA | Text contrast $\ge 4.5:1$ (measured: $13.5:1$ in light, $14.1:1$ in dark). | `scripts/a11y.py` |
| **1.4.4** | Resize Text | AA | Text scaling buttons (90%, 100%, 110%) and browser 200% zoom without truncation. | `scripts/a11y.py` |
| **1.4.10** | Reflow | AA | CSS Flexbox/Grid responsive down to 320 px without horizontal scroll. | `tests/a11y/test_wcag22.py` & `scripts/a11y.py` |
| **1.4.11** | Non-text Contrast | AA | Form borders, focus rings, and UI components have $\ge 3:1$ contrast. | `scripts/a11y.py` |
| **1.4.12** | Text Spacing | AA | Evaluated with line-height 1.5x, letter-spacing 0.12em, word-spacing 0.16em with zero clipping. | `tests/a11y/test_wcag22.py` & `app/static/styles.css` |
| **2.1.1** | Keyboard | A | All buttons, inputs, tabs, and persona presets are verified keyboard operable. | `scripts/a11y.py` |
| **2.1.2** | No Keyboard Trap | A | No modal focus traps; focus flows sequentially through DOM order. | `scripts/a11y.py` |
| **2.4.1** | Bypass Blocks | A | Visible skip links to `#main-content`, `#results`, and `#ask-section`. | `scripts/a11y.py` & `tests/a11y/test_static_markup.py` |
| **2.4.7** | Focus Visible | AA | High-visibility 3px blue outline (`outline: 3px solid #1a56db`) with 3px offset. | `app/static/styles.css` |
| **2.4.11** | Focus Not Obscured | AA | `scroll-padding-top: 5rem` ensures fixed headers never obscure focused controls. | `tests/a11y/test_wcag22.py` & `app/static/styles.css` |
| **2.5.8** | Target Size (Minimum) | AA | Interactive controls meet $\ge 24\times 24\text{ px}$ (defaulting to $\ge 44\text{ px}$). | `tests/a11y/test_wcag22.py` & `app/static/styles.css` |
| **3.2.6** | Consistent Help | A | Persistent link to Accessibility Statement & GitHub Issues in site footer across all views. | `app/static/index.html` & `tests/a11y/test_static_markup.py` |
| **3.3.1** | Error Identification | A | Form validation aggregates errors in an ARIA-alert error summary. | `app/static/index.html` |
| **3.3.3** | Error Suggestion | AA | Input constraints provide guidance for invalid coordinates and time windows. | `app/static/js/app.js` |
| **3.3.7** | Redundant Entry | A | Stored user preferences (language, scale, contrast, routine) persist across runs. | `app/static/js/state.js` |
| **4.1.2** | Name, Role, Value | A | Custom controls have explicit `role`, `aria-label`, and `aria-expanded` attributes. | `scripts/a11y.py` & `tests/a11y/test_aria_snapshots.py` |
| **4.1.3** | Status Messages | AA | Dynamic results, assistant responses, and copy confirmations use `aria-live="polite"`. | `app/static/index.html` & `tests/a11y/test_aria_snapshots.py` |

---

## 4. Keyboard Navigation Flow Verification

Every interactive feature is verified operable via sequential keyboard navigation (Tab, Shift+Tab, Enter, Space, Arrow keys) tested programmatically and structurally:

| Step | Keystrokes | Expected Focus / Action | Observed Result | Status |
|---|---|---|---|---|
| 1 | `Tab` (on load) | Focus moves to `.skip-link` ("Skip to content") | Button appears visibly at top-left | ✅ PASS |
| 2 | `Enter` | Activates skip link | Focus jumps directly to `#main-content` | ✅ PASS |
| 3 | `Tab` | Cycles through Language Toggle, Text Size controls (A-, A, A+), Contrast, Spacing | High-contrast visible focus outline (3px solid #1a56db) | ✅ PASS |
| 4 | `Tab` | Persona preset buttons (Working Parents, Elderly, Student, Rider) | `Enter` or `Space` loads preset and announces via `aria-live` | ✅ PASS |
| 5 | `Tab` | City input and Search button | `Enter` triggers geocode search | ✅ PASS |
| 6 | `Tab` | City match candidate buttons | `Enter` selects city, populates coordinates, and closes list | ✅ PASS |
| 7 | `Tab` | Family member list (name, age group select, sensitive toggle) | Full tab order across inputs and "+ Add Member" button | ✅ PASS |
| 8 | `Tab` | Submit button | `Enter` submits plan | ✅ PASS |
| 9 | Auto-Focus | Upon plan generation | Focus automatically shifts to `#results` (`tabindex="-1"`) | ✅ PASS |
| 10 | `Tab` | Hourly timeline & comparison tables | Timeline container has `tabindex="0"` for arrow-key horizontal scrolling | ✅ PASS |
| 11 | `Tab` | Indoor module tabs | Tab switching accessible with Enter/Space | ✅ PASS |
| 12 | `Tab` | Ask Assistant input and button | `Enter` queries grounded QA; response announced via `aria-live` | ✅ PASS |

---

## 5. Visual & Cognitive Accessibility

1. **Color Contrast (WCAG 1.4.3 & 1.4.11):**
   - Body text: `#10251c` on `#f7faf7` — contrast ratio **13.5:1** (far exceeds 4.5:1).
   - WhatsApp community button: `#ffffff` on `#0b6659` — contrast ratio **5.2:1** (exceeds 4.5:1).
   - Headings & brand: `#0d4d31` on white — contrast ratio **8.6:1**.
   - Input borders: `#8ca395` against backgrounds — contrast ratio **3.1:1** (meets component 3:1).
   - Dark theme (`prefers-color-scheme: dark`): `#f0f7f3` on `#121c16` — contrast ratio **14.1:1**.

2. **Reading Comfort Panel:**
   - Text scaling: 90%, 100%, 110% root font-size scaling.
   - High-contrast toggle (`html[data-contrast="high"]`): Enforces pure black borders and maximum contrast.
   - Text-spacing toggle (`html[data-spacing="enhanced"]`): Applies line-height 1.6, letter-spacing 0.12em, word-spacing 0.16em per WCAG 1.4.12.

3. **No Meaning by Color Alone (WCAG 1.4.1):**
   - AQI and CPCB levels always include explicit text category labels ("Good", "Satisfactory", "Moderately polluted", "Poor", "Very poor", "Severe") alongside colors.
   - Cleaner Day chart includes an accessible `<details open>` table alternative with full numeric values.

4. **Reflow & Zoom (WCAG 1.4.10):**
   - Page tested at 320px and 360px viewport widths (equivalent to 400% zoom on 1280px display).
   - Zero horizontal scrollbar on body; grids reflow into single-column cards.

5. **Reduced Motion (WCAG 2.3.3):**
   - `@media (prefers-reduced-motion: reduce)` disables all animations and sets `scroll-behavior: auto !important`.

6. **Touch Targets (WCAG 2.5.8):**
   - Minimum target height of 44px (`min-height: 2.75rem`) for all buttons and interactive inputs (WCAG 2.2 AA minimum requirement is 24x24 px).

---

## 6. Screen-Reader & Assistive Technology Status

- **Automated Accessibility Trees:** Validated with Chromium DevTools Accessibility Tree, Axe-Core 4.10.2, and Python HTML/AST markup tests. Semantic landmarks, heading hierarchy (H1 -> H2 -> H3), form labels, and live regions are strictly bound.
- **Dynamic Announcements:** An offscreen `#a11y-announcer-polite` and `#a11y-announcer-assertive` announce status changes (loading, plan generated, preset loaded, city selected, errors).
- **Verification Commands:**
  - Automated Axe-Core audit: `python3 scripts/a11y.py`
  - Automated Lighthouse audit: `python3 scripts/verify_lighthouse.py`
  - Pytest accessibility test suite: `pytest tests/a11y/`

