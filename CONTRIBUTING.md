# Contributing to Jules Idea Automation

Thanks for your interest in contributing! This guide will help you get started.

## Getting Started

```bash
# Clone the repository
git clone https://github.com/julesjewels-ai/jules-idea-automation.git
cd jules-idea-automation

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install dev dependencies
pip install pytest black isort flake8
```

## Running Tests

All changes must pass the test suite before merging:

```bash
python -m pytest tests/ -v
```

## Code Style

This project uses **Black** for formatting and **isort** for import ordering:

```bash
# Format code
black --line-length 120 .

# Sort imports
isort --profile black --line-length 120 .

# Lint
flake8 src/ tests/
```

## Pull Request Process

1. **Fork** the repository and create a feature branch from `main`.
2. **Write tests** for any new functionality.
3. **Run the full test suite** to make sure nothing is broken.
4. **Format your code** with Black and isort before committing.
5. **Open a PR** with a clear description of your changes.

## Reporting Issues

- Use GitHub Issues to report bugs or request features.
- Include steps to reproduce for bug reports.
- Check existing issues before opening a new one.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
