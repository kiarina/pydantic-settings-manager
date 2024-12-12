.PHONY: format lint test clean build publish

format:
	poetry run black .
	poetry run isort .

lint:
	poetry run ruff .
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

build: clean
	poetry build

publish: build
	poetry publish
