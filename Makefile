export PATH := $(CURDIR)/.venv/bin:$(PATH)

.PHONY: install lint typecheck test test-js e2e a11y security bench report quality verify
install:
	python3 -m venv .venv || true
	.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
lint:
	ruff format --check app tests scripts
	ruff check app tests scripts
typecheck:
	mypy app
test:
	pytest
test-js:
	node --test app/static/tests/*.test.js
e2e:
	python3 scripts/e2e.py
a11y:
	python3 scripts/a11y.py
security:
	bandit -q -r app
	pip-audit -r requirements.txt
bench:
	python3 scripts/bench.py
report:
	python3 scripts/report.py
quality:
	python3 scripts/quality_report.py
verify: lint typecheck test test-js security report
