# Test & Verification Report

Generated automatically on: `2026-11-27 13:48:32 UTC`

## System Verification Summary

| Category | Target / Requirement | Measured Result | Status |
|---|---|---|---|
| **Engine Execution Speed** | < 50 ms (6 members) | `3.7 ms` | ✅ PASS |
| **Interpolation Throughput** | 1000 runs < 200 ms | `44.39 ms` | ✅ PASS |
| **Static Bundle Size** | < 60 KB gzipped | `39.95 KB` (raw: 126.12 KB) | ✅ PASS |
| **Overall Test Coverage** | ≥ 95% enforced | `99.37%` (275 passed) | ✅ PASS |
| **Engine Test Coverage** | ≥ 95% target | `99.42%` | ✅ PASS |
| **Hermetic Execution** | No secrets/network | Hermetic clean | ✅ PASS |
| **Axe Accessibility Audit** | 0 WCAG 2.2 AA violations | 0 violations (56 rules) | ✅ PASS |
| **Reflow (WCAG 1.4.10)** | 360 px without scroll | Zero overflow | ✅ PASS |
| **Prompt Injection Defense** | Multilingual corpus | 57 blocked | ✅ PASS |
| **Medical Safety Redirect** | Immediate clinical safety | Redirect active | ✅ PASS |
| **Security Audits** | Bandit & pip-audit | Clean scan | ✅ PASS |

## Test Suite Breakdown

- **Engine Unit Tests (`tests/unit/engine/`):**
  - CPCB PM2.5 category breakpoints against official Gazette/MoEFCC standards.
  - Physical inhaled PM2.5 dosage (micrograms) using EPA Exposure Factors Handbook rates.
  - ±25% uncertainty bounds on all physical dosage estimates.
  - 5-day smog forecast engine with midday ventilation and surface wind stagnation detection.
  - Cleaner Day routine optimizer shifting flexible outdoor exposure.
  - CO2e and INR cost models with budget-tier filtering (`free`, `under_500`, etc.).
  - Indoor module (AHAM CADR 2/3 sizing rule, DIY box fan filter instructions).

- **API & Endpoint Tests (`tests/api/`):**
  - `/api/plan`: Validation envelope (422), 12-member limit, city bounding, routine simulation.
  - `/api/ask`: Grounded QA with zero raw JSON keys and clinical medical redirection.
  - `/health` & `/api/health`: Zero-dependency readiness probes.
  - `/api/geocode`: Open-Meteo city search proxy with strict parameter validation.

- **Security & A11y Tests (`tests/security/`, `tests/a11y/`, `scripts/verify/`):**
  - Prompt injection corpus in English, Hinglish, and Hindi (57 vectors).
  - Real client IP resolution with reverse-proxy trust guards.
  - Strict Content Security Policy (`default-src 'self'`, no unsafe-inline, no unsafe-eval).
  - Playwright and Axe-Core automated WCAG 2.2 AA validation (`scripts/verify/a11y.py`).
  - End-to-end multi-language user journey (`scripts/verify/e2e.py`).
  - Node.js native test runner for i18n key parity and Devanagari script integrity (`tests/js/`).

## Verification Commands

```bash
make verify      # Runs lint, typecheck, pytest with coverage, JS unit tests, security, and report
make quality     # Runs Radon complexity and Interrogate docstring coverage audit
make test        # Runs hermetic pytest suite with coverage enforcement
make test-js     # Runs frontend i18n unit tests
make typecheck   # Runs strict mypy
make security    # Runs bandit and pip-audit
make e2e         # Runs Playwright full journey across English, Hinglish, Hindi
make a11y        # Runs Axe-core WCAG 2.2 AA audit
make bench       # Runs engine latency and bundle benchmarks
```
