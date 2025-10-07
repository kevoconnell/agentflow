.PHONY: help install lint format test clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install package with dev dependencies"
	@echo "  make lint       - Run ruff linter"
	@echo "  make format     - Auto-fix linting issues with ruff"
	@echo "  make typecheck  - Run mypy type checker"
	@echo "  make test       - Run pytest tests"
	@echo "  make clean      - Clean build artifacts"

install:
	pip install -e ".[dev]"

lint:
	ruff check src/

format:
	ruff check --fix src/
	ruff format src/

test:
	pytest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/

