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
UV_RUN := uv run --project $(BACKEND_DIR)

.PHONY: backend-install lint format format-check typecheck imports \
        test-unit test-integration test-coverage audit quality-gates \
        dev-backend help

backend-install: ## Sync backend deps into the uv-managed venv
	uv sync --project $(BACKEND_DIR) --extra dev

lint: ## ruff check (lint + security S rules) (QG-001)
	$(UV_RUN) ruff check $(BACKEND_DIR)/src $(BACKEND_DIR)/tests

format: ## ruff format (write) on backend sources
	$(UV_RUN) ruff format $(BACKEND_DIR)/src $(BACKEND_DIR)/tests

format-check: ## ruff format --check (QG-001)
	$(UV_RUN) ruff format --check $(BACKEND_DIR)/src $(BACKEND_DIR)/tests

typecheck: ## mypy strict on domain+application, looser on adapters (QG-001)
	cd $(BACKEND_DIR) && uv run mypy src/viridarium

imports: ## import-linter hexagonal boundary contracts (ARCH-003)
	cd $(BACKEND_DIR) && uv run lint-imports --config pyproject.toml

test-unit: ## pytest unit layer (QG-002, TEST-012)
	$(UV_RUN) pytest $(BACKEND_DIR)/tests -m unit

test-integration: ## pytest integration layer (QG-002, TEST-012)
	$(UV_RUN) pytest $(BACKEND_DIR)/tests -m integration

test-coverage: ## full suite with coverage floor 85 (QG-002)
	$(UV_RUN) pytest $(BACKEND_DIR)/tests \
		--cov=viridarium --cov-report=term-missing \
		--cov-config=$(BACKEND_DIR)/pyproject.toml

audit: ## pip-audit dependency CVE scan (SEC-009)
	# Ignored advisories carry a justification + revisit date inline (SEC-009) and in
	# specs/changes/scaffold-backend/proposal.md.
	# PYSEC-2026-161 (starlette Host-header validation): fix is starlette 1.0.1, which
	# the current FastAPI line does not yet allow; advisory is below the SEC-009 CVSS>7.5
	# block bar and off our critical path (no Host-based URL reconstruction in v1).
	# Revisit 2026-09-01 (or sooner when FastAPI admits starlette >=1.0).
	cd $(BACKEND_DIR) && uv run pip-audit --ignore-vuln PYSEC-2026-161

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

.PHONY: fe-install fe-lint fe-format-check fe-typecheck fe-test fe-build dev-frontend

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

dev-frontend: ## Vite dev server (/api proxied to localhost:8000)
	cd $(FRONTEND_DIR) && npm run dev
