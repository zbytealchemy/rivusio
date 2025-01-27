# Core Concepts

## Overview

Rivusio is built around a few core concepts:

1. **Pipes**: Basic units of data transformation
2. **Pipelines**: Compositions of pipes
3. **Configuration**: Type-safe settings using Pydantic
4. **Error Handling**: Comprehensive error tracking
5. **Monitoring**: Built-in performance metrics

## Pipes

Pipes are the fundamental building blocks in Rivusio. Each pipe:

- Takes input data
- Performs a transformation
- Returns output data

```python
from typing import List, Dict
from rivusio import AsyncBasePipe, PipeConfig

class FilterConfig(PipeConfig):
    """Configuration for filter pipe."""
    min_value: float = 100.0

class FilterPipe(AsyncBasePipe[List[Dict], List[Dict]]):
    """Filter items based on value."""

    def __init__(self, config: FilterConfig) -> None:
        super().__init__()
        self.config = config
        self.name = config.name or self.__class__.__name__

    async def process(self, data: List[Dict]) -> List[Dict]:
        return [
            item for item in data
            if item.get("value", 0) > self.config.min_value
        ]
```

## Pipelines

Pipelines compose multiple pipes into a single processing unit:

```python
# Create pipes
filter_pipe = FilterPipe(FilterConfig(min_value=100))
transform_pipe = TransformPipe(TransformConfig())

# Create pipeline using >> operator
pipeline = filter_pipe >> transform_pipe

# Process data
result = await pipeline(data)
```

## Configuration

All pipes can be configured using Pydantic models:

```python
from rivusio import PipeConfig

class ProcessorConfig(PipeConfig):
    batch_size: int = 100
    timeout: float = 30.0
    retries: int = 3
```

## Error Handling

Rivusio provides comprehensive error handling:

```python
from rivusio import PipeError

try:
    result = await pipeline(data)
except PipeError as e:
    print(f"Error in {e.pipe}: {e.error}")
```

## Parallel Processing

Process data in parallel using execution strategies:

```python
from rivusio.sync.parallel import ExecutionStrategy

# Configure parallel execution
pipeline.configure_parallel(
    strategy=ExecutionStrategy.THREAD_POOL,
    max_workers=4
)

# Process batch in parallel
async with pipeline:
    results = await pipeline.execute_parallel(batch_data)
```

## Monitoring

Monitor pipeline performance:

```python
# Get pipeline metrics
metrics = pipeline.get_metrics()

# Analyze performance
for pipe_name, stats in metrics.items():
    print(f"Pipe: {pipe_name}")
    print(f"Processing time: {stats['processing_time']}")
    print(f"Items processed: {stats['item_count']}")
