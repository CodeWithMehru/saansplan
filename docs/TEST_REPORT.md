# Test & Verification Report

Generated automatically on: `2026-11-26 08:24:59 UTC`

## System Verification Summary

| Category | Target / Requirement | Measured Result | Status |
|---|---|---|---|
| **Engine Execution Speed** | < 50 ms for 6-member family | `2.47 ms` | ✅ PASS |
| **Interpolation Throughput** | 1000 runs < 200 ms | `44.65 ms` | ✅ PASS |
| **Static Bundle Size** | < 60 KB gzipped | `35.68 KB` (raw: 112.54 KB) | ✅ PASS |
| **Overall Test Coverage** | ≥ 95% enforced by pyproject | `99.32%` (269 passed) | ✅ PASS |
| **Engine Test Coverage** | ≥ 95% target | `99.4%` | ✅ PASS |
| **Hermetic Execution** | No secrets & no network required | Hermetic tests pass cleanly | ✅ PASS |
| **Axe Accessibility Audit** | 0 WCAG 2.2 AA violations | 0 violations (43 initial, 56 populated) | ✅ PASS |
| **Reflow (WCAG 1.4.10)** | 360 px width without horizontal scroll | Zero horizontal overflow | ✅ PASS |
| **Prompt Injection Defense** | Multi-lingual adversarial corpus | 57 injection strings tested and blocked | ✅ PASS |
| **Medical Safety Redirect** | Immediate redirect on symptoms/meds | Tested clinical safety fallback | ✅ PASS |
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
  - Prompt injection corpus in English, Hinglish, and Hindi (57 vectors).
  - Real client IP resolution with reverse-proxy trust guards.
  - Strict Content Security Policy (`default-src 'self'`, no unsafe-inline, no unsafe-eval).
  - Playwright and Axe-Core automated WCAG 2.2 AA validation (`scripts/a11y.py`).
  - End-to-end multi-language user journey (`scripts/e2e.py`).
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
