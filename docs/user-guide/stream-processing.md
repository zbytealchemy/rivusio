# Stream Processing

## Basic Streaming

```python
from rivusio import StreamPipe, StreamConfig
from typing import AsyncIterator, Dict

class DataStreamPipe(StreamPipe[Dict, Dict]):
    async def process_stream(self, stream: AsyncIterator[Dict]) -> AsyncIterator[Dict]:
        async for item in stream:
            if self.should_process(item):
                yield await self.transform(item)

async def main():
    stream_pipe = DataStreamPipe()
    async for result in stream_pipe.process_stream(data_source()):
        await store_result(result)
```

## Batch Streaming

```python
class BatchStreamPipe(StreamPipe[Dict, List[Dict]]):
    def __init__(self, batch_size: int):
        self.batch_size = batch_size
        self.current_batch = []

    async def process_stream(self, stream: AsyncIterator[Dict]) -> AsyncIterator[List[Dict]]:
        async for item in stream:
            self.current_batch.append(item)
            if len(self.current_batch) >= self.batch_size:
                yield self.current_batch
                self.current_batch = []
```