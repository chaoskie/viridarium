# Viridarium - quality gates.
#
# One target per gate (QG-001/002), aggregated by `make quality-gates`. The backend
# section below is self-contained; frontend targets are appended by the frontend agent
# in a clearly separated section without touching the backend block.

.DEFAULT_GOAL := help

# ============================================================================
# BACKEND (Python / FastAPI). Owned by the backend agent.
# ============================================================================

BACKEND_DIR := backend
# `uv run` executes inside the backend project venv reproducibly.
# --frozen: the lockfile never re-resolves implicitly (retro 2026-06-11);
# dependency changes require an explicit `uv lock`.
UV_RUN := uv run --frozen --project $(BACKEND_DIR)

.PHONY: backend-install lint format format-check typecheck imports \
        test-unit test-integration test-coverage audit quality-gates \
        dev-backend help

backend-install: ## Sync backend deps into the uv-managed venv
	uv sync --frozen --project $(BACKEND_DIR) --extra dev

lint: ## ruff check (lint + security S rules) (QG-001)
	$(UV_RUN) ruff check $(BACKEND_DIR)/src $(BACKEND_DIR)/tests

format: ## ruff format (write) on backend sources
	$(UV_RUN) ruff format $(BACKEND_DIR)/src $(BACKEND_DIR)/tests

format-check: ## ruff format --check (QG-001)
	$(UV_RUN) ruff format --check $(BACKEND_DIR)/src $(BACKEND_DIR)/tests

typecheck: ## mypy strict on domain+application, looser on adapters (QG-001)
	cd $(BACKEND_DIR) && uv run --frozen mypy src/viridarium

imports: ## import-linter hexagonal boundary contracts (ARCH-003)
	cd $(BACKEND_DIR) && uv run --frozen lint-imports --config pyproject.toml

test-unit: ## pytest unit layer (QG-002, TEST-012)
	$(UV_RUN) pytest $(BACKEND_DIR)/tests -m unit

test-integration: ## pytest integration layer (QG-002, TEST-012)
	$(UV_RUN) pytest $(BACKEND_DIR)/tests -m integration

test-coverage: ## full suite with coverage floor 85 (QG-002)
	$(UV_RUN) pytest $(BACKEND_DIR)/tests \
		--cov=viridarium --cov-report=term-missing \
		--cov-config=$(BACKEND_DIR)/pyproject.toml

audit: ## pip-audit dependency CVE scan (SEC-009)
	# No suppressions: the starlette 1.3.1 bump (via fastapi 0.137) retired the prior
	# PYSEC-2026-161 ignore and cleared CVE-2026-54282/54283/48817/48818 (BUG-006).
	# Any future ignore carries a justification + revisit date inline (SEC-009).
	cd $(BACKEND_DIR) && uv run pip-audit

quality-gates: lint format-check typecheck imports test-coverage audit fe-lint fe-format-check fe-typecheck fe-test ## Run the full mechanical gate, backend + frontend (QG-001)
	@echo "All quality gates passed."

dev-backend: ## Run the backend dev server with reload
	$(UV_RUN) uvicorn viridarium.main:app --reload \
		--app-dir $(BACKEND_DIR)/src --port 8000

help: ## List available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# FRONTEND (React / Vite). Owned by the frontend agent.
# All targets run inside ./frontend via npm and mirror the QG-001 gate.
# ============================================================================

FRONTEND_DIR := frontend

.PHONY: fe-install fe-lint fe-format-check fe-typecheck fe-test fe-build \
        fe-e2e fe-e2e-matrix fe-e2e-install dev-frontend

fe-install: ## Install frontend dependencies (npm ci against the lockfile)
	cd $(FRONTEND_DIR) && npm ci

fe-lint: ## ESLint over the frontend (QG-001)
	cd $(FRONTEND_DIR) && npm run lint

fe-format-check: ## Prettier check (QG-001, FE-006)
	cd $(FRONTEND_DIR) && npm run format:check

fe-typecheck: ## tsc --noEmit under strict flags (QG-001, FE-004)
	cd $(FRONTEND_DIR) && npm run typecheck

fe-test: ## Vitest run (jsdom + Testing Library)
	cd $(FRONTEND_DIR) && npm run test

fe-build: ## Production build (FE-007 budget)
	cd $(FRONTEND_DIR) && npm run build

fe-e2e-install: ## Install the Playwright Chromium browser for the acceptance suite
	cd $(FRONTEND_DIR) && npx playwright install --with-deps chromium

fe-e2e: ## Playwright acceptance suite (TEST-009; boots backend + built frontend)
	cd $(FRONTEND_DIR) && npx playwright test

fe-e2e-matrix: ## Acceptance suite + the release-gated top-5 mobile device matrix
	cd $(FRONTEND_DIR) && E2E_DEVICE_MATRIX=1 npx playwright test

dev-frontend: ## Vite dev server (/api proxied to localhost:8000)
	cd $(FRONTEND_DIR) && npm run dev
