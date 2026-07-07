# MotoQuant Pro — developer entry point.
#
# The one interface every contributor (human or AI) should use. It encodes the
# same commands CI runs, so "green locally" ≈ "green in CI". Run `make` (or
# `make help`) to see everything.
#
# Design rule: every target here must also be what CI does, and vice-versa —
# they must not drift. If you add a CI step, add a make target and reference it.

PY ?= python3
PYTEST ?= $(PY) -m pytest
FAST_TESTS := tests/test_validation.py tests/test_scraper.py \
              tests/test_two_stroke.py tests/test_compatibility.py \
              tests/test_submodel_kaizen.py tests/test_category_dispatch.py

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@echo "MotoQuant Pro — make targets:"
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Before opening a PR:  make check"
	@echo "State of the world:   make health"

# ── Setup ──────────────────────────────────────────────────────────────────
.PHONY: install
install: ## Install runtime + dev dependencies and the package (editable)
	$(PY) -m pip install -r requirements-api.txt -r requirements-dev.txt
	$(PY) -m pip install -e .

.PHONY: db
db: ## Initialise + seed a fresh dev database (motoquant.db ships seeded)
	$(PY) -m motoquant.run db init
	$(PY) -m motoquant.run db seed

# ── Quality gates (mirror CI) ──────────────────────────────────────────────
.PHONY: lint
lint: ## Ruff lint
	ruff check motoquant/ tests/ scripts/

.PHONY: format
format: ## Ruff auto-format (writes changes)
	ruff format .

.PHONY: fmt-check
fmt-check: ## Ruff format check (no writes) — what CI enforces
	ruff format --check .

.PHONY: baselines
baselines: ## Assert the K5/R1/Hayabusa reference baselines are bit-identical
	$(PY) scripts/check_baselines.py

.PHONY: audit
audit: ## Check headline stats (bike/part/tire counts) are in sync sitewide
	$(PY) scripts/audit_headline_stats.py

.PHONY: health
health: ## Fast state-of-the-world dashboard (baselines, lint, catalog, secrets)
	$(PY) scripts/health_check.py

# ── Tests ──────────────────────────────────────────────────────────────────
.PHONY: test
test: ## Full pytest suite (~25 min; what a PR must pass — serial, matches CI)
	$(PYTEST) tests/ -q

.PHONY: test-fast
test-fast: ## Focused fast subset (~3 min) — run this while iterating
	$(PYTEST) $(FAST_TESTS) -q

.PHONY: test-slow
test-slow: ## Slow integration tests (full physics on parts, recommendations)
	MOTOQUANT_SLOW_TESTS=1 $(PYTEST) tests/test_recommendations.py -q

# ── The pre-PR gate ────────────────────────────────────────────────────────
.PHONY: check
check: lint fmt-check baselines test-fast ## Fast pre-PR gate (lint+fmt+baselines+fast tests)
	@echo ""
	@echo "✓ Fast gate passed. Run 'make test' for the full suite before opening a PR."

# ── Run the product ────────────────────────────────────────────────────────
.PHONY: api
api: ## Run the FastAPI backend locally on :8000
	uvicorn motoquant.api:app --reload --port 8000

.PHONY: web-install
web-install: ## Install the Next.js frontend deps
	cd web && npm install

.PHONY: web-dev
web-dev: ## Run the Next.js frontend against a local API on :8000
	cd web && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

.PHONY: web-build
web-build: ## Production build of the frontend (what Vercel runs)
	cd web && npm run build

# ── Housekeeping ───────────────────────────────────────────────────────────
.PHONY: clean
clean: ## Remove Python caches and build artefacts
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache *.egg-info build dist coverage.xml
