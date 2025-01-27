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

## Features

- Generic, type-safe data processing pipeline framework
- Support for both sync and async operations
- Parallel execution strategies for improved performance
- Built-in configuration management using Pydantic
- Clean, modular architecture that's easy to extend
- Comprehensive error handling and monitoring
- Stream processing capabilities

## Installation

```bash
pip install rivusio
```

## Quick Start

```python
from typing import Dict, List
from rivusio import AsyncBasePipe, SyncBasePipe, AsyncPipeline
from rivusio.core.parallel import ExecutionStrategy

# Async pipe example
class FilterPipe(AsyncBasePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        return {k: v for k, v in data.items() if v > 100}

# Sync pipe example
class TransformPipe(SyncBasePipe[Dict, List]):
    def process(self, data: Dict) -> List:
        return list(data.values())

# Create pipeline using >> operator
pipeline = AsyncPipeline([FilterPipe(), TransformPipe()])

# Process single item
data = {"a": 150, "b": 50, "c": 200}
result = await pipeline(data)  # [150, 200]

# Process multiple items in parallel
async with pipeline:
    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL)
    batch = [
        {"a": 150, "b": 50, "c": 200},
        {"x": 300, "y": 75, "z": 400}
    ]
    results = await pipeline.execute_parallel(batch)
```

## Documentation

For complete documentation, visit [https://rivusio.readthedocs.io](https://rivusio.readthedocs.io)

## License

MIT License - see LICENSE file for details
