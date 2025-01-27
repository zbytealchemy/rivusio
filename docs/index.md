# Rivusio

A lightweight, type-safe data transformation framework for Python.

## Features

- **Type Safety**: Built with Python's type hints for better code quality and IDE support
- **Async-First**: Native support for asynchronous processing
- **Composable**: Easy pipeline composition with the `>>` operator
- **Stream Processing**: Built-in support for processing data streams
- **Monitoring**: Comprehensive metrics collection and monitoring
- **Error Handling**: Robust error handling with retries and recovery

## Quick Example

```python
from rivusio import AsyncBasePipe
from typing import Dict, List

class FilterPipe(AsyncBasePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        return {k: v for k, v in data.items() if v > 100}

class TransformPipe(AsyncBasePipe[Dict, List]):
    async def process(self, data: Dict) -> List:
        return list(data.values())

async def main():
    # Create pipeline using >> operator
    pipeline = FilterPipe() >> TransformPipe()

    # Process data
    data = {"a": 150, "b": 50, "c": 200}
    result = await pipeline(data)  # [150, 200]
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Installation

```bash
pip install rivusio
```

## Why Rivusio?

- **Simple but Powerful**: Clean, intuitive API that doesn't get in your way
- **Type-Safe**: Catch errors before they happen with static type checking
- **Production Ready**: Built for reliability with monitoring and error handling
- **Extensible**: Easy to integrate with your existing tools and workflows
- **Well Documented**: Comprehensive documentation and examples

## Next Steps

- Check out the [Quick Start](getting-started/quickstart.md) guide
- Learn about [Basic Concepts](getting-started/concepts.md)
- Browse the [Examples](examples/basic-transformation.md)
- Read the [API Reference](api/core.md)
