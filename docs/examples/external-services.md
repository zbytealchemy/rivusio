# External Services Example

This example demonstrates how to integrate external services with Rivusio pipelines.

```python
from rivusio import AsyncBasePipe, AsyncPipeline
from rivusio.config import PipeConfig
from typing import Dict, Any, Optional
import aiohttp
import aiokafka
import aioredis
import asyncpg
from pydantic import BaseModel, Field

class ServiceConfig(PipeConfig):
    redis_url: str = Field(default="redis://localhost")
    kafka_brokers: List[str] = Field(default_factory=lambda: ["localhost:9092"])
    postgres_dsn: str = Field(default="postgresql://user:pass@localhost/db")
    api_key: str = Field(default="")

class ExternalAPIClient(AsyncBasePipe[Dict[str, Any], Optional[Dict[str, Any]]]):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def setup(self) -> None:
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def cleanup(self) -> None:
        if self.session:
            await self.session.close()
    
    async def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        async with self.session.post(
            "https://api.example.com/process",
            json=data
        ) as response:
            if response.status == 200:
                return await response.json()
            return None

class CacheLayer(AsyncBasePipe[Dict[str, Any], Dict[str, Any]]):
    def __init__(self, redis_url: str):
        super().__init__()
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
    
    async def setup(self) -> None:
        self.redis = await aioredis.from_url(self.redis_url)
    
    async def cleanup(self) -> None:
        if self.redis:
            await self.redis.close()
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        
        cache_key = f"data:{data.get('id')}"
        
        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return cached
        
        # Cache miss, store and return
        await self.redis.set(cache_key, data, ex=300)  # 5 minutes TTL
        return data

async def main():
    config = ServiceConfig(
        redis_url="redis://localhost",
        api_key="your-api-key"
    )
    
    pipeline = AsyncPipeline([
        CacheLayer(config.redis_url),
        ExternalAPIClient(config.api_key)
    ])
    
    data = {"id": "123", "payload": "test"}
    
    async with pipeline:
        result = await pipeline(data)
        print(f"Processed result: {result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

This example demonstrates:
1. Integration with external HTTP APIs
2. Redis caching layer
3. Proper resource management with setup/cleanup
4. Configuration management for external services
```
