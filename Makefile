export PATH := $(CURDIR)/.venv/bin:$(PATH)

.PHONY: help install lint typecheck test test-js check-js check-docs check e2e a11y security bench report quality mutation verify

help: ## Show available Makefile targets and descriptions
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install Python dependencies into local virtual environment
	python3 -m venv .venv || true
	.venv/bin/pip install -r requirements.txt -r requirements-dev.txt

lint: ## Run Python formatting and style linters
	ruff format --check app tests scripts
	ruff check app tests scripts

typecheck: ## Run strict static type checking with mypy
	mypy app

test: ## Run unit and integration test suite with coverage
	pytest --cov=app --cov-report=term-missing --cov-fail-under=95

test-js: ## Run Node.js tests for frontend modules
	node --test tests/js/*.test.js

check-js: ## Run ESLint, Prettier, TypeScript, and HTML validation on frontend assets
	npx --yes eslint@10.15.0 app/static/js/
	npx --yes prettier@3.5.2 --check app/static/ tests/js/
	npx --yes --package=typescript@5.7.3 tsc --noEmit
	npx --yes html-validate app/static/*.html

check-docs: ## Check Markdown consistency, links, paths, and Makefile targets
	python3 scripts/verify/check_docs_consistency.py

check: lint typecheck check-js check-docs ## Run all static analysis, linters, and consistency checks

e2e: ## Run end-to-end multi-locale journey verification
	python3 scripts/verify/e2e.py

a11y: ## Run automated accessibility verification
	python3 scripts/verify/a11y.py

security: ## Run static application security testing and dependency vulnerability scan
	bandit -q -r app
	pip-audit -r requirements.txt
	pip-audit -r requirements.lock.txt --require-hashes

bench: ## Run performance latency benchmarks
	python3 scripts/verify/bench.py

report: ## Generate docs/TEST_REPORT.md from current test and benchmark results
	python3 -m scripts.reports.report

quality: ## Generate docs/CODE_QUALITY.md metrics report
	python3 -m scripts.reports.quality_report

mutation: ## Run mutation testing on engine and guard modules
	mutmut run

verify: check test test-js security report ## Run complete validation pipeline
