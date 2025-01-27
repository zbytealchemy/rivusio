# Installation

## Requirements

- Python 3.10 or higher
- Poetry (recommended) or pip

## Using Poetry (Recommended)

```bash
poetry add rivusio
```

## Using pip

```bash
pip install rivusio
```

## Development Installation

To install Rivusio for development:

1. Clone the repository:
```bash
git clone https://github.com/zbytealchemy/rivusio.git
cd rivusio
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Install pre-commit hooks (optional but recommended):
```bash
pre-commit install
```

## Verifying Installation

After installation, you can verify everything is working by running the tests:

```bash
poetry run pytest tests/
```

For more detailed testing options, see our [Development Testing Guide](../development/testing.md).
