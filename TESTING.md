# Testing & Verification Guide

This document describes the test architecture, hermetic execution policy, test suites, and traceability matrix from challenge phrases and README claims to existing test implementations.

---

## 1. Hermetic Testing Policy

Every test in the `tests/` suite executes hermetically:
- **No API keys required:** Tests execute cleanly in environments with no `.env` file and no `GROQ_API_KEY` set.
- **No live network required:** All external network calls (Open-Meteo, Groq) are intercepted using unittest mocks and predefined golden payloads.
- **Strict coverage enforcement:** `pyproject.toml` enforces a minimum 95% overall line and branch coverage threshold (`--cov-fail-under=95`). A plain `pytest` run fails if coverage drops below this threshold (measured: 96.07% across 178 tests).

---

## 2. Test Suites Overview

| Suite Directory / File | Description | Key Areas Covered |
|---|---|---|
| `tests/unit/engine/` | Pure deterministic domain calculations | CPCB PM2.5 category breakpoints, physical inhaled dosage ($\mu\text{g}$) with $\pm 25\%$ uncertainty bounds, 5-day smog forecast, Cleaner Day routine optimizer, carbon emissions & INR cost models, AHAM CADR sizing, indoor penetration. |
| `tests/unit/test_branch_coverage.py` | Targeted branch coverage gaps | Cache LRU eviction, geocoding error responses, air quality backoffs, plan defaults, assistant CADR resolution. |
| `tests/unit/test_fault_injection.py` | Chaos & resilience testing | Open-Meteo 500s, malformed upstream JSON, Groq 429 rate limits, and reverse-proxy client IP spoofing defense. |
| `tests/unit/test_property_invariants.py` | Hypothesis property-based testing | Inhaled dosage non-negativity, CPCB monotonic ordering, CADR scaling linearity, cleaner-day reduction bounds. |
| `tests/unit/test_architecture_boundaries.py` | Static AST architecture boundary check | Verifies unidirectional dependency flow: Routers $\to$ Services $\to$ Engine (pure & deterministic). |
| `tests/api/test_characterization_snapshots.py` | Regression characterization snapshots | 7 full JSON response snapshots matching golden baseline outputs across family personas and edge cases. |
| `tests/api/` | FastAPI endpoint contracts | `/api/plan` schema validation, 422 error envelopes, 12-member household limit, `/api/ask` grounded QA, `/health` and `/api/health` probes. |
| `tests/security/test_prompt_injection.py` | Adversarial injection resistance | 48-string multi-lingual prompt injection corpus (English, Hinglish, Hindi) tested and blocked. |
| `tests/security/test_http_hardening.py` | Defensive HTTP headers & RFC 9116 | Content-Type 415 rejection for non-JSON POST, CORP same-origin, X-Request-ID, RFC 9116 security.txt validation, zero key leakage. |
| `tests/a11y/test_static_markup.py` | Accessibility AST markup tests | Single `<h1>` document hierarchy, semantic landmarks, form control labels, scoped table headers, zero inline JavaScript event handlers. |
| `app/static/tests/` | Frontend native test runner (`node --test`) | Key parity across English, Hinglish, and Hindi translation dictionaries; Devanagari script integrity validation. |
| `scripts/a11y.py` | Automated Axe-Core audit | End-to-end WCAG 2.2 Level AA compliance check across initial, translated, and populated views (0 violations across 56 rules). |
| `scripts/verify_lighthouse.py` | Automated Google Lighthouse runner | Runs headless Chrome Lighthouse accessibility audit (measured: 100/100). |
| `scripts/e2e.py` | Playwright end-to-end journey | Automated verification of city search, persona prefilling, plan generation, human-readable labels, and zero console errors. |

---

## 3. Challenge Phrases & README Claims Traceability Matrix

Every core challenge phrase from Hack2skill Challenge 6 ("Urban Air Quality Assistant") and every technical claim in `README.md` traces directly to automated test implementations:

