# Stream Processing

## Basic Streaming

```python
from rivusio import AsyncBasePipe, AsyncStream
from typing import AsyncIterator, Dict, Optional

class DataProcessPipe(AsyncBasePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        if self.should_process(data):
            return await self.transform(data)
        return data

async def data_source() -> AsyncIterator[Dict]:
    data = [
        {"value": 1},
        {"value": 2},
        {"value": 3}
    ]
    for item in data:
        yield item

async def main():
    # Create stream and pipe
    stream = AsyncStream(data_source())
    pipe = DataProcessPipe()
    
    # Process stream
    async for result in stream.process(pipe):
        await store_result(result)
```

## Batch Processing

```python
from datetime import timedelta

# Process items in batches
config = StreamConfig(batch_size=10)
stream = AsyncStream(data_source(), config=config)

async for batch in stream.process(pipe):
    print(f"Processed batch: {batch}")

# Process items in time windows
config = StreamConfig(window_size=timedelta(seconds=30))
stream = AsyncStream(data_source(), config=config)

async for window in stream.process(pipe):
    print(f"Processed window: {window}")
```

## Error Handling

```python
from rivusio import PipeError

class SafeProcessPipe(AsyncBasePipe[Dict, Optional[Dict]]):
    async def process(self, data: Dict) -> Optional[Dict]:
        try:
            return await self._process_data(data)
        except Exception as e:
            raise PipeError(self.__class__.__name__, e)

# Configure retries
config = StreamConfig(
    retry_attempts=3,
    retry_delay=1.0
)

stream = AsyncStream(data_source(), config=config)
pipe = SafeProcessPipe()

async for result in stream.process(pipe):
    if result:
        print(f"Processed: {result}")
```

## Sliding Windows

```python
# Process with sliding windows
stream = AsyncStream(data_source())

async for window in stream.sliding_window(window_size=5, step_size=2):
    print(f"Window items: {window}")

# Process with tumbling windows
async for window in stream.tumbling_window(window_size=5):
    print(f"Tumbling window: {window}")
```

## Best Practices

1. Configure appropriate batch sizes for your use case
2. Use windowing for time-based aggregations
3. Implement proper error handling
4. Consider backpressure with large data streams
5. Monitor stream processing metrics
