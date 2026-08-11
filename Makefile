.PHONY: help install test test-smoke test-regression test-api test-perf test-a11y test-unit test-headed test-rerun-failed report gen-testcases typecheck lint format-check demo

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "%-18s %s\n", $$1, $$2}'

install: ## Create venv (if needed) and install runtime + dev dependencies, plus browsers
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
	.venv/bin/playwright install --with-deps

test: ## Full suite, all browsers
	pytest --browser chromium --browser firefox --browser webkit

test-smoke: ## Fast subset, tagged smoke
	pytest -m smoke

test-regression: ## Broader negative/edge coverage
	pytest -m regression

test-api: ## API-only specs (no browser)
	pytest tests/api

test-perf: ## Navigation-timing smoke checks
	pytest tests/performance

test-a11y: ## axe-core accessibility checks
	pytest tests/accessibility

test-unit: ## Pure-logic unit tests, no browser
	pytest tests/unit

test-headed: ## Any of the above with --headed for local debugging
	pytest --headed

test-rerun-failed: ## Re-run only the tests that failed last run (reports/failed_tests.log)
	@test -s reports/failed_tests.log || (echo "No reports/failed_tests.log -- run a suite first" && exit 1)
	pytest -k "$$(cat reports/failed_tests.log)"

report: ## Open the last HTML report
	open reports/html/index.html

gen-testcases: ## Regenerate test-cases/test-cases.xlsx
	python test-cases/generate_xlsx.py

typecheck: ## mypy --strict
	mypy .

lint: ## ruff check + POM-boundary enforcement
	ruff check .
	python scripts/check_pom_boundary.py

format-check: ## ruff format --check
	ruff format --check .

demo: ## Record a video of the login -> add-to-cart -> place-order flow
	python demo/record_demo.py
