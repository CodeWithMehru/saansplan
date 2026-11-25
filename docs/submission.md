# SaansPlan Submission Notes

## Changes / updates made in the deployed version

SaansPlan upgrades the Indian air-quality assistant across all evaluation criteria. Code quality: layered architecture, thin routers, modular guards, domain schemas, componentized ES modules, Radon CC Rank A (3.22 avg), docstrings (187/187), zero files >250 lines. Security: 415 Content-Type check, RFC 9116 security.txt, SHA-pinned CI actions, 48-vector injection corpus, CORP same-origin, SlowAPI rate limits (30/min). Efficiency: BoundedTTLCache (30m TTL, LRU), gzip, 1.52ms engine plan calculation, 32.70 KB gzipped bundle. Testing: 178 hermetic tests (96.07% coverage, >=95% gate), fault injection, Hypothesis invariants, 7 characterization snapshots, Node.js i18n runner. Accessibility: WCAG 2.2 AA (0 Axe violations on 56 rules), Lighthouse Accessibility 100/100, Reading Comfort panel (High Contrast, Text Spacing WCAG 1.4.12), standalone /accessibility page. Features: 5-day smog forecast, Cleaner Day optimizer (±25% range), CADR sizing, emissions/cost engine, WhatsApp kit, and grounded Q&A.

## Gen AI services utilized and where

Groq Cloud API (openai/gpt-oss-20b) is the sole GenAI service, applied strictly in 3 bounded areas with deterministic safety guards:
1. Routine Parsing (POST /api/plan): Parses free-text routines in English, Hinglish, or Hindi into validated Pydantic JSON (Routine). Input sanitized with XML tags; network timeouts (>6s) or schema parsing errors fall back gracefully to default_routine.
2. Plan Explanation (POST /api/plan): Explains engine facts in user language using 12-hour clock times and physical inhaled units (µg saved, percent). A deterministic Number Guard validates every numeral against engine facts; ungrounded numbers or past-tense claims fall back to templated_explanation.
3. Grounded Q&A Assistant (POST /api/ask): Verified via outbound call inspection to make exactly 1 outbound Groq request for general air quality/purifier queries (grounded in KB facts). Symptom queries make 0 outbound Groq requests: deterministically intercepted by check_safety for immediate medical redirection.

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

Live: https://saansplan.onrender.com
Code: https://github.com/CodeWithMehru/saansplan

Key Highlights:
• Transparent Physics: Hourly CPCB AQI categories, physical inhaled PM2.5 dosage (µg) using EPA inhalation rates with ±25% uncertainty bands.
• Your Cleaner Day: Shifts flexible outdoor tasks to cleaner afternoon windows (11 AM–3 PM); flags wind stagnation (< 2 m/s).
• Indoor IAQ & Cost: AHAM 2/3 room CADR calculator, EPA DIY box-fan filter guide, and weekly carbon (kg CO2e) and INR cost comparisons.
• Grounded GenAI (Groq gpt-oss-20b): Parses Hinglish/English/Hindi routines; deterministic number guard stops hallucinations; template fallback on failure. Outbound dispatch verified: 1 call for general queries, 0 calls for clinical symptom redirects.
• Production Rigor: WCAG 2.2 AA (0 Axe violations), Lighthouse Accessibility 100, strict CSP, sub-2ms engine execution, and 178 tests with 96.07% coverage.

#Hack2skill #CleanAir #AIForGood

## Character counts

- Changes/updates field: **1002 characters** (limit: < 1024 characters).
- Gen AI services field: **1002 characters** (limit: < 1024 characters).
- LinkedIn post draft: **1184 characters** (limit: < 1300 characters).
