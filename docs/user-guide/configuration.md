# Configuration Management

## Using PipeConfig

Define type-safe configurations:

```python
from rivusio import PipeConfig, ConfigurablePipe
from pydantic import Field, validator

class BatchConfig(PipeConfig):
    size: int = Field(ge=1, le=1000)
    timeout: int = Field(ge=0)
    
    @validator("timeout")
    def validate_timeout(cls, v, values):
        if v == 0 and values["size"] > 100:
            raise ValueError("Timeout required for large batch sizes")
        return v

class BatchProcessor(ConfigurablePipe[List[Dict], Dict, BatchConfig]):
    async def process(self, data: List[Dict]) -> Dict:
        if len(data) > self.config.size:
            raise ValueError("Batch size exceeded")
        return await self.process_batch(data)
```

## Environment Variables

```python
class ApiConfig(PipeConfig):
    api_key: str = Field(..., env='API_KEY')
    endpoint: str = Field(..., env='API_ENDPOINT')
    timeout: int = Field(default=30, env='API_TIMEOUT')
```

## Nested Configuration

Create complex configurations:

```python
class KafkaConfig(PipeConfig):
    bootstrap_servers: List[str]
    topic: str
    group_id: str

class ProcessingConfig(PipeConfig):
    batch_size: int = 100
    timeout: int = 30
    kafka: KafkaConfig

config = ProcessingConfig(
    batch_size=200,
    kafka=KafkaConfig(
        bootstrap_servers=["localhost:9092"],
        topic="my-topic",
        group_id="my-group"
    )
)
```

## Validation

Add validation rules:

```python
from pydantic import validator

class BatchConfig(PipeConfig):
    size: int = Field(ge=1, le=1000)
    timeout: int = Field(ge=0)
    
    @validator("timeout")
    def validate_timeout(cls, v, values):
        if v == 0 and values["size"] > 100:
            raise ValueError("Timeout required for large batch sizes")
        return v
```

## Best Practices

1. Use type hints for all fields
2. Provide sensible defaults
3. Add field descriptions
4. Use environment variables for sensitive data
5. Validate configuration values
