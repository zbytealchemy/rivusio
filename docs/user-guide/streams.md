# Stream Processing

## Overview

Rivusio provides native support for stream processing, allowing you to build efficient data streaming pipelines.

## Basic Streaming

Create a streaming pipeline:

```python
from rivusio.streams import StreamPipe
from typing import AsyncIterator, Dict

class MyStreamPipe(StreamPipe[Dict, Dict]):
    async def process_stream(self, stream: AsyncIterator[Dict]) -> AsyncIterator[Dict]:
        async for item in stream:
            yield await self.process_item(item)
    
    async def process_item(self, item: Dict) -> Dict:
        return {"processed": item}

# Use the stream pipe
pipe = MyStreamPipe()
async for result in pipe.stream(source_data):
    print(result)
```

## Windowing

Process data in windows:

```python
from rivusio.streams import WindowedStreamPipe
from datetime import timedelta

class WindowProcessor(WindowedStreamPipe[Dict, List]):
    def __init__(self, window_size: timedelta):
        super().__init__(window_size)
    
    async def process_window(self, window: List[Dict]) -> List:
        return self.aggregate_window(window)
```

## Batching

Process data in batches:

```python
from rivusio.streams import BatchStreamPipe

class BatchProcessor(BatchStreamPipe[Dict, List]):
    def __init__(self, batch_size: int):
        super().__init__(batch_size)
    
    async def process_batch(self, batch: List[Dict]) -> List:
        return await self.process_items(batch)
```

## Backpressure

Handle backpressure:

```python
from rivusio.streams import BackpressureConfig

config = BackpressureConfig(
    max_buffer_size=1000,
    throttle_threshold=0.8,
    min_processing_time=0.1
)

pipe = StreamPipe(config=config)
```

## Error Handling

Handle stream errors:

```python
from rivusio.streams import StreamError

try:
    async for result in pipe.stream(data):
        try:
            process_result(result)
        except StreamError as e:
            handle_stream_error(e)
except Exception as e:
    handle_fatal_error(e)
```

## Monitoring

Monitor stream processing:

```python
from rivusio.monitoring import PipelineMonitor

monitor = PipelineMonitor()
pipe.set_monitor(monitor)

# Get stream metrics
metrics = monitor.get_metrics()
print(f"Throughput: {metrics['throughput']}")
print(f"Processing time: {metrics['processing_time']}")
```

## Best Practices

1. Use appropriate window/batch sizes
2. Handle backpressure
3. Implement proper error handling
4. Monitor stream performance
5. Clean up resources properly
6. Test with realistic data volumes

## Async Streams

```python
from rivusio import AsyncBasePipe, AsyncStream
from typing import AsyncIterator, Dict, Optional
import asyncio

class AsyncNumberFilterPipe(AsyncBasePipe[Dict, Optional[Dict]]):
    async def process(self, data: Dict) -> Optional[Dict]:
        filtered = {k: v for k, v in data.items() if isinstance(v, (int, float))}
        return filtered if filtered else None

async def data_generator() -> AsyncIterator[Dict]:
    data = [
        {"a": 1, "b": "text", "c": 2.5},
        {"x": "skip", "y": "ignore"},
        {"d": 10, "e": 20.0, "f": 30},
    ]
    for item in data:
        yield item
        await asyncio.sleep(0.1)  # Simulate async data source

async def main():
    # Create stream and pipe
    stream = AsyncStream(data_generator())
    pipe = AsyncNumberFilterPipe()
    
    # Process stream
    async for result in stream.through(pipe):
        if result:  # Handle None results from filter
            print(f"Processed: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Sync Streams

```python
from rivusio import SyncBasePipe, SyncStream
from typing import Iterator, List

class BatchSumPipe(SyncBasePipe[List[float], float]):
    def process(self, batch: List[float]) -> float:
        return sum(batch)

def number_generator() -> Iterator[List[float]]:
    batches = [
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0],
        [7.0, 8.0, 9.0]
    ]
    for batch in batches:
        yield batch

def main():
    # Create stream and pipe
    stream = SyncStream(number_generator())
    pipe = BatchSumPipe()
    
    # Process stream
    for batch_sum in stream.through(pipe):
        print(f"Batch sum: {batch_sum}")

if __name__ == "__main__":
    main()
```

## Stream with Error Handling

```python
from rivusio import AsyncBasePipe, AsyncStream, PipeError
from typing import AsyncIterator, Dict
import asyncio

class SafeDivisionPipe(AsyncBasePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        try:
            return {k: 100 / v for k, v in data.items()}
        except ZeroDivisionError as e:
            raise PipeError(f"Division by zero: {str(e)}")
    
    async def handle_error(self, error: Exception, data: Dict) -> Dict:
        print(f"Error processing {data}: {error}")
        return {"error": str(error)}

async def data_with_errors() -> AsyncIterator[Dict]:
    data = [
        {"a": 2, "b": 4},
        {"a": 0, "b": 1},  # Will cause error
        {"a": 5, "b": 10}
    ]
    for item in data:
        yield item
        await asyncio.sleep(0.1)

async def main():
    stream = AsyncStream(data_with_errors())
    pipe = SafeDivisionPipe()
    
    async for result in stream.through(pipe):
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```
