# Contributing to Rivusio

We love your input! We want to make contributing to Rivusio as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Local Development

Set up your development environment:

```bash
# Clone the repository
git clone https://github.com/zbytealchemy/rivusio.git
cd rivusio

# Install dependencies
poetry install

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make coverage
```

## Code Style

We use `black` for Python code formatting and `isort` for import sorting. Both tools are configured in `pyproject.toml`.

```bash
# Format code
make format

# Check code style
make lint
```

## Documentation

We use MkDocs with the Material theme for documentation:

```bash
# Install documentation dependencies
poetry install --with docs

# Build documentation
make docs

# Serve documentation locally
make docs-serve
```

## Pull Request Process

1. Update the README.md with details of changes to the interface
2. Update the docs with any new API changes
3. The PR may be merged once you have the sign-off of two other developers
4. Make sure all tests pass and code style checks are satisfied

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issue tracker](https://github.com/zbytealchemy/rivusio/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/zbytealchemy/rivusio/issues/new).

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
