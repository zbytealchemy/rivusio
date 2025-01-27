# Performance Tuning Guide

This guide provides comprehensive information about optimizing Rivusio for maximum performance.

## Key Performance Metrics

1. **Throughput**: Records processed per second
2. **Latency**: Time to process individual records
3. **Resource Usage**: CPU, memory, and I/O utilization
4. **Backpressure**: Buffer utilization and blocking time

## Configuration Optimization

### 1. Stream Configuration

```python
from datetime import timedelta
from rivusio.streams import StreamConfig

config = StreamConfig(
    batch_size=1000,              # Adjust based on data size
    window_size=timedelta(seconds=30),
    buffer_size=5000,             # Control memory usage
    max_retries=3,                # Balance reliability vs performance
)
```

#### Batch Size Optimization
- Small batches (100-1000): Lower latency, good for real-time
- Large batches (1000+): Higher throughput, good for bulk processing
- Monitor memory usage to find optimal size

### 2. Pipeline Configuration

```python
from rivusio import AsyncPipeline
from rivusio.monitoring import PipelineMonitor

pipeline = AsyncPipeline()
monitor = PipelineMonitor(window_size=timedelta(minutes=5))
pipeline.set_monitor(monitor)

# Enable parallel processing where possible
pipeline.parallel_workers = 4  # Adjust based on CPU cores
```

## Memory Management

### 1. Memory Profiling

```python
from memory_profiler import profile

@profile
async def process_data():
    async with pipeline:
        await pipeline.process(data)
```

### 2. Memory Optimization Techniques

```python
# Use generators for large datasets
async def data_generator():
    async for chunk in large_dataset:
        yield chunk

# Stream processing with windowing
stream = AsyncStream(
    data_generator(),
    config=StreamConfig(window_size=timedelta(seconds=30))
)
```

## CPU Optimization

### 1. Parallel Processing

```python
# Configure parallel execution
pipeline.parallel_execution = True
pipeline.max_workers = min(32, (os.cpu_count() or 1) * 2)

# Process data in parallel
results = await pipeline.execute_parallel(data_batch)
```

### 2. CPU Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Your code here
profiler.disable()
stats = pstats.Stats(profiler).sort_stats('cumulative')
stats.print_stats()
```

## I/O Optimization

### 1. Async I/O

```python
class AsyncIOPipe(AsyncBasePipe[Data, Result]):
    async def process(self, data: Data) -> Result:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()
```

### 2. Buffering

```python
from rivusio.streams import BufferedStreamConfig

config = BufferedStreamConfig(
    buffer_size=1000,
    flush_interval=timedelta(seconds=5)
)
```

## Monitoring and Metrics

### 1. Performance Metrics Collection

```python
from rivusio.monitoring import MetricsCollector

metrics = MetricsCollector()
metrics.record_timing("processing_time", 1.5)
metrics.record_count("records_processed", 1000)
```

### 2. Real-time Monitoring

```python
async def monitor_performance():
    while True:
        metrics = pipeline.monitor.get_metrics()
        print(f"Throughput: {metrics.throughput}/s")
        print(f"Latency: {metrics.latency}ms")
        await asyncio.sleep(1)
```

## Performance Testing

### 1. Load Testing

```python
async def load_test(pipeline: AsyncPipeline, data_size: int):
    start_time = time.time()
    data = generate_test_data(data_size)
    
    async with pipeline:
        result = await pipeline.process(data)
    
    duration = time.time() - start_time
    print(f"Processed {data_size} records in {duration:.2f}s")
    print(f"Throughput: {data_size/duration:.2f} records/s")
```

### 2. Stress Testing

```python
async def stress_test(pipeline: AsyncPipeline, duration: int):
    end_time = time.time() + duration
    records_processed = 0
    
    while time.time() < end_time:
        data = generate_continuous_data()
        await pipeline.process(data)
        records_processed += len(data)
