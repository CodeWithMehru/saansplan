# Testing & Verification Guide

This document describes the test architecture, hermetic execution policy, and step-by-step reproduction instructions for SaansPlan.

---

## 1. Hermetic Testing Policy

Every test in the `tests/` suite is **100% hermetic**:
- **No API keys required:** Tests execute cleanly in environments with no `.env` file and no `GROQ_API_KEY` set.
- **No live network required:** All external network calls (Open-Meteo, Groq) are intercepted using unittest mocks and predefined golden payloads.
- **Strict coverage enforcement:** `pyproject.toml` enforces a minimum 90% overall line and branch coverage threshold (`--cov-fail-under=90`). A plain `pytest` run fails if coverage drops below this threshold.

---

## 2. Test Suites Overview

| Suite Directory | Description | Key Areas Covered |
|---|---|---|
| `tests/unit/engine/` | Pure deterministic domain calculations | CPCB PM2.5 category breakpoints, physical inhaled dosage ($\mu\text{g}$) with uncertainty bands, 5-day smog forecast, Cleaner Day routine optimizer, carbon emissions & INR cost models, AHAM CADR sizing, indoor module. |
| `tests/unit/` | Unit tests for infrastructure components | Bounded TTL cache (LRU eviction, expiration, locking), input guard, LLM branch fallback, transport error resilience. |
| `tests/api/` | FastAPI endpoint contracts | `/api/plan` schema validation, 422 error envelopes, 12-member household limit, `/api/ask` grounded QA, `/health` and `/api/health` probes. |
| `tests/security/` | Security and adversarial resistance | 25-string multi-lingual prompt injection corpus (English, Hinglish, Hindi), clinical medical redirect guard, reverse proxy client IP validation, strict Content Security Policy. |
| `tests/a11y/` | Accessibility AST markup tests | Single `<h1>` rule, semantic landmarks, form control labels, scoped table headers, zero inline JavaScript event handlers. |
| `app/static/tests/` | Frontend native test runner (`node --test`) | Complete key parity across English, Hinglish, and Hindi translation dictionaries; Devanagari script integrity validation. |
| `scripts/a11y.py` | Automated Axe-Core audit | End-to-end WCAG 2.2 Level AA compliance check across initial, translated, and populated views (0 violations). |
| `scripts/e2e.py` | Playwright end-to-end journey | Automated verification of city search, persona prefilling, plan generation, F10 human-readable labels, and zero console errors. |

---

## 3. Clean Clone Verification

To prove that tests pass independently in a pristine environment with zero ambient state:

```bash
# 1. Clone into a temporary clean directory
git clone git@github.com:CodeWithMehru/saansplan.git /tmp/verify_saansplan
cd /tmp/verify_saansplan

# 2. Verify that no .env exists
[ ! -f .env ] && echo "Clean environment: no .env present"

# 3. Create fresh Python 3.13 venv and install dependencies
python3.13 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

# 4. Run pytest suite (asserts >= 90% coverage)
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

## 4. Make Targets Reference

| Target | Description |
|---|---|
| `make verify` | Runs the full verification pipeline: lint, typecheck, pytest, node tests, security audits, and generates `docs/TEST_REPORT.md`. |
| `make test` | Runs the hermetic pytest suite with coverage enforcement. |
| `make test-js` | Runs frontend i18n key parity tests using Node's native test runner. |
| `make lint` | Validates code formatting and rules across `app`, `tests`, and `scripts`. |
| `make typecheck` | Runs strict static type checking with Mypy. |
| `make security` | Runs Bandit static security analysis and `pip-audit` CVE vulnerability scan. |
| `make a11y` | Runs Axe-Core 4.10.2 automated WCAG 2.2 AA audit via Playwright. |
| `make e2e` | Runs Playwright multi-language browser journey. |
| `make bench` | Runs engine throughput and static bundle size benchmarks. |
| `make report` | Re-generates `docs/TEST_REPORT.md` with live benchmark measurements. |
