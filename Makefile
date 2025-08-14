.PHONY: format lint test clean build publish update-deps
.DEFAULT_GOAL := build

format:
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run mypy .

test:
	uv run pytest --cov=pydantic_settings_manager tests/

clean:
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

build: format lint test clean
	uv build

publish: build
	uv publish

update-deps:
	@echo "Updating dependencies..."
	uv lock --upgrade
	@echo "Dependencies updated successfully!"
	@echo ""
	@echo "To sync the updated dependencies, run:"
	@echo "  uv sync --group dev"
