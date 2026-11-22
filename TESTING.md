# Testing SaansPlan

Run `make test` for pytest-cov and the 90% overall coverage gate. Engine coverage is tracked in pytest-cov output and is targeted at 95%+.

## Hermetic policy

Tests use mocks for Open-Meteo and Groq. A fresh checkout needs no `.env`, real key or network. The public API remains tested through FastAPI TestClient.

## Suites

- `tests/unit`: pure engine and utility properties
- `tests/api`: endpoint contracts and stable error envelopes
- `tests/security`: headers, prompt defence and input limits
- `tests/a11y`: static markup and accessibility invariants
- `tests/performance`: benchmark budgets
- `tests/e2e`: browser flow via Playwright outside the repository

## Commands

- `make lint`
- `make typecheck`
- `make test`
- `make test-js`
- `make a11y`
- `make security`
- `make verify`
