# SaansPlan Submission Notes

## Changes / updates made in the deployed version

SaansPlan 2.0 upgrades the Indian urban air-quality assistant across all evaluation criteria. Code quality: layered architecture (core, engine, routers, services), Pydantic schemas, modular ES-modules, typed APIs. Security: zero key exposure, SlowAPI rate limiting (30/min), proxy-aware IP, strict CSP, 25-string multi-lingual injection corpus, emergency symptom redirect. Efficiency: BoundedTTLCache (30m TTL, LRU, single-flight), gzip compression, weak ETags, sub-3ms engine calculation, 26.6 KB gzipped bundle. Testing: 124 hermetic tests (91.18% coverage enforcing >=90% gate), property and golden tests, Node.js i18n runner, Playwright E2E. Accessibility: WCAG 2.2 AA compliant (0 Axe violations across EN/Hinglish/HI and populated states), 360px mobile reflow, keyboard skip link, A-/A/A+ scaling. Features: 5-day smog forecast, Cleaner Day routine optimizer with ±25% uncertainty bands, AHAM CADR calculator, emissions/cost estimator, WhatsApp community kit, and grounded Ask SaansPlan.

## Gen AI services utilized and where

Groq Cloud API (`openai/gpt-oss-20b`) is the sole GenAI service, used in 3 touched areas with strict guardrails:
1. Routine Parsing (`POST /api/plan`): Parses free text in English, Hinglish, or Hindi into Pydantic JSON (`Routine`). Demarcated with XML tags; timeouts (>6s) or failures fall back to `default_routine`.
2. Plan Explanation (`POST /api/plan`): Explains engine facts in user language using 12h clock and physical units (µg saved, percent). A Number Guard validates every numeral against engine facts; past-tense wording or raw units trigger deterministic `templated_explanation`.
3. Grounded Q&A Assistant (`POST /api/ask`): Answers questions using engine facts and verified knowledge snippets (`app/kb/knowledge.json`). Computes deterministic CADR (AHAM 2/3 rule) and enforces immediate medical safety refusals for symptoms.

## 90-second demo script

**0:00–0:10 — Intro & Setup:** Open SaansPlan at https://saansplan.onrender.com. Present the urban Indian family winter smog scenario.

**0:10–0:20 — City Search & Coordinates:** Search "Delhi" via geocode autocomplete; review automatic coordinate and timezone binding.

**0:20–0:30 — Household & Persona Presets:** Click "Working Parents & School Children" preset (populates parent + child with sensitive toggle) or enter custom members.

**0:30–0:42 — Hinglish Daily Routine:** Submit Hinglish text ("Subah 7:30 bache ko school drop karte hain, 9 baje metro se office, shaam 6 baje park walk") with LPG cooking and closed windows.

**0:42–0:54 — Plan Results & CPCB Category:** View peak AQI, CPCB category ("Very Poor"), and guard-verified explanation in physical micrograms (µg) saved with 12-hour clock ("6 pm").

**0:54–1:06 — 5-Day Forecast & Your Cleaner Day:** Inspect 5-day smog forecast (midday 11am-3pm airing window, wind stagnation alert <2 m/s) and Cleaner Day schedule optimizer with SVG comparison chart and accessible table.

**1:06–1:18 — Indoor Module & Emissions/Cost:** Calculate AHAM CADR for a 150 sq ft bedroom (100 CFM), review DIY box-fan filter instructions, and compare weekly commute/cooking carbon (kg CO2e) and INR savings across budget tiers.

**1:18–1:25 — Ask SaansPlan:** Ask "What CADR is needed for a 150 sq ft room?" to see grounded synthesis and citation, followed by a symptom query showing the immediate clinical redirect.

**1:25–1:30 — Accessibility, I18n & Graceful Fallback:** Toggle Hindi/Hinglish/English, demonstrate keyboard skip link, A-/A/A+ text scaling, and show "AI explanation unavailable" template fallback when Groq is unreachable.

## LinkedIn post draft

Smog season in North India exposes millions of urban families to hazardous PM2.5 levels. I built SaansPlan for Hack2skill Challenge 6 ("Urban Air Quality Assistant") to turn hourly atmospheric data into clear, practical daily actions.

Live Demo: https://saansplan.onrender.com
GitHub: https://github.com/CodeWithMehru/saansplan

Key Highlights:
• Transparent Physics First: Hourly CPCB National AQI categories, physical inhaled PM2.5 dosage in micrograms (µg) using EPA inhalation rates with transparent ±25% uncertainty bands.
• Your Cleaner Day & 5-Day Forecast: Shifts flexible outdoor tasks to cleaner afternoon windows (11 AM–3 PM) while preserving work/school routines; flags surface wind stagnation (< 2 m/s).
• Indoor IAQ & Cost Engine: AHAM 2/3 room-sizing CADR calculator, verified EPA DIY box-fan filter guide, and weekly carbon (kg CO2e) and INR cost comparisons across budget tiers.
• Grounded GenAI with Groq (openai/gpt-oss-20b): Parses Hinglish/English/Hindi routines; deterministic number guards enforce that the LLM never invents numbers; template fallbacks guarantee zero downtime.
• Production Rigor: WCAG 2.2 AA compliant (0 Axe violations across EN/Hinglish/HI), 360px mobile reflow, strict CSP, sub-3ms engine execution, and 124 tests with 91.18% coverage.

## Character counts

- Changes/updates field: **993 characters** (limit: < 1024 characters).
- Gen AI services field: **837 characters** (limit: < 1024 characters).
- LinkedIn post draft: **1280 characters** (limit: < 1300 characters).