```

## Best Practices

1. **Data Size Management**
   - Use streaming for large datasets
   - Implement windowing for time-series data
   - Buffer data appropriately

2. **Resource Management**
   - Use context managers for cleanup
   - Implement proper error handling
   - Monitor system resources

3. **Optimization Strategy**
   - Profile before optimizing
   - Test with production-like data
   - Monitor real-world performance

## Performance Troubleshooting

1. **High Latency**
   - Reduce batch size
   - Check for I/O bottlenecks
   - Monitor system resources

2. **Memory Issues**
   - Implement proper cleanup
   - Use generators for large datasets
   - Monitor memory usage

3. **CPU Bottlenecks**
   - Enable parallel processing
   - Optimize compute-heavy operations
   - Profile CPU usage

## Performance Tuning

### Overview

Rivusio provides several ways to optimize pipeline performance:
1. Parallel execution strategies
2. Pipeline composition
3. Resource management
4. Memory optimization

### Parallel Execution

#### Execution Strategies

Choose the right execution strategy based on your workload:

```python
from rivusio.core.parallel import ExecutionStrategy

# I/O-bound tasks (default)
pipeline.configure_parallel(ExecutionStrategy.GATHER)

# Mixed I/O and light CPU tasks
pipeline.configure_parallel(
    ExecutionStrategy.THREAD_POOL,
    max_workers=4  # Defaults to min(32, cpu_count + 4)
)

# CPU-intensive tasks (coming soon)
pipeline.configure_parallel(
    ExecutionStrategy.PROCESS_POOL,
    max_workers=8,  # Defaults to cpu_count
    chunk_size=1000  # For batching items
)
```

#### When to Use Each Strategy

1. **GATHER**
   - Best for: I/O-bound tasks (network requests, file operations)
   - Pros: Low overhead, efficient for async operations
   - Cons: No true parallelism, blocked by CPU-bound tasks

2. **THREAD_POOL**
   - Best for: Mixed I/O and light CPU tasks
   - Pros: True parallelism for I/O, handles blocking calls
   - Cons: Limited by GIL for CPU-intensive tasks

3. **PROCESS_POOL** (coming soon)
   - Best for: CPU-intensive tasks
   - Pros: True parallelism, bypasses GIL
   - Cons: Higher overhead, data serialization costs

### Pipeline Composition

Optimize pipeline structure:

1. **Minimize Pipeline Length**
   ```python
   # Bad: Many small pipes
   pipeline = pipe1 >> pipe2 >> pipe3 >> pipe4 >> pipe5

   # Better: Combine related operations
   pipeline = preprocess >> transform >> postprocess
   ```

2. **Balance Async/Sync Operations**
   ```python
   # Bad: Mixing async/sync unnecessarily
   pipeline = AsyncPipeline([
       async_io_pipe,
       sync_transform,  # Blocks event loop
       async_io_pipe
   ])

   # Better: Group sync operations
   pipeline = AsyncPipeline([
       async_io_pipe,
       combined_sync_transform,  # Single sync block
       async_io_pipe
   ])
   ```

### Resource Management

1. **Use Context Managers**
   ```python
   async with pipeline:
       results = await pipeline.execute_parallel(items)
   # Resources automatically cleaned up
   ```

2. **Configure Worker Pools**
   ```python
   # Adjust based on system resources
   pipeline.configure_parallel(
       strategy=ExecutionStrategy.THREAD_POOL,
       max_workers=min(32, cpu_count + 4)
   )
   ```

### Memory Optimization

1. **Chunk Processing**
   ```python
   # Process large datasets in chunks
   pipeline.configure_parallel(
       strategy=ExecutionStrategy.THREAD_POOL,
       chunk_size=1000  # Adjust based on memory constraints
   )
   ```

2. **Clean Up Intermediate Results**
   ```python
   # Get outputs if needed, then clear
   outputs = pipeline.get_pipe_outputs(pipe)
   pipeline._pipe_outputs[pipe].clear()  # Free memory
   ```

### Monitoring Performance

Use built-in metrics to identify bottlenecks:

```python
# Get performance metrics
metrics = pipeline.get_metrics()

# Analyze pipe-specific metrics
for pipe_name, pipe_metrics in metrics.items():
    print(f"Pipe: {pipe_name}")
    print(f"Processing time: {pipe_metrics['processing_time']}")
    print(f"Items processed: {pipe_metrics['item_count']}")
```

### Best Practices

1. Profile your workload to choose the right execution strategy
2. Monitor memory usage with large datasets
3. Use appropriate chunk sizes for parallel processing
4. Clean up resources properly
5. Keep pipelines focused and efficient
6. Consider data locality and serialization costs
