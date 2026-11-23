# SaansPlan — Urban Air Quality & Winter Smog Assistant

[![CI](https://github.com/CodeWithMehru/saansplan/actions/workflows/ci.yml/badge.svg)](https://github.com/CodeWithMehru/saansplan/actions/workflows/ci.yml)
![Python 3.13](https://img.shields.io/badge/python-3.13-3776ab)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Coverage 91%](https://img.shields.io/badge/coverage-91%25-brightgreen)
![WCAG 2.2 AA](https://img.shields.io/badge/WCAG%202.2-AA%20Compliant-blue)

> **Hack2skill Challenge 6 Submission:** "Urban Air Quality Assistant"  
> A GenAI-powered assistant helping Indian families and communities navigate severe winter smog with low-emission daily routines, indoor air quality hacks, and verified alternatives tailored to their location and lifestyle.

---

## 1. Evaluation Criteria Mapping Table

Every evaluation criteria maps directly to concrete implementations, tests, and Makefile commands:

| Evaluation Criterion | Implementation Files & Modules | Verification Command | Proving Artifacts |
|---|---|---|---|
| **Code Quality** | Clean layered architecture (`app/core/`, `app/engine/`, `app/routers/`, `app/services/`), strict Pydantic schemas (`app/models.py`), modular ES-modules (`app/static/js/`), typed public APIs | `make lint`<br>`make typecheck` | `ruff check` (0 errors)<br>`mypy --strict app` (clean in 32 files) |
| **Security** | Zero API key exposure, no PII logging, XML prompt demarcation, 25-string multi-lingual injection corpus, SlowAPI proxy-aware rate limits, strict CSP, SSRF allowlist, Bandit & pip-audit | `make security` | [docs/SECURITY.md](docs/SECURITY.md)<br>`tests/security/` (100% pass)<br>`pip-audit` (0 vulns) |
| **Efficiency** | In-memory `BoundedTTLCache` (30m TTL, LRU), HTTP gzip compression, weak ETags, single-flight locking, engine plan computation in 2.8ms, gzipped static bundle 30.7 KB (< 60 KB budget) | `make bench` | [docs/TEST_REPORT.md](docs/TEST_REPORT.md)<br>`scripts/bench.py`<br>`app/core/cache.py` |
| **Testing** | 81 hermetic tests with 91.30% coverage (enforced ≥ 90% gate), property tests, golden tests, Node.js i18n test runner, Playwright multi-language E2E | `make test`<br>`make test-js`<br>`make e2e` | [TESTING.md](TESTING.md)<br>[docs/TEST_REPORT.md](docs/TEST_REPORT.md)<br>`pyproject.toml` |
| **Accessibility** | WCAG 2.2 Level AA compliance, Lighthouse Accessibility 100/100, 0 Axe-Core violations across EN/Hinglish/HI and populated views, 360px mobile reflow (WCAG 1.4.10), keyboard skip link, A-/A/A+ text scaling | `make a11y` | [docs/ACCESSIBILITY.md](docs/ACCESSIBILITY.md)<br>`scripts/a11y.py` (0 violations)<br>Lighthouse: 100/100 |
| **Problem Statement Alignment** | Indian winter smog focus, CPCB NAQI category breakpoints, physical inhaled $\mu$g estimates (EPA factors), 5-day smog forecast, "Cleaner Day" routine optimizer, emissions/cost calculator, WhatsApp kit | `pytest tests/unit/engine/` | [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md)<br>All citations verified 100% |

---

## 2. Problem Statement Alignment Table

| Challenge 6 Requirement | SaansPlan Solution | Technical Implementation |
|---|---|---|
| **GenAI-powered assistant** | Dual Groq LLM integration (`openai/gpt-oss-20b`) for parsing unstructured routine text and explaining validated facts with deterministic template fallback | `app/services/llm.py`, `app/services/guard.py` |
| **Families & communities** | Multi-member household profiles (children, adults, elderly, sensitive members) with age-scaled inhalation; WhatsApp community kit and RWA morning advisories | `app/engine/inhaled.py`, `app/engine/community.py`, `app/static/js/render.js` |
| **Severe winter smog** | Indian CPCB NAQI category breakpoints (Good to Severe+), 5-day winter smog forecasting, midday ventilation windows, surface wind stagnation warnings (< 2 m/s) | `app/core/aqi.py`, `app/engine/forecast.py`, `app/services/air_quality.py` |
| **Low-emission daily routines** | "Your Cleaner Day" optimizer: shifts flexible outdoor tasks to cleaner afternoon hours while strictly preserving fixed work/school commitments | `app/engine/cleaner_day.py`, `app/engine/swaps.py` |
| **Indoor air quality hacks** | AHAM CADR 2/3 room-sizing calculator, verified DIY Corsi-Rosenthal box-fan filter guide (EPA), wet-mopping vs broom sweep, room checklists | `app/engine/indoor_module.py`, `app/engine/alternatives.py` |
| **Sustainable alternatives** | Weekly carbon emissions ($\text{kg CO}_2\text{e}$) and cost ($\text{INR}$) comparison for commute, cooking, and heating, filtered by budget tiers (`free`, `< ₹500`, `< ₹5000`) | `app/engine/emissions.py`, `app/static/js/render.js` |
| **Direct impact explanation** | Estimated inhaled PM2.5 dosage in micrograms ($\mu\text{g}$) with a transparent $\pm 25\%$ uncertainty band; before-and-after comparison chart and accessible table | `app/engine/inhaled.py`, `app/engine/cleaner_day.py` |

---

## 3. Architecture & System Flow

```mermaid
flowchart TD
    subgraph Client["Client Browser (Vanilla HTML5 / CSS3 / ES-Modules)"]
        UI["User Form & Persona Presets<br/>(Working Parents, Elderly, Student, Rider)"]
        A11Y["WCAG 2.2 AA Focus Router & Announcer"]
        I18N["Bilingual Locales<br/>(English, Hinglish, Hindi)"]
    end

    subgraph Server["FastAPI Backend (Python 3.13 Stateless)"]
        RT["FastAPI Routers (/api/plan, /api/ask, /api/geocode, /health)"]
        SEC["Security & CSP Middleware<br/>(Rate Limiting, Size Guard, Strict Headers)"]
        CACHE["BoundedTTLCache<br/>(30m TTL, LRU Eviction, Single-Flight Lock)"]
        
        subgraph Engines["Deterministic Physical & Optimization Engines"]
            EXP["Exposure Simulation Engine<br/>(app/engine/exposure.py)"]
            INH["Inhaled Dose Engine (EPA factors)<br/>(app/engine/inhaled.py)"]
            FC["5-Day Smog Forecast Engine<br/>(app/engine/forecast.py)"]
            CD["Cleaner Day Optimizer<br/>(app/engine/cleaner_day.py)"]
            EM["Emissions & Cost Calculator<br/>(app/engine/emissions.py)"]
            INDOOR["AHAM CADR & DIY Box-Fan Engine<br/>(app/engine/indoor_module.py)"]
        end

        subgraph Guard["Security & Fallback Layer"]
            G1["Input Sanitizer & XML Demarcation"]
            G2["Medical Symptom Guard (Doctor Redirect)"]
            G3["Number Guard (Fact Whitelist Validation)"]
        end
    end

    subgraph External["External Services"]
        OM["Open-Meteo Air Quality & Geocoding API"]
        GROQ["Groq Cloud API (openai/gpt-oss-20b)"]
        KB["Grounded Verified Knowledge Base<br/>(app/kb/knowledge.json)"]
    end

    UI -->|JSON Payload| SEC --> RT
    RT --> CACHE
    CACHE -->|Cache Miss| OM
    RT --> G1 --> GROQ
    GROQ -->|Routine JSON| G2 --> EXP
    EXP --> INH
    EXP --> FC
    EXP --> CD
    EXP --> EM
    EXP --> INDOOR
    Engines --> G3 --> GROQ
    GROQ -->|Fact Explanation| RT
    RT -->|Gzip Compressed Response| UI
```

---

## 4. Render Deployment & Python 3.13 Pinning

SaansPlan is continuously deployed on Render Free Tier (512 MB RAM limit).

### Why Python 3.13 is Strictly Pinned
Render's default Linux build environment uses the latest bleeding-edge Python (Python 3.14+). At the time of deployment, `pydantic-core` does not provide pre-compiled binary wheels for Python 3.14 on Linux `x86_64`/`aarch64`. Consequently, `pip` attempts to compile `pydantic-core` from source using the Rust compiler, which exceeds Render's 512 MB RAM limit and causes build timeouts.

To guarantee deterministic, instantaneous deployments, Python 3.13 is strictly pinned across two configuration files:
1. `.python-version`: `3.13.2` (read by Render buildpack).
2. `render.yaml`: `envVars: [{ key: PYTHON_VERSION, value: 3.13.2 }]`.

---

## 5. Failure Modes & Graceful Degradation

| Failure Mode | Root Cause | System Response & Graceful Degradation |
|---|---|---|
| **Groq API Outage / Rate Limit** | Groq service downtime or quota exhaustion | System automatically catches `httpx.HTTPError` and falls back to deterministic rule-based routine parsing and template explanations. The user receives a 100% complete, fully functional plan without interruption. |
| **Open-Meteo API Down** | Upstream weather provider unreachable | Cached air quality data is returned if available. If no cache exists, the system gracefully falls back to regional seasonal baseline values with clear UI notice. |
| **Missing Hourly PM2.5 Data** | Sensor gaps or null values from API | Linear interpolation engine (`app/engine/exposure.py`) fills missing hours; interpolated slots are explicitly marked with an asterisk in the timeline table. |
| **Medical Query Submitted** | User asks for diagnosis, cough syrup, or medical treatment | The clinical safety guard (`app/services/guard.py`) intercepts health keywords and immediately returns a safe medical advisory directing the user to a doctor or emergency clinic. |
| **Prompt Injection Attack** | Adversarial text attempting to hijack system prompts | XML data demarcation confines user input to data slots; system prompts explicitly forbid executing tools or commands; 25 multi-lingual test strings verify 100% neutralization. |
| **Slow Network / Client Disconnect** | High-latency mobile network | Client-side `AbortController` enforces a 14s timeout; server uses an 8s outbound timeout and GZip compression to ensure payloads stay under 31 KB. |

---

## 6. Quickstart & Local Reproduction

### Prerequisites
- Python 3.13 (`python3 --version`)
- Node.js (`node --version`, for i18n tests)
- Chromium (`/usr/bin/chromium` or Playwright)

### Setup Instructions

```bash
# 1. Clone repository
git clone git@github.com:CodeWithMehru/saansplan.git
cd saansplan

# 2. Set up virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# 3. Configure local environment (optional for local mock testing)
cp .env.example .env
# Edit .env and insert GROQ_API_KEY if testing live LLM calls

# 4. Run full verification suite
make verify

# 5. Start development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 7. Verified Citations & Assumptions

All scientific constants, emission factors, and health guidance in SaansPlan are verified against original publishers:
- **CPCB NAQI Breakpoints:** Gazette of India / MoEFCC notification (0-30 Good, 31-60 Satisfactory, 61-90 Moderate, 91-120 Poor, 121-250 Very Poor, >250 Severe).
- **EPA Exposure Factors Handbook (Chapter 6):** Age-specific inhalation rates (Adult ~15.7 $\text{m}^3/\text{day}$, Child ~10.0 $\text{m}^3/\text{day}$, Elderly ~13.3 $\text{m}^3/\text{day}$).
- **AHAM / US EPA Air Cleaners in the Home:** CADR 2/3 room-area sizing rule ($\text{CADR in CFM} \ge 2/3 \times \text{area in sq ft}$).
- **US EPA Science Matters:** DIY Box Fan filter (Corsi-Rosenthal principle) with MERV 13 rating.
- **WHO Household Fuel Guidelines:** Solid fuels (wood/coal/cow dung) produce severe indoor PM2.5 spikes; induction eliminates combustion emissions.

See full verification audit in [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md).
