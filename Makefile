.PHONY: help install test lint format clean docs build publish docker-test docker-up docker-down test-unit test-integration test-watch update-deps

help:  ## Show this help menu
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "%-30s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

install:  ## Install the package and dependencies
	poetry install

test:  ## Run all tests with coverage
	poetry run pytest tests/ --cov=rivusio --cov-report=term-missing

test-unit:  ## Run only unit tests
	poetry run pytest tests/test_rivusio -v

test-watch:  ## Run tests in watch mode (requires pytest-watch)
	poetry run ptw tests/ --onpass "echo 'All tests passed!'" --onfail "echo 'Tests failed!'"

update-deps:  ## Update dependencies and regenerate lock file
	poetry update
	poetry lock --no-update

lint:  ## Run code linting
	poetry run ruff src/rivusio tests/
	poetry run mypy src/rivusio tests/

format:  ## Format code
	poetry run ruff --fix .

clean:  ## Clean up build artifacts
	rm -rf dist/
	rm -rf build/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf site/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

docs:  ## Build documentation
	poetry install --with docs
	poetry run mkdocs build

docs-serve:  ## Serve documentation locally
	poetry run mkdocs serve

build:  ## Build package
	poetry build

publish:  ## Publish package to PyPI
	poetry publish

cache-purge:  ## Clean up Poetry cache
	poetry cache clear . --all
	rm -rf ~/Library/Caches/pypoetry
	rm -rf ~/.cache/pypoetry