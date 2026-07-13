# Business Intelligence Search Engine — developer operations
# One-word operations so contributors never memorize tool invocations.

.DEFAULT_GOAL := help
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

LINT_PATHS := src tests config

.PHONY: help venv install lint format typecheck arch test cov check up down migrate serve clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

$(VENV): ## Create the virtual environment
	python3 -m venv $(VENV)

venv: $(VENV) ## Alias for creating the venv

install: $(VENV) ## Install the package + dev tooling (editable)
	$(PIP) install -U pip
	$(PIP) install -e ".[dev]"

lint: ## Lint with ruff (check only)
	$(VENV)/bin/ruff check $(LINT_PATHS)

format: ## Auto-format with ruff
	$(VENV)/bin/ruff format $(LINT_PATHS)
	$(VENV)/bin/ruff check --fix $(LINT_PATHS)

typecheck: ## Static type-check with mypy
	$(VENV)/bin/mypy src config

arch: ## Enforce Clean Architecture dependency rule
	$(VENV)/bin/lint-imports

test: ## Run the test suite
	$(VENV)/bin/pytest

cov: ## Run tests with coverage
	$(VENV)/bin/pytest --cov=bise --cov-report=term-missing

check: lint typecheck arch test ## Run all quality gates (what CI runs)

up: ## Start local Postgres + Redis
	docker compose up -d

down: ## Stop local services
	docker compose down

migrate: ## Apply database migrations (alembic upgrade head)
	$(VENV)/bin/alembic upgrade head

serve: ## Run the API locally with autoreload
	$(VENV)/bin/uvicorn bise.presentation.api.main:app --reload

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
