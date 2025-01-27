# Quick Start

This guide will help you get started with Rivusio by walking through a simple example.

## Installation

Install Rivusio using pip:

```bash
pip install rivusio
```

## Basic Usage

### 1. Create a Simple Pipe

Let's create a pipe that filters dictionary values:

```python
from rivusio import BasePipe
from typing import Dict

class FilterPipe(BasePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        return {k: v for k, v in data.items() if v > 100}
```

### 2. Process Data

Use the pipe to process some data:

```python
filter_pipe = FilterPipe()

data = {"a": 150, "b": 50, "c": 200}
result = await filter_pipe(data)
print(result)  # {"a": 150, "c": 200}
```

### 3. Compose Pipes

Create a pipeline by composing multiple pipes:

```python
from rivusio import AsyncPipeline, BasePipe
from typing import Dict, List

class TransformPipe(BasePipe[Dict, List]):
    async def process(self, data: Dict) -> List:
        return list(data.values())

# Compose pipes using >>
pipeline = AsyncPipeline([FilterPipe()]) >> TransformPipe()

result = await pipeline(data)
print(result)  # [150, 200]
```

### 4. Error Handling

Add error handling to your pipe:

```python
from rivusio import BasePipe, PipeError

class SafeFilterPipe(BasePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        try:
            return {k: v for k, v in data.items() if v > 100}
        except Exception as e:
            raise PipeError(self, e)
            
    async def handle_error(self, error: Exception, data: Dict) -> Dict:
        return {}
```

### 5. Process Streams

Process a stream of data:

```python
from rivusio.streams import AsyncStream

async def data_source():
    data = [
        {"a": 150, "b": 50},
        {"c": 200, "d": 75},
        {"e": 300, "f": 100}
    ]
    for item in data:
        yield item

stream = AsyncStream(data_source())

async for result in stream.process(pipeline):
    print(result)
```

## Next Steps

- Learn about [Basic Concepts](concepts.md)
- Explore [Error Handling](../user-guide/error-handling.md)
- Check out [Stream Processing](../user-guide/streams.md)
- Browse more [Examples](../examples/basic-transformation.md)
