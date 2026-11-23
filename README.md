# SaansPlan — Urban Air Quality & Winter Smog Assistant

[![CI](https://github.com/CodeWithMehru/saansplan/actions/workflows/ci.yml/badge.svg)](https://github.com/CodeWithMehru/saansplan/actions/workflows/ci.yml)
![Python 3.13](https://img.shields.io/badge/python-3.13-3776ab)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Coverage 91%](https://img.shields.io/badge/coverage-91.18%25-brightgreen)
![WCAG 2.2 AA](https://img.shields.io/badge/WCAG%202.2-AA%20Compliant-blue)

> **Hack2skill Challenge 6 Submission:** "Urban Air Quality Assistant"  
> A GenAI-powered assistant helping Indian families and communities navigate severe winter smog with low-emission daily routines, indoor air quality hacks, and verified alternatives tailored to their location and lifestyle.

**Live Demo:** [https://saansplan.onrender.com](https://saansplan.onrender.com) *(Hosted on Render free tier; if idle, initial spin-up takes ~60 seconds. Health probe: `/health`)*

---

## Table of Contents
1. [Live Demo & Overview](#saansplan--urban-air-quality--winter-smog-assistant)
2. [Evaluation Criteria Mapping](#1-evaluation-criteria-mapping)
3. [What's New Since Attempt 1](#2-whats-new-since-the-first-submission)
4. [Problem Statement Alignment](#3-problem-statement-alignment)
5. [Target Persona & System Architecture](#4-target-persona--system-architecture)
6. [API Specification & Examples](#5-api-specification--endpoint-reference)
7. [Environment Variables & Deployment](#6-environment-variables--deployment)
8. [Setup & Local Reproduction](#7-setup--local-reproduction)
9. [Verification Suites Summary](#8-verification-suites-summary)
10. [Responsible AI & Privacy Safeguards](#9-responsible-ai--privacy-safeguards)
11. [Assumptions & Limitations](#10-assumptions--limitations)
12. [Data Sources & Attribution](#11-data-sources--attribution)

---

## 1. Evaluation Criteria Mapping

Every evaluation criteria maps directly to concrete implementations, verification commands, and documented artifacts:

| Evaluation Criterion | Implementation Files & Modules | Verification Command | Proving Artifacts & Real Measured Results |
|---|---|---|---|
| **Code Quality** | Clean layered architecture (`app/core/`, `app/engine/`, `app/routers/`, `app/services/`), strict Pydantic schemas (`app/models.py`), modular ES-modules (`app/static/js/`), typed public APIs | `make lint`<br>`make typecheck` | `ruff check` (0 errors across 70 files)<br>`mypy app` (clean across 32 source files) |
| **Security** | Zero API key exposure, no PII logging, XML prompt demarcation, 25-string multi-lingual injection corpus, SlowAPI proxy-aware rate limits (30 req/min), strict CSP, SSRF allowlist, Bandit & pip-audit | `make security` | [docs/SECURITY.md](docs/SECURITY.md)<br>`tests/security/` (26 passed, 100%)<br>`bandit` (0 issues), `pip-audit` (0 CVEs) |
| **Efficiency** | In-memory `BoundedTTLCache` (30m TTL, LRU eviction, max 64 items), HTTP gzip compression (min 1000 B), weak ETags, single-flight locking, engine plan computation in 2.14 ms, gzipped static bundle 26.63 KB (< 60 KB budget) | `make bench` | [docs/TEST_REPORT.md](docs/TEST_REPORT.md)<br>`scripts/bench.py`<br>`app/core/cache.py` |
| **Testing** | 124 hermetic tests with 91.18% coverage (enforced ≥ 90% gate), property tests, golden tests, Node.js i18n test runner (2 tests), Playwright multi-language E2E | `make test`<br>`make test-js`<br>`make e2e` | [TESTING.md](TESTING.md)<br>[docs/TEST_REPORT.md](docs/TEST_REPORT.md)<br>`pyproject.toml` (`--cov-fail-under=90`) |
| **Accessibility** | WCAG 2.2 Level AA compliance, 0 Axe-Core violations across EN/Hinglish/HI and populated views (43 initial rules, 56 populated rules), 360px mobile reflow (WCAG 1.4.10), keyboard skip link, A-/A/A+ text scaling (90%–120%) | `make a11y` | [docs/ACCESSIBILITY.md](docs/ACCESSIBILITY.md)<br>`scripts/a11y.py` (0 violations)<br>Static AST: 100% label and landmark binding |
| **Problem Statement Alignment** | Indian winter smog focus, CPCB NAQI category breakpoints, physical inhaled $\mu\text{g}$ estimates (EPA factors, ±25% range), 5-day smog forecast, "Cleaner Day" routine optimizer, emissions/cost calculator, WhatsApp kit | `pytest tests/unit/engine/` | [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md)<br>All 8 citations primary-source verified |

---

## 2. What's New Since the First Submission

Attempt 1 scored 70.53/100 (Code Quality 52, Security 78, Efficiency 70, Testing 0, Accessibility 45, Problem Statement Alignment 60). The following systemic fixes and features were engineered:

| Criterion | Defect / Limitation in Attempt 1 | Resolution in SaansPlan 2.0 | Proving Files / Tests |
|---|---|---|---|
| **Testing** (0 → 91%+) | Testing scored 0 because dev-dependencies were unseparated, tests had missing discoverability, and CI was red. | Established hermetic test suite with 124 pytest unit/property/golden tests, 91.18% coverage enforced in `pyproject.toml`, Node.js native i18n runner, and a clean green GitHub Actions CI pipeline. | `pyproject.toml`, `requirements-dev.txt`, `.github/workflows/ci.yml` |
| **Code Quality** (52 → 90+) | Raw internal snake_case identifiers displayed in UI (`wood_coal`, `mostly_closed`), monolithic frontend script. | Built F10 human-readable translation registry in English, Hinglish, and Hindi (`app/static/js/utils.js`); refactored frontend into modular ES-modules (`api.js`, `render.js`, `state.js`, `focus.js`). | `app/static/js/utils.js`, `app/static/js/render.js` |
| **Problem Alignment** (60 → 95+) | Conflated peak outdoor AQI hour with peak personal exposure hour; raw meaningless exposure units (`47872.35`). | Separated "Highest AQI Hour" from "Highest Inhaled Intake Hour"; replaced arbitrary numbers with physical inhaled dosage in micrograms ($\mu\text{g}$) using EPA inhalation rates and ±25% uncertainty bands. | `app/engine/exposure.py`, `app/engine/inhaled.py`, `tests/test_guard.py` |
| **AI Explanation Quality** | Raw units, "Peak hour 0", and past-tense claims ("dropped", "kam hua") for hypothetical routine plans. | Re-anchored explanation prompt and Number Guard strictly to physical units ($\mu\text{g}$, percent) and 12-hour clock times ("6 pm", "shaam 6 baje"); enforced forward-looking hypothetical phrasing ("could reduce about 29% (estimate)"). | `app/services/guard.py`, `app/services/llm.py`, `tests/test_guard.py` |
| **Grounded Assistant** | `/api/ask` returned ungrounded static snippets without server-side recalculation or CADR sizing. | Grounded `/api/ask` with deterministic CADR calculation (AHAM 2/3 rule: 150 sq ft → 100 CFM), live plan context, and immediate emergency medical redirects for acute respiratory symptoms. | `app/routers/ask.py`, `tests/api/test_ask_endpoint.py` |
| **Accessibility** (45 → 95+) | Missing keyboard focus management, missing landmarks, no mobile reflow, unlabelled form inputs. | Added visible `.skip-link`, semantic landmarks (`role="banner"`, `main`, `contentinfo`), A-/A/A+ text scaling, full 360px reflow without horizontal scrolling, and 0 Axe-Core violations. | `app/static/index.html`, `app/static/js/a11y/focus.js`, `scripts/a11y.py` |
| **Repository Hygiene** | Multiple branches and Dependabot bot churn. | Pinned strictly to a single branch (`main`), removed branch-creating bots, maintained clean repository size under 2 MB with zero node_modules or venvs committed. | `git branch -a`, `git count-objects -vH` |

---

## 3. Problem Statement Alignment

Every phrase of Hack2skill Challenge 6 ("Urban Air Quality Assistant") is backed by domain logic:

| Challenge Phrase | SaansPlan Solution | Technical Implementation & Tests |
|---|---|---|
| **GenAI-powered assistant** | Dual Groq LLM integration (`openai/gpt-oss-20b`) for parsing unstructured routine text and generating guard-validated natural language explanations with deterministic template fallback | `app/services/llm.py`, `app/services/guard.py`, `tests/unit/test_llm_branches.py` |
| **Families & communities** | Multi-member household profiles (children, adults, elderly, sensitive members) with age-scaled inhalation; WhatsApp community kit and RWA morning advisories | `app/engine/inhaled.py`, `app/engine/community.py`, `tests/unit/engine/test_inhaled_properties.py` |
| **Severe winter smog** | Indian CPCB NAQI category breakpoints (Good to Severe), 5-day winter smog forecasting, midday ventilation windows (11 AM–3 PM), surface wind stagnation alerts (< 2 m/s) | `app/core/aqi.py`, `app/engine/forecast.py`, `tests/unit/engine/test_cpcb_category.py` |
| **Low-emission daily routines** | "Your Cleaner Day" optimizer: shifts flexible outdoor tasks to cleaner afternoon hours while strictly preserving fixed work/school commitments | `app/engine/cleaner_day.py`, `app/engine/swaps.py`, `tests/unit/engine/test_cleaner_day.py` |
| **Indoor air quality hacks** | AHAM CADR 2/3 room-sizing calculator, verified DIY Corsi-Rosenthal box-fan filter guide (EPA), wet-mopping vs dry sweeping, room checklists | `app/engine/indoor_module.py`, `app/engine/alternatives.py`, `tests/unit/engine/test_indoor_module.py` |
| **Sustainable alternatives** | Weekly carbon emissions ($\text{kg CO}_2\text{e}$) and cost ($\text{INR}$) comparison for commute, cooking, and heating, filtered by budget tiers (`free`, `< ₹500`, `< ₹5000`, `any`) | `app/engine/emissions.py`, `tests/unit/engine/test_emissions.py` |
| **Tailored to location & lifestyle** | Open-Meteo geocoding search with auto coordinate binding; 4 lifestyle presets (Working Parents, Senior Citizen, Student, Delivery Rider) | `app/routers/geocode.py`, `app/engine/personas.py`, `tests/test_geocode_and_csp.py` |
| **Explaining direct impact of choices** | Estimated inhaled PM2.5 dosage in micrograms ($\mu\text{g}$) with transparent $\pm 25\%$ uncertainty band; before-and-after comparison chart and accessible table | `app/engine/inhaled.py`, `app/static/js/render.js`, `tests/unit/engine/test_exposure_properties.py` |

---

## 4. Target Persona & System Architecture

### Target Persona
Urban Indian families navigating severe Indo-Gangetic Plain winter smog (e.g. Delhi NCR, Lucknow, Patna). Households include multi-generational members (school children, working adults, elderly grandparents with respiratory vulnerabilities) who must balance rigid daily commitments (school transit, office commute) with flexible exposures (evening walks, shopping, indoor heating choices).

### Deterministic Engine vs LLM Division of Labor
To guarantee safety and prevent mathematical hallucination:
- **All numbers, physical dosage estimates ($\mu\text{g}$), percentages, CPCB categories, and schedules are computed exclusively by pure, deterministic Python functions.**
- The LLM (Groq `openai/gpt-oss-20b`) is confined strictly to:
  1. Parsing unstructured free text into strict Pydantic schemas.
  2. Generating natural language explanations using *only* whitelist facts supplied by the engine.
  3. Grounded Q&A assistance using verified knowledge base entries.
- If the LLM produces an ungrounded numeral, past-tense claim, or is unavailable, the system instantly serves the deterministic template output.

```mermaid
flowchart TD
    subgraph Client["Client Browser (Vanilla HTML5 / CSS3 / ES-Modules)"]
        UI["User Form & Persona Presets<br/>(Working Parents, Elderly, Student, Rider)"]
        A11Y["WCAG 2.2 AA Focus Router & Announcer"]
        I18N["Trilingual Locales<br/>(English, Hinglish, Hindi)"]
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
        OM["Open-Meteo Air Quality & Weather API"]
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

## 5. API Specification & Endpoint Reference

### 1. Health Probe
- **Method:** `GET`
- **Paths:** `/health`, `/api/health`
- **Purpose:** Zero-dependency liveness and readiness probe for reverse proxies and monitoring.
- **Response Example:**
  ```json
  {"status": "ok", "service": "SaansPlan"}
  ```

### 2. Plan Generation (`/api/plan`)
- **Method:** `POST`
- **Path:** `/api/plan`
- **Rate Limit:** 30 requests / minute
- **Purpose:** Fetches atmospheric dispersion data, parses routine text, executes deterministic physical engines, and generates verified recommendations.
- **Request Example:**
  ```json
  {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "city": "Delhi",
    "members": [
      {"name": "Parent", "age_group": "adult", "sensitive": False},
      {"name": "Child", "age_group": "child", "sensitive": True}
    ],
    "routine_text": "Subah 7:30 bache ko school drop karte hain, 9 baje metro se office, shaam 6 baje park walk.",
    "language": "hinglish"
  }
  ```
- **Response Highlights:**
  - `exposure`: `peak_aqi`, `peak_aqi_hour` (e.g. 0), `peak_exposure_hour` (e.g. 8), `total_inhaled_ug`, `uncertainty_band_ug` (`[min, max]`).
  - `hourly`: 24-hour breakdown with `pm25`, `aqi`, `indian_category`, `indian_aqi`, `exposure`, `interpolated`.
  - `forecast`: 5-day daily forecast with `worst_window`, `best_window`, `safest_airing_hour`, `is_stagnant`, `avg_wind_speed_mps`.
  - `cleaner_day`: Optimized 24h schedule with `inhaled_saved_ug`, `percent_reduction`, and before/after hourly table.
  - `explanation`: `ai_available` (`bool`), `explanation` (guard-validated string).

### 3. Grounded Q&A Assistant (`/api/ask`)
- **Method:** `POST`
- **Path:** `/api/ask`
- **Rate Limit:** 30 requests / minute
- **Purpose:** Synthesizes air-quality answers from verified KB entries, computes deterministic CADR sizing, and enforces clinical non-intervention redirects.
- **Request Example:**
  ```json
  {
    "question": "What CADR air purifier is recommended for a 150 sq ft bedroom?"
  }
  ```
- **Response Example:**
  ```json
  {
    "answer": "For a 150 sq ft bedroom, the AHAM 2/3 guideline recommends a Smoke CADR of about 100 CFM (~170 m³/h) to achieve roughly 5 air changes per hour. [purifier-sizing]",
    "kb_ids": ["purifier-sizing"],
    "safety_redirect": false
  }
  ```

### 4. City Geocoding Search (`/api/geocode`)
- **Method:** `GET`
- **Path:** `/api/geocode?name=Delhi`
- **Rate Limit:** 30 requests / minute
- **Purpose:** Proxies Open-Meteo geocoding with strict parameter validation and safe bounding.
- **Response Example:**
  ```json
  {
    "results": [
      {"name": "Delhi", "latitude": 28.65195, "longitude": 77.23149, "country": "India"}
    ]
  }
  ```

---

## 6. Environment Variables & Deployment

### Environment Variables Matrix

| Variable | Type | Default Value | Description |
|---|---|---|---|
| `GROQ_API_KEY` | Secret String | `None` (Optional) | API key for Groq Cloud. If unset, app operates in deterministic mode using `default_routine` and `templated_explanation`. |
| `GROQ_MODEL` | String | `"openai/gpt-oss-20b"` | Model endpoint identifier on Groq OpenAI-compatible API. |
| `TRUST_PROXY` | Boolean String | `"false"` | When set to `"true"`, reads real client IP from first `X-Forwarded-For` header entry for reverse proxy rate limiting. |
| `ENVIRONMENT` | String | `"production"` | Set to `"development"` to enable Swagger UI at `/docs` and OpenAPI schema. |
| `CORS_ORIGINS` | Comma-delimited String | `"http://localhost:8000"` | Allowed CORS origins. |
| `PORT` | Integer | System assigned / `10000` | Port listened to by Uvicorn. |

### Docker Deployment
The application includes a production multi-stage `Dockerfile`:
```bash
docker build -t saansplan .
docker run -p 10000:10000 --env GROQ_API_KEY="your-key" saansplan
```
Runs as an unprivileged non-root user (`saansplan`), binds port `10000`, and contains zero dev dependencies.

### Render Free Tier Deployment & Python Version Pinning
Render's default Linux build environment uses Python 3.14+, where `pydantic-core` lacks pre-compiled wheels, causing heavy Rust source compilation that exceeds Render's 512 MB RAM limit.
To ensure instantaneous binary builds, Python 3.13 is strictly pinned:
- `.python-version`: `3.13`
- `render.yaml`: `envVars: [{ key: PYTHON_VERSION, value: 3.13.0 }]`

---

## 7. Setup & Local Reproduction

### Prerequisites
- Python 3.13 (`python3 --version`)
- Node.js (`node --version`, for frontend i18n runner)

### Step-by-Step Instructions

```bash
# 1. Clone repository via HTTPS
git clone https://github.com/CodeWithMehru/saansplan.git
cd saansplan

# 2. Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# 3. Configure local environment (optional for local testing)
cp .env.example .env
# Edit .env and supply GROQ_API_KEY if testing live LLM calls

# 4. Run full quality and verification pipeline
make verify

# 5. Start development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 8. Verification Suites Summary

### 1. Quality Gates
```bash
make lint        # ruff format --check & ruff check app tests scripts (0 errors)
make typecheck   # mypy app (clean across 32 source files)
make test        # pytest with coverage enforcement (124 passed, 91.18% coverage)
make test-js     # node --test app/static/tests/*.test.js (2 passed)
make security    # bandit -q -r app & pip-audit -r requirements.txt (0 issues)
make a11y        # Axe-Core 4.10.2 WCAG 2.2 AA audit (0 violations)
make bench       # Engine speed and static bundle size benchmarks
```

### 2. Measured Benchmark Performance
- **Engine Execution Speed:** `1.56 ms` for a 6-member family plan (< 50 ms budget).
- **Interpolation Throughput:** `44.19 ms` for 1000 runs (< 200 ms budget).
- **Static Bundle Size:** `26.63 KB` gzipped (< 60 KB budget; raw: 90.48 KB).
- **Overall Test Coverage:** `91.18%` branch + statement coverage across 1110 statements.

---

## 9. Responsible AI & Privacy Safeguards

1. **Estimates, Not Medical Advice:** All inhaled dosages ($\mu\text{g}$) and reduction percentages are planning estimates with explicit $\pm 25\%$ uncertainty bounds. The assistant does not diagnose, prescribe, or provide clinical triage.
2. **Deterministic Guardrails (Number Guard):** The LLM is technically prevented from inventing numbers. The Number Guard validates every numeral against engine facts. Any ungrounded numeral immediately triggers the deterministic template fallback.
3. **Clinical Safety Intercept:** If user input mentions acute respiratory symptoms ("chest tightness", "severe shortness of breath", "wheezing") or asks for medication ("dawa", "cough syrup", "antibiotic"), the system refuses medical advice and outputs an immediate emergency doctor redirect.
4. **Privacy by Design:**
   - Stateless backend: zero user accounts, zero database persistence of routines or health indicators.
   - User routine text is processed purely in-memory and never written to logs or disk.
   - Coordinates are rounded to 2 decimal places in cache keys (~1.1 km spatial resolution).

---

## 10. Assumptions & Limitations

All scientific constants and assumptions are detailed in [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md):
- **Planning Estimates, Not Clinical Measurements:** Inhaled intake calculations use EPA Exposure Factors Handbook reference breathing volumes; real-world intake depends on individual lung capacity, nasal vs oral breathing, and exact indoor air exchange rates.
- **Modelled Forecasts vs Local Sensors:** Open-Meteo uses atmospheric dispersion models (CAMS ensemble). While capturing regional transport and winter stagnation, localized micro-hotspots (e.g., hyper-local street trash burning) may differ from grid averages.
- **CPCB Categorization Scale:** CPCB National AQI categories are officially standardized on 24-hour average PM2.5 concentrations. SaansPlan applies these breakpoints to hourly values to provide immediate real-time behavioral guidance.
- **Groq Free-Tier Rate Limits:** On free tier, Groq applies request-per-minute limits. During burst testing, we measured an ~20% fallback rate where requests gracefully degraded to `templated_explanation` (with 0% guard rejections).
- **Language Localization:** Hindi and Hinglish translations were programmatically verified for key parity and script integrity, but have not undergone formal human review by native linguistics experts.
- **Automated Accessibility Testing:** Accessibility compliance was verified via automated Axe-Core 4.10.2 audits, Playwright, and static AST parsers (0 violations); manual testing by human users with screen-readers (NVDA, VoiceOver) has not been performed.
- **Free Hosting Cold Starts:** On Render's free tier, the web service spins down after inactivity; initial cold start takes ~60 seconds.

---

## 11. Data Sources & Attribution

All external data sources and citations are documented in [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md) and verified:
- **Open-Meteo Air Quality & Weather API:** Hourly PM2.5, AQI, and 10m surface wind speed data provided by [Open-Meteo.com](https://open-meteo.com/), licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
- **Groq Cloud API:** Cloud inference for `openai/gpt-oss-20b` via the OpenAI-compatible REST API.
- **CPCB NAQI Standards:** Ministry of Environment, Forest and Climate Change (MoEFCC) / Central Pollution Control Board (Gazette Oct 2014) [PIB Release 110654](https://pib.gov.in/newsite/PrintRelease.aspx?relid=110654).
- **US EPA Exposure Factors Handbook (Chapter 6):** Physiological inhalation rates for adults, children, and older adults [EPA Exposure Factors](https://www.epa.gov/expobox/about-exposure-factors-handbook).
- **AHAM AC-1 & US EPA:** CADR 2/3 room-sizing rule for portable air cleaners [EPA Air Cleaners in the Home](https://www.epa.gov/indoor-air-quality-iaq/air-cleaners-and-air-filters-home).
- **US EPA Science Matters:** Research on DIY Corsi-Rosenthal Box-Fan air cleaners [EPA DIY Air Cleaners](https://www.epa.gov/sciencematters/do-it-yourself-air-cleaners-making-cleaner-air-more-accessible).
- **WHO Household Fuel Combustion Guidelines:** Health risks of indoor biomass/coal combustion and benefits of clean fuels [WHO Household Fuel Guidelines](https://www.who.int/publications/i/item/9789241548885).
- **IPCC Emission Factor Database (EFDB):** Carbon intensity values for urban passenger transport modes [IPCC EFDB](https://www.ipcc-nggip.iges.or.jp/EFDB/main.php).