| Challenge Phrase / README Claim | Technical Implementation Module | Proving Automated Test(s) |
|---|---|---|
| **GenAI-powered assistant** | `app/services/llm.py`<br>`app/services/assistant.py` | `tests/unit/test_llm_branches.py`<br>`tests/api/test_ask_endpoint.py`<br>`tests/test_llm_calls.py` |
| **Families & communities** | `app/schemas/family.py`<br>`app/engine/community.py`<br>`app/engine/personas.py` | `tests/unit/engine/test_inhaled_properties.py`<br>`tests/api/test_plan_endpoint.py`<br>`tests/test_schema_validation.py` |
| **Severe winter smog** | `app/core/aqi.py`<br>`app/engine/forecast.py` | `tests/unit/engine/test_cpcb_category.py`<br>`tests/unit/engine/test_forecast.py`<br>`tests/unit/test_property_invariants.py` |
| **Low-emission daily routines** | `app/engine/cleaner_day.py`<br>`app/engine/swaps.py` | `tests/unit/engine/test_cleaner_day.py`<br>`tests/test_swaps.py`<br>`tests/unit/test_property_invariants.py` |
| **Indoor air quality hacks** | `app/engine/indoor_module.py`<br>`app/engine/indoor_penetration.py` | `tests/unit/engine/test_indoor_module.py`<br>`tests/unit/engine/test_indoor_branches.py`<br>`tests/api/test_ask_endpoint.py` |
| **Sustainable alternatives** | `app/engine/emissions.py`<br>`app/engine/alternatives.py` | `tests/unit/engine/test_emissions.py`<br>`tests/test_engine.py` |
| **Tailored to location & lifestyle** | `app/routers/geocode.py`<br>`app/engine/personas.py` | `tests/test_geocode_and_csp.py`<br>`tests/unit/test_branch_coverage.py` |
| **Explaining direct impact of choices** | `app/engine/inhaled.py`<br>`app/services/guard_numbers.py`<br>`app/services/guard_wording.py` | `tests/unit/engine/test_inhaled_properties.py`<br>`tests/test_guard.py`<br>`tests/unit/test_guard_branches.py` |
| **Medical Symptom Interception** | `app/services/assistant_resolvers.py`<br>`app/services/guard_safety.py` | `tests/api/test_ask_endpoint.py`<br>`tests/unit/test_branch_coverage.py` |
| **Prompt Injection Defense** | `app/services/assistant_resolvers.py`<br>`app/services/llm.py` | `tests/security/test_prompt_injection.py` (48 test vectors) |
| **Content-Type 415 Enforcement** | `app/main.py` | `tests/security/test_http_hardening.py` |
| **Reverse Proxy IP Trust Defense** | `app/core/limiting.py` | `tests/security/test_real_client_ip.py`<br>`tests/unit/test_fault_injection.py` |
| **OpenAPI & Regression Snapshots** | `app/routers/plan.py`<br>`app/routers/geocode.py` | `tests/api/test_characterization_snapshots.py` (7 snapshots)<br>`tests/test_geocode_and_csp.py` |
| **WCAG 2.2 AA Compliance** | `app/static/index.html`<br>`app/static/styles.css` | `tests/a11y/test_static_markup.py`<br>`scripts/a11y.py` (56 rules across 5 states) |
| **Sub-50ms Engine Execution** | Pure deterministic Python modules | `scripts/bench.py`<br>`tests/unit/engine/test_golden.py` |

---

## 4. Clean Clone Verification

To prove that tests pass independently in a clean environment with zero ambient state and no `.env`:

```bash
# 1. Clone into a clean directory
git clone https://github.com/CodeWithMehru/saansplan.git /tmp/verify_clean
cd /tmp/verify_clean

# 2. Confirm no .env is present
[ ! -f .env ] && echo "Clean environment: no .env present"

# 3. Create fresh Python 3.13 venv and install dependencies
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# 4. Run pytest suite (enforces >= 95% coverage)
pytest

# 5. Run frontend i18n unit tests
node --test app/static/tests/*.test.js

# 6. Run lint and typecheck
ruff format --check app tests scripts
ruff check app tests scripts
mypy app

# 7. Run security checks
bandit -q -r app
pip-audit -r requirements.txt
```

---

## 5. Make Targets Reference

| Target | Description |
|---|---|
| `make verify` | Runs the full verification pipeline: lint, typecheck, pytest, node tests, security audits, and generates `docs/TEST_REPORT.md`. |
| `make quality` | Audits cyclomatic complexity with Radon and docstring coverage with Interrogate, updating `docs/CODE_QUALITY.md`. |
| `make test` | Runs the hermetic pytest suite with coverage enforcement (`--cov-fail-under=95`). |
| `make test-js` | Runs frontend i18n key parity tests using Node's native test runner. |
| `make lint` | Validates code formatting and rules across `app`, `tests`, and `scripts`. |
| `make typecheck` | Runs strict static type checking with Mypy (`mypy app`). |
| `make security` | Runs Bandit static security analysis and `pip-audit` CVE vulnerability scan. |
| `make a11y` | Runs Axe-Core 4.10.2 automated WCAG 2.2 AA audit via Playwright across 5 states. |
| `make e2e` | Runs Playwright multi-language browser journey. |
| `make bench` | Runs engine throughput and static bundle size benchmarks. |
| `make report` | Regenerates `docs/TEST_REPORT.md` with live benchmark measurements. |
| `make install` | Installs runtime and development dependencies into `.venv`. |
