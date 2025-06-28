.PHONY: format lint test clean build publish
.DEFAULT_GOAL := build

format:
	poetry run ruff check --fix .

lint:
	poetry run ruff check .
	poetry run mypy .

test:
	poetry run pytest --cov=pydantic_settings_manager tests/

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
	poetry build

publish: build
	poetry publish
