# Test & Verification Report

Generated automatically on: `2026-11-24 09:56:03 UTC`

## System Verification Summary

| Category | Target / Requirement | Measured Result | Status |
|---|---|---|---|
| **Engine Execution Speed** | < 50 ms for 6-member family | `1.39 ms` | ✅ PASS |
| **Interpolation Throughput** | 1000 runs < 200 ms | `43.71 ms` | ✅ PASS |
| **Static Bundle Size** | < 60 KB gzipped | `29.7 KB` (raw: 92.43 KB) | ✅ PASS |
| **Overall Test Coverage** | ≥ 90% enforced by pyproject | `91.18%` (124 passed) | ✅ PASS |
| **Engine Test Coverage** | ≥ 95% target | `95%+` | ✅ PASS |
| **Hermetic Execution** | No secrets & no network required | Hermetic tests pass cleanly | ✅ PASS |
| **Axe Accessibility Audit** | 0 WCAG 2.2 AA violations | 0 violations (43 initial, 56 populated) | ✅ PASS |
| **Reflow (WCAG 1.4.10)** | 360 px width without horizontal scroll | Zero horizontal overflow | ✅ PASS |
| **Prompt Injection Defense** | Multi-lingual adversarial corpus | 25 injection strings blocked | ✅ PASS |
| **Medical Safety Redirect** | 100% redirect on symptoms/meds | Verified clinical safety fallback | ✅ PASS |
| **Security Audits** | Bandit zero issues, pip-audit zero vulns | Clean automated scan | ✅ PASS |

## Test Suite Breakdown

- **Engine Unit Tests (`tests/unit/engine/`):**
  - CPCB PM2.5 category breakpoints against official Gazette/MoEFCC standards.
  - Physical inhaled PM2.5 dosage (micrograms) using EPA Exposure Factors Handbook ventilation rates.
  - ±25% uncertainty bounds on all physical dosage estimates.
  - 5-day smog forecast engine with midday ventilation and surface wind stagnation detection.
  - Cleaner Day routine optimizer preserving fixed commitments while shifting flexible outdoor exposure.
  - CO2e and INR cost models with budget-tier filtering (`free`, `under_500`, `under_5000`, `any`).
  - Indoor module (AHAM CADR 2/3 sizing rule, DIY box fan filter instructions, room checklists).

- **API & Endpoint Tests (`tests/api/`):**
  - `/api/plan`: Validation envelope (422), 12-member limit, city bounding, routine simulation.
  - `/api/ask`: Grounded QA with zero raw JSON keys and clinical medical redirection.
  - `/health` & `/api/health`: Zero-dependency readiness probes.
  - `/api/geocode`: Open-Meteo city search proxy with strict parameter validation.

- **Security & A11y Tests (`tests/security/`, `tests/a11y/`, `scripts/`):**
  - Prompt injection corpus in English, Hinglish, and Hindi.
  - Real client IP resolution with reverse-proxy trust guards.
  - Strict Content Security Policy (`default-src 'self'`, no unsafe-inline, no unsafe-eval).
  - Playwright and Axe-Core automated WCAG 2.2 AA validation (`scripts/a11y.py`).
  - End-to-end multi-language user journey (`scripts/e2e.py`).
  - Node.js native test runner for 100% i18n key parity and Devanagari script integrity (`app/static/tests/`).

## Verification Commands

```bash
make verify      # Runs lint, typecheck, pytest with coverage, JS unit tests, security, and report
make test        # Runs hermetic pytest suite with coverage enforcement
make test-js     # Runs frontend i18n unit tests
make typecheck   # Runs strict mypy
make security    # Runs bandit and pip-audit
make e2e         # Runs Playwright full journey across English, Hinglish, Hindi
make a11y        # Runs Axe-core WCAG 2.2 AA audit
make bench       # Runs engine latency and bundle benchmarks
```
