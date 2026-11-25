# SaansPlan Automation & Verification Scripts

This directory contains standalone scripts organized into functional suites:

## Directory Structure

- `scripts/verify/`: Quality, verification, accessibility, performance, and consistency checks:
  - `check_docs_consistency.py`: Validates all backticked paths, Makefile targets, and Markdown links across `docs/` and root `.md` files.
  - `a11y.py`: Automated accessibility verification runner using Axe-core.
  - `e2e.py`: End-to-end multi-locale flow verification across English, Hinglish, and Hindi.
  - `bench.py`: Engine and API latency benchmarks measuring p50/p95 against budgets.
  - `verify_fake_key.py`: Confirms graceful deterministic template fallback on missing or invalid API keys.
  - `verify_lighthouse.py`: Audits static markup against Lighthouse standards.
  - `verify_live.py`: Probes live deployment endpoints for latency and security headers.
- `scripts/reports/`: Metrics aggregation and markdown documentation generators:
  - `report.py`: Aggregates test counts, coverage, bundle size, and benchmark results into `docs/TEST_REPORT.md`.
  - `quality_report.py`: Computes Radon complexity, maintainability, type coverage, and linters into `docs/CODE_QUALITY.md`.

## Execution

Scripts can be executed via the root `Makefile`:
```bash
make bench      # Run engine performance benchmarks
make a11y       # Run accessibility checks
make e2e        # Run end-to-end multi-locale journeys
make report     # Generate docs/TEST_REPORT.md
make quality    # Generate docs/CODE_QUALITY.md
make verify     # Run complete verification suite
```
Or directly using Python:
```bash
python3 scripts/verify/check_docs_consistency.py
python3 scripts/reports/quality_report.py
```
