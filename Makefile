.PHONY: lint test typecheck check serve clean

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
	poetry run uvicorn stock_adviser.server:app --host 0.0.0.0 --port 8000 --reload

# Remove generated files
clean:
	rm -rf dist/ build/ .mypy_cache/ .pytest_cache/ **/__pycache__/
