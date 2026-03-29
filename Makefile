.PHONY: lint test typecheck check serve frontend-install frontend-dev dev clean

# Format and lint (via pre-commit)
lint:
	pre-commit run --all-files

# Unit tests
test:
	poetry run pytest tests/ -v --tb=short -q

# Static type checking
typecheck:
	poetry run mypy src/stock_adviser/ || true

# Run all fast checks — the single command after every change
check: lint test typecheck

# Run the API server
serve:
	poetry run uvicorn stock_adviser.server:app --host 0.0.0.0 --port 8881 --reload

# Install frontend dependencies
frontend-install:
	cd frontend && npm install

# Run frontend dev server
frontend-dev:
	cd frontend && npm run dev

# Run both backend and frontend (requires two terminals)
dev:
	@echo "Start in two terminals:"
	@echo "  Terminal 1: make serve"
	@echo "  Terminal 2: make frontend-dev"

# Remove generated files
clean:
	rm -rf dist/ build/ .mypy_cache/ .pytest_cache/ **/__pycache__/
