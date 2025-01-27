# Working with Pipelines

## Overview

Pipelines in Rivusio are sequences of pipes that process data in a specific order. They can be linear, branching, or merging, allowing you to build complex data processing workflows.

## Creating Pipelines

There are several ways to create pipelines:

### Using Pipeline Classes

```python
from rivusio import AsyncPipeline, SyncPipeline, MixedPipeline

# Create async pipeline
async_pipeline = AsyncPipeline([async_pipe1, async_pipe2])

# Create sync pipeline 
sync_pipeline = SyncPipeline([sync_pipe1, sync_pipe2])

# Create mixed pipeline
mixed_pipeline = MixedPipeline([sync_pipe1, async_pipe2])
```

### Using the >> Operator

```python
# Create sync pipeline
sync_pipeline = sync_pipe1 >> sync_pipe2

# Create async pipeline  
async_pipeline = async_pipe1 >> async_pipe2

# Create mixed pipeline
mixed_pipeline = sync_pipe1 >> async_pipe2
```

## Pipeline Configuration

Configure pipeline-wide settings:

```python
from rivusio import PipelineConfig

config = PipelineConfig(
    max_retries=3,
    retry_delay=5,
    timeout=30
)

pipeline = AsyncPipeline([pipe1, pipe2], name="MyPipeline")
```

## Parallel Execution

Rivusio supports parallel execution of pipelines using different strategies:

```python
from rivusio.core.parallel import ExecutionStrategy

# Configure parallel execution
pipeline.configure_parallel(
    strategy=ExecutionStrategy.THREAD_POOL,  # or GATHER for I/O-bound tasks
    max_workers=4,  # Optional, defaults based on strategy
    chunk_size=1000  # For process pool chunking
)

# Process items in parallel
async with pipeline:
    results = await pipeline.execute_parallel(batch_of_items)
```

The available execution strategies are:
- `GATHER`: Uses asyncio.gather for I/O-bound tasks (default)
- `THREAD_POOL`: Uses ThreadPoolExecutor for I/O and light CPU tasks
- `PROCESS_POOL`: Uses ProcessPoolExecutor for CPU-intensive tasks (currently using thread pool as temporary solution)

## Error Handling

Handle errors at the pipeline level:

```python
from rivusio.core.exceptions import PipelineError

try:
    result = await pipeline.process(data)
except PipelineError as e:
    print(f"Error in pipe {e.pipe}: {e.error}")
```

## Pipeline Metrics

Monitor pipeline performance:

```python
# Get metrics for all pipes
metrics = pipeline.get_metrics()

# Get outputs from a specific pipe
pipe_outputs = pipeline.get_pipe_outputs(specific_pipe)
```

## Best Practices

1. Use type hints to ensure type safety throughout the pipeline
2. Choose the appropriate pipeline type (Sync/Async/Mixed) based on your pipes
3. Use parallel execution for batch processing of independent items
4. Configure error handling and monitoring for production use
5. Clean up resources by using pipelines as async context managers
6. Choose the right execution strategy based on your workload:
   - GATHER for I/O-bound tasks
   - THREAD_POOL for mixed I/O and light CPU tasks
   - PROCESS_POOL for CPU-intensive tasks (coming soon)
