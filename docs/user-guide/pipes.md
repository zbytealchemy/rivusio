# Working with Pipes

## Overview

Pipes are the basic building blocks in Rivusio. Each pipe represents a single data transformation operation that can be composed into larger pipelines.

## Types of Pipes

Rivusio provides three base pipe types:

1. `SyncBasePipe`: For synchronous operations
2. `AsyncBasePipe`: For asynchronous operations
3. `BasePipe`: Abstract base class for both sync and async pipes

## Creating a Pipe

Here's how to create a basic pipe:

```python
from rivusio import AsyncBasePipe, PipeConfig
from typing import Dict

class TransformConfig(PipeConfig):
    """Configuration for the transform pipe."""
    uppercase_fields: List[str] = ["name", "title"]

class TransformPipe(AsyncBasePipe[Dict, Dict]):
    """Transform specific fields to uppercase."""
    
    def __init__(self, config: TransformConfig) -> None:
        """Initialize the pipe."""
        super().__init__()
        self.config = config
        self.name = config.name or self.__class__.__name__

    async def process(self, data: Dict) -> Dict:
        """Process the input data."""
        result = data.copy()
        for field in self.config.uppercase_fields:
            if field in result:
                result[field] = result[field].upper()
        return result

# Create and use the pipe
config = TransformConfig(name="my_transformer")
pipe = TransformPipe(config)
result = await pipe.process({"name": "john", "title": "developer"})
```

## Configuration

Pipes can be configured using Pydantic models:

```python
from pydantic import BaseModel
from rivusio import PipeConfig

class MyPipeConfig(PipeConfig):
    max_retries: int = 3
    timeout: float = 5.0
    batch_size: int = 100
```

## Error Handling

Implement error handling in your pipe's process method:

```python
from rivusio import AsyncBasePipe, PipeError

class ProcessingPipe(AsyncBasePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        try:
            # Process data
            result = await self._process_data(data)
            return result
        except Exception as e:
            raise PipeError(
                pipe=self,
                message="Failed to process data",
                error=e
            ) from e
```

## Best Practices

1. Always use type hints for input and output types
2. Keep pipes focused on a single responsibility
3. Handle errors appropriately using PipeError
4. Use meaningful names and docstrings
5. Make pipes configurable via PipeConfig
6. Implement proper cleanup in __aenter__ and __aexit__ if needed

## Composing Pipes

Pipes can be composed using the >> operator:

```python
# Create pipeline
pipeline = filter_pipe >> transform_pipe >> output_pipe

# Process data
result = await pipeline(data)
```

## Monitoring

Monitor pipe performance using built-in metrics:

```python
# Get pipe metrics
metrics = pipe.get_metrics()
print(f"Processing time: {metrics['processing_time']}")
print(f"Items processed: {metrics['item_count']}")
```
