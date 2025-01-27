# Rivusio

[![codecov](https://codecov.io/gh/zbytealchemy/rivusio/branch/main/graph/badge.svg)](https://codecov.io/gh/zbytealchemy/rivusio)
[![PyPI version](https://badge.fury.io/py/rivusio.svg)](https://badge.fury.io/py/rivusio)
[![Documentation Status](https://readthedocs.org/projects/rivusio/badge/?version=latest)](https://rivusio.readthedocs.io/en/latest/?badge=latest)
[![Python versions](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/github/license/zbytealchemy/rivusio)](https://github.com/zbytealchemy/rivusio/blob/main/LICENSE)
[![Tests](https://github.com/zbytealchemy/rivusio/actions/workflows/test.yml/badge.svg)](https://github.com/zbytealchemy/rivusio/actions/workflows/test.yml)
[![Downloads](https://static.pepy.tech/badge/rivusio/month)](https://pepy.tech/project/rivusio)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type Checking: mypy](https://img.shields.io/badge/type%20checking-mypy-blue)](http://mypy-lang.org/)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

A blazing-fast, type-safe data processing pipeline framework in Python, designed for seamless integration of both synchronous and asynchronous operations, complete with robust parallel execution for ultimate performance and scalability.

## 🚀 Key Features

- **Type Safety**: Comprehensive type hints and runtime validation
- **Flexible Processing**: Support for both sync and async operations
- **High Performance**: Parallel execution strategies and optimized processing
- **Stream Processing**: Built-in support for various windowing strategies
- **Robust Error Handling**: Configurable retries and error recovery
- **Monitoring**: Built-in metrics collection and monitoring
- **Configuration**: Type-safe configuration using Pydantic
- **Extensible**: Plugin system for custom components

## 🛠️ Installation

```bash
pip install rivusio
```

## 🎯 Quick Start

```python
from typing import Dict, List
from rivusio import AsyncBasePipe, SyncBasePipe, AsyncPipeline

# Define a simple transformation pipe
class NumberFilterPipe(AsyncBasePipe[Dict[str, int], List[int]]):
    async def __call__(self, data: Dict[str, int]) -> List[int]:
        return [v for v in data.values() if v > 100]

# Create and use a pipeline
async def main():
    pipeline = AsyncPipeline([NumberFilterPipe()])
    
    # Process data
    data = {"a": 150, "b": 50, "c": 200}
    result = await pipeline(data)  # [150, 200]
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 📚 Documentation

Visit our [comprehensive documentation](https://rivusio.readthedocs.io) for:
- Detailed guides and tutorials
- API reference
- Best practices
- Advanced examples
- Configuration options

## 🔧 Development Setup

```bash
# Clone the repository
git clone https://github.com/zbytealchemy/rivusio.git
cd rivusio

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Build documentation
poetry install --with docs
make docs
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Code of Conduct
- Development process
- Pull request guidelines
- Testing requirements

## 📋 Requirements

- Python 3.10+
- Poetry for dependency management
- Git for version control

## 📈 Performance

Rivusio is designed for high performance:
- Efficient batch processing
- Parallel execution capabilities
- Optimized stream processing
- Minimal overhead

## 🔒 Security

- Regular security audits
- Type-safe operations
- Input validation
- Comprehensive testing

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Special thanks to all [contributors](https://github.com/zbytealchemy/rivusio/graphs/contributors) who have helped make Rivusio better.

---

Built with ❤️ by [ZbyteAlchemy](https://github.com/zbytealchemy)
