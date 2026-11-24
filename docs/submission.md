# SaansPlan Submission Notes

## Changes / updates made in the deployed version

SaansPlan upgrades the Indian air-quality assistant across all evaluation criteria. Code quality: layered architecture, thin routers, modular guards, domain schemas, componentized ES modules, Radon CC Rank A (3.24), 100% docstrings, zero files >250 lines. Security: 415 Content-Type check, RFC 9116 security.txt, SHA-pinned CI actions, 48-vector injection corpus, CORP same-origin, SlowAPI rate limits (30/min). Efficiency: BoundedTTLCache (30m TTL, LRU), gzip, 1.73ms engine plan calculation, 32.7 KB gzipped bundle (<60 KB). Testing: 178 hermetic tests (96.07% coverage, >=95% gate), fault injection, Hypothesis property invariants, 7 characterization snapshots, Node.js i18n runner. Accessibility: WCAG 2.2 AA (0 Axe violations on 56 rules), Lighthouse 100/100, Reading Comfort panel (High Contrast, Text Spacing WCAG 1.4.12), standalone /accessibility page. Features: 5-day smog forecast, Cleaner Day optimizer (±25% range), CADR sizing, emissions/cost engine, WhatsApp kit, and grounded Q&A.

## Gen AI services utilized and where

Groq Cloud API (openai/gpt-oss-20b) is the sole GenAI service, applied strictly in 3 bounded areas with deterministic safety guards:
1. Routine Parsing (POST /api/plan): Parses free-text routines in English, Hinglish, or Hindi into validated Pydantic JSON (Routine). Input sanitized with XML tags; network timeouts (>6s) or schema parsing errors fall back gracefully to default_routine.
2. Plan Explanation (POST /api/plan): Explains engine facts in user language using 12-hour clock times and physical inhaled units (µg saved, percent). A deterministic Number Guard validates every numeral against engine facts; ungrounded numbers or past-tense claims fall back to templated_explanation.
3. Grounded Q&A Assistant (POST /api/ask): Answers queries using deterministic engine facts and verified knowledge base snippets. Automatically calculates AHAM 2/3 CADR sizing and immediately redirects acute respiratory symptoms to emergency medical care.

## 90-second demo script

**0:00–0:10 — Intro & Setup:** Open SaansPlan at https://saansplan.onrender.com. Present the urban Indian family winter smog scenario.

**0:10–0:20 — City Search & Coordinates:** Search "Delhi" via geocode autocomplete; review automatic coordinate and timezone binding.

**0:20–0:30 — Household & Persona Presets:** Click "Working Parents & School Children" preset (populates parent + child with sensitive toggle) or enter custom members.

**0:30–0:42 — Hinglish Daily Routine:** Submit Hinglish text ("Subah 7:30 bache ko school drop karte hain, 9 baje metro se office, shaam 6 baje park walk") with LPG cooking and closed windows.

**0:42–0:54 — Plan Results & CPCB Category:** View peak AQI, CPCB category ("Very Poor"), and guard-verified explanation in physical micrograms (µg) saved with 12-hour clock ("6 pm").

**0:54–1:06 — 5-Day Forecast & Your Cleaner Day:** Inspect 5-day smog forecast (midday 11am-3pm airing window, wind stagnation alert <2 m/s) and Cleaner Day schedule optimizer with SVG comparison chart and accessible table.

**1:06–1:18 — Indoor Module & Emissions/Cost:** Calculate AHAM CADR for a 150 sq ft bedroom (100 CFM), review DIY box-fan filter instructions, and compare weekly commute/cooking carbon (kg CO2e) and INR savings across budget tiers.

**1:18–1:25 — Ask SaansPlan:** Ask "What CADR is needed for a 150 sq ft room?" to see grounded synthesis and citation, followed by a symptom query showing the immediate clinical redirect.

**1:25–1:30 — Accessibility, I18n & Graceful Fallback:** Toggle Hindi/Hinglish/English, demonstrate keyboard skip link, Reading Comfort high contrast / text spacing controls, and show "AI explanation unavailable" template fallback when Groq is unreachable.

## LinkedIn post draft

Smog season in North India exposes millions of urban families to hazardous PM2.5 levels. I built SaansPlan for Hack2skill Challenge 6 ("Urban Air Quality Assistant") to turn hourly atmospheric data into clear, practical daily actions.

Live Demo: https://saansplan.onrender.com
GitHub: https://github.com/CodeWithMehru/saansplan

Key Highlights:
• Transparent Physics First: Hourly CPCB National AQI categories, physical inhaled PM2.5 dosage in micrograms (µg) using EPA inhalation rates with transparent ±25% uncertainty bands.
• Your Cleaner Day & 5-Day Forecast: Shifts flexible outdoor tasks to cleaner afternoon windows (11 AM–3 PM) while preserving work/school routines; flags surface wind stagnation (< 2 m/s).
• Indoor IAQ & Cost Engine: AHAM 2/3 room-sizing CADR calculator, verified EPA DIY box-fan filter guide, and weekly carbon (kg CO2e) and INR cost comparisons across budget tiers.
• Grounded GenAI with Groq (openai/gpt-oss-20b): Parses Hinglish/English/Hindi routines; deterministic number guards enforce that the LLM never invents numbers; template fallbacks guarantee zero downtime.
• Production Rigor: WCAG 2.2 AA compliant (0 Axe violations across EN/Hinglish/HI), Lighthouse 100/100, strict CSP, sub-2ms engine execution, and 178 tests with 96.07% coverage.

## Character counts

- Changes/updates field: **996 characters** (limit: < 1024 characters).
- Gen AI services field: **944 characters** (limit: < 1024 characters).
- LinkedIn post draft: **1279 characters** (limit: < 1300 characters).
