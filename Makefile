.PHONY: lint test typecheck check clean

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

# Remove generated files
clean:
	rm -rf dist/ build/ .mypy_cache/ .pytest_cache/ **/__pycache__/
