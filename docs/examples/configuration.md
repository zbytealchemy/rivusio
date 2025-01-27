# Configuration Example

This example demonstrates how to use configuration management in Rivusio.

```python
from rivusio import AsyncBasePipe
from rivusio.config import PipeConfig
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import timedelta

class DatabaseConfig(PipeConfig):
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    max_connections: int = Field(default=10, gt=0)
    timeout: timedelta = Field(default=timedelta(seconds=30))
    retry_attempts: int = Field(default=3, ge=0)

class ProcessingConfig(PipeConfig):
    batch_size: int = Field(default=100, gt=0)
    window_size: timedelta = Field(default=timedelta(minutes=5))
    filters: List[str] = Field(default_factory=list)
    threshold: float = Field(default=0.5, ge=0, le=1.0)

class DataProcessor(AsyncBasePipe[Dict[str, Any], Dict[str, Any]]):
    def __init__(self, db_config: DatabaseConfig, proc_config: ProcessingConfig):
        super().__init__()
        self.db_config = db_config
        self.proc_config = proc_config
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Use configuration in processing
        if len(data) > self.proc_config.batch_size:
            data = dict(list(data.items())[:self.proc_config.batch_size])
        
        if self.proc_config.filters:
            data = {k: v for k, v in data.items() if k in self.proc_config.filters}
        
        return data

async def main():
    # Load config from environment variables or file
    db_config = DatabaseConfig(
        host="db.example.com",
        port=5432,
        max_connections=20
    )
    
    proc_config = ProcessingConfig(
        batch_size=50,
        filters=["important", "critical"],
        threshold=0.75
    )
    
    processor = DataProcessor(db_config, proc_config)
    
    # Process data
    data = {
        "important": 1,
        "critical": 2,
        "normal": 3
    }
    
    result = await processor(data)
    print(f"Processed data: {result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

This example demonstrates:
1. Creating configuration classes using `PipeConfig`
2. Validating configuration using Pydantic fields
3. Using multiple configurations in a single pipe
4. Processing data with configuration parameters
