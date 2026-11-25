# Contributing to SaansPlan

Thank you for contributing to SaansPlan. Please adhere to the following engineering standards and policies:

---

## 1. Repository & Branching Policy

- **Single Branch Enforcement:** The repository operates strictly on a single branch (`main`). Do not create or push feature branches, release branches, or PR branches.
- **No Automated Branch Bots:** Do not configure Dependabot or any bot that automatically creates branches or PRs.
- **Zero Secret Commits:** Never commit `.env`, `GROQ_API_KEY`, API tokens, personal routine logs, screenshots, or `.venv` virtual environments.

---

## 2. Conventional Commit Standards

All commits to `main` must use standard Conventional Commits:
- `feat(...)`: New user-facing capabilities or modules.
- `fix(...)`: Bug fixes or algorithmic corrections.
- `refactor(...)`: Internal refactoring with identical external behaviour.
- `test(...)`: Adding, boosting, or updating test suites.
- `docs(...)`: Documentation updates, architecture guides, reports.
- `sec(...)`: Security hardening, headers, prompt injection defenses.
- `chore(...)`: Routine housekeeping tasks.

---

## 3. Local Development & Verification Commands

All development verification is standardized via the project `Makefile`. Before pushing any commit to `main`, run `make verify`:

| Target | Command | Description |
|---|---|---|
| `make verify` | `lint typecheck test test-js security report` | Runs the full verification pipeline before pushing. |
| `make quality` | `python3 scripts/quality_report.py` | Audits cyclomatic complexity with Radon and docstring coverage with Interrogate. |
| `make test` | `pytest` | Runs the hermetic pytest suite with 95% coverage enforcement (`--cov-fail-under=95`). |
| `make test-js` | `node --test app/static/tests/*.test.js` | Runs frontend i18n key parity and script integrity tests. |
| `make lint` | `ruff format --check && ruff check` | Checks formatting and code style across `app`, `tests`, and `scripts`. |
| `make typecheck` | `mypy app` | Runs strict static type checking across all 46 Python source files. |
| `make security` | `bandit -q -r app && pip-audit -r requirements.txt` | Runs static AST security analysis and checks dependencies for CVEs. |
| `make bench` | `python3 scripts/bench.py` | Benchmarks engine execution latency (< 50 ms budget) and static bundle size (< 60 KB budget). |
| `make a11y` | `python3 scripts/a11y.py` | Runs Axe-Core 4.10.2 automated WCAG 2.2 AA audit across all UI states and languages. |
| `make e2e` | `python3 scripts/e2e.py` | Runs automated Playwright multi-language browser journey. |
| `make report` | `python3 scripts/report.py` | Regenerates `docs/TEST_REPORT.md` with live benchmark measurements. |
| `make install` | `pip install -r requirements.txt -r requirements-dev.txt` | Installs runtime and development dependencies in `.venv`. |
