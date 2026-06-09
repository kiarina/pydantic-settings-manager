.PHONY: format lint test clean build publish upgrade
.DEFAULT_GOAL := build

init:
	mise run setup

update:
	uv sync --all-extras --all-groups

upgrade:
	mise run upgrade --sync

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

upgrade:
	@echo "⬆️  Upgrading dependencies..."
	uv lock --upgrade
	@echo "✅ Dependencies upgraded successfully!"
	@echo ""
	@echo "💡 Next steps:"
	@echo "   - Sync dependencies: uv sync --all-extras --all-groups"
	@echo "   - Or use mise: mise run upgrade --sync"
