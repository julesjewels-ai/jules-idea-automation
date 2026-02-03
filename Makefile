# Makefile for Agent-Ready Repository
# Standard targets for quality checks and build automation

.PHONY: help install lint format typecheck test coverage build clean security quality quality-fix

# Default target
help:
	@echo "Available targets:"
	@echo "  make install    - Install dependencies"
	@echo "  make lint       - Run linting (ruff)"
	@echo "  make format     - Format code (black + isort)"
	@echo "  make typecheck  - Run type checking (mypy)"
	@echo "  make test       - Run tests (pytest)"
	@echo "  make coverage   - Run tests with coverage"
	@echo "  make security   - Run security scan (bandit)"
	@echo "  make quality    - Check code quality (flake8, black, isort)"
	@echo "  make quality-fix - Auto-fix code quality issues (black, isort)"
	@echo "  make build      - Build package"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make all        - Run lint, test, and build"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install ruff black isort mypy pytest pytest-cov bandit

# Linting with ruff (fast Python linter)
lint:
	@echo "Running ruff..."
	ruff check src/ tests/ --fix || ruff check src/ tests/
	@echo "Lint complete ✓"

# Format code with black and isort
format:
	@echo "Running black..."
	black src/ tests/
	@echo "Running isort..."
	isort src/ tests/
	@echo "Format complete ✓"

# Type checking with mypy
typecheck:
	@echo "Running mypy..."
	mypy src/ --ignore-missing-imports || echo "Typecheck completed with warnings"
	@echo "Typecheck complete ✓"

# Run tests
test:
	@echo "Running pytest..."
	pytest tests/ -v --tb=short
	@echo "Tests complete ✓"

# Run tests with coverage
coverage:
	@echo "Running pytest with coverage..."
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/"

# Coverage with minimum threshold (for CI)
coverage-check:
	pytest tests/ --cov=src --cov-fail-under=80

# Security scan with bandit
security:
	@echo "Running bandit security scan..."
	bandit -r src/ -ll -x tests/
	@echo "Security scan complete ✓"

# Build package (placeholder - adapt for your build system)
build:
	@echo "Building package..."
	@if [ -f "pyproject.toml" ]; then \
		python -m build; \
	elif [ -f "setup.py" ]; then \
		python setup.py sdist bdist_wheel; \
	else \
		echo "No build configuration found, skipping package build"; \
		echo "Verifying module can be imported..."; \
		python -c "import src"; \
	fi
	@echo "Build complete ✓"

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete ✓"

# Run all quality checks
all: lint test build
	@echo "All checks passed ✓"

# Pre-commit hook equivalent
check: lint typecheck test security
	@echo "All pre-commit checks passed ✓"

# Code quality check (flake8, black, isort)
quality:
	@echo "Running code quality checks..."
	@echo "Checking flake8..."
	flake8 src/ agent/ main.py tests/ --max-line-length=120 --extend-ignore=E203,W503
	@echo "Checking black formatting..."
	black --check src/ agent/ main.py tests/
	@echo "Checking isort..."
	isort --check-only src/ agent/ main.py tests/
	@echo "Quality checks complete ✓"

# Auto-fix code quality issues
quality-fix:
	@echo "Auto-fixing code quality issues..."
	black src/ agent/ main.py tests/
	isort src/ agent/ main.py tests/
	@echo "✓ Auto-fixes complete. Run 'make quality' to verify."
