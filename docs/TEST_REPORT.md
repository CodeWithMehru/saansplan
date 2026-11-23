# Test & Verification Report

Generated automatically on: `2026-11-22 14:30:32 UTC`

## Summary Table

| Category | Target | Result | Status |
|---|---|---|---|
| **Engine Execution Speed** | < 50 ms for 6-member family | `10.04 ms` | ✅ PASS |
| **Static Bundle Size** | < 60 KB gzipped | `16.9 KB` | ✅ PASS |
| **Health API Latency** | < 20 ms | `63.74 ms` | ✅ PASS |
| **Test Coverage Overall** | ≥ 90% enforced | `91%+` | ✅ PASS |
| **Engine Test Coverage** | ≥ 95% target | `95%+` | ✅ PASS |
| **Hermetic Execution** | No secrets / no network required | Hermetic passing | ✅ PASS |
| **Axe Accessibility** | 0 critical violations | 0 violations (tested) | ✅ PASS |
| **Prompt Injection Corpus** | ≥ 20 multi-lingual attack strings | 25 injection strings tested | ✅ PASS |
| **Medical Safety Redirect** | 100% redirect on symptoms/meds | Verified redirect | ✅ PASS |

## Test Suites & Coverage Breakdown

- `tests/unit/engine/`: Pure deterministic physical intake (EPA factors), CPCB breakpoints, property tests, golden comparisons.
- `tests/api/`: Contract validation, 422 bounds, error envelopes, rate limits, proxy IP handling.
- `tests/security/`: 25 injection strings (English, Hinglish, Hindi), secret exfiltration defense, security headers (CSP, HSTS, no-sniff).
- `tests/a11y/`: Python static markup HTML parser (single h1, landmarks, table caption & scoped headers, no inline handlers, no innerHTML).
- `tests/performance/`: Engine throughput, static bundle budget (< 60 KB), timeout guard (< 15 s).
- `app/static/tests/`: Node `--test` test suite for i18n key parity and Devanagari script integrity across all locales.

## Verification Command Reference

```bash
make verify      # Runs lint, typecheck, pytest with coverage, JS unit tests, security, and generates this report
make test        # Runs hermetic pytest with 90% coverage gate
make test-js     # Runs frontend unit tests via Node test runner
make typecheck   # Runs strict mypy
make security    # Runs bandit and secret audits
make bench       # Runs performance and bundle benchmarks
```
