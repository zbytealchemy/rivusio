# Stream Processing Example

This example demonstrates advanced stream processing patterns using Rivusio.

```python
from rivusio import AsyncBasePipe, AsyncPipeline
from rivusio.streams import AsyncStream
from rivusio.config import StreamConfig
from typing import Dict, Any, AsyncIterator
from datetime import timedelta
import aiohttp
import asyncio

class APISource(AsyncBasePipe[None, Dict[str, Any]]):
    def __init__(self, url: str, interval: float = 1.0):
        super().__init__()
        self.url = url
        self.interval = interval
    
    async def generate(self) -> AsyncIterator[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(self.url) as response:
                    data = await response.json()
                    yield data
                await asyncio.sleep(self.interval)

class DataEnricher(AsyncBasePipe[Dict[str, Any], Dict[str, Any]]):
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["processed_at"] = asyncio.get_event_loop().time()
        return data

class BatchAggregator(AsyncBasePipe[Dict[str, Any], List[Dict[str, Any]]]):
    def __init__(self, window_size: int = 10):
        super().__init__()
        self.window_size = window_size
        self.batch: List[Dict[str, Any]] = []
    
    async def process(self, data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        self.batch.append(data)
        
        if len(self.batch) >= self.window_size:
            result = self.batch.copy()
            self.batch.clear()
            return result
        return None

async def main():
    # Configure stream processing
    source = APISource("https://api.example.com/data", interval=2.0)
    
    pipeline = AsyncPipeline([
        DataEnricher(),
        BatchAggregator(window_size=5)
    ])
    
    config = StreamConfig(
        window_size=timedelta(minutes=1),
        batch_size=10
    )
    
    stream = AsyncStream(source.generate(), config=config)
    
    # Process stream
    async with pipeline:
        async for batch in stream.process(pipeline):
            if batch:
                print(f"Processed batch: {len(batch)} items")
                # Process batch further or store results

if __name__ == "__main__":
    asyncio.run(main())
```

## Explanation

1. Creating a custom data source that generates an async stream
2. Enriching data in real-time
3. Batch aggregation with windowing
4. Stream configuration with window and batch sizes
5. Pipeline composition for stream processing
6. Resource management with async context managers

