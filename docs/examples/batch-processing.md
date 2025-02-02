# Batch Processing Example

This example demonstrates how to implement batch processing using Rivusio pipelines.

```python
from rivusio import AsyncBasePipe, AsyncPipeline
from rivusio.config import ParallelConfig
from rivusio.core import ExecutionStrategy
from typing import List, Dict, Any
import asyncio
from datetime import datetime

class BatchProcessor(AsyncBasePipe[List[Dict[str, Any]], List[Dict[str, Any]]]):
    async def process(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed = []
        for item in batch:
            item["processed"] = True
            item["timestamp"] = datetime.now().isoformat()
            processed.append(item)
        return processed

class BatchValidator(AsyncBasePipe[List[Dict[str, Any]], List[Dict[str, Any]]]):
    async def process(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [item for item in batch if self._is_valid(item)]
    
    def _is_valid(self, item: Dict[str, Any]) -> bool:
        required_fields = ["id", "value"]
        return all(field in item for field in required_fields)

async def main():
    pipeline = AsyncPipeline([
        BatchValidator(),
        BatchProcessor()
    ])
    
    # Configure parallel processing
    parallel_config = ParallelConfig(
        strategy=ExecutionStrategy.THREAD_POOL,
        max_workers=4
    )
    pipeline.configure_parallel(parallel_config)
    
    # Create test batches
    batches = [
        [
            {"id": 1, "value": "a"},
            {"id": 2, "value": "b"},
            {"id": 3, "value": "c"}
        ],
        [
            {"id": 4, "value": "d"},
            {"value": "invalid"},
            {"id": 6, "value": "f"}
        ]
    ]
    
    # Process batches in parallel
    async with pipeline:
        results = await pipeline.execute_parallel(batches)
        
        for i, batch in enumerate(results):
            print(f"Batch {i + 1} results:")
            for item in batch:
                print(f"  {item}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Explanation

1. Batch validation using `BatchValidator`
2. Batch processing using `BatchProcessor`
3. Parallel execution configuration
4. Processing multiple batches concurrently