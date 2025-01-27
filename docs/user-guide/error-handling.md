# Error Handling

## Overview

Rivusio provides comprehensive error handling capabilities to help you build robust data processing pipelines.

## Error Types

### PipeError

Base error type for pipe-specific errors:

```python
from rivusio.exceptions import PipeError

try:
    result = await pipe.process(data)
except PipeError as e:
    print(f"Error in pipe {e.pipe}: {e.error}")
```

### PipelineError

Error type for pipeline-level errors:

```python
from rivusio.exceptions import PipelineError

try:
    result = await pipeline.process(data)
except PipelineError as e:
    print(f"Pipeline error: {e}")
    print(f"Failed pipe: {e.pipe}")
    print(f"Original error: {e.original_error}")
```

## Retry Mechanism

Configure retries for transient errors:

```python
from rivusio import RetryConfig

config = RetryConfig(
    max_retries=3,
    retry_delay=5,
    backoff_factor=2,
    exceptions=[TransientError]
)

pipe = MyPipe(config=config)
```

## Error Recovery

Implement custom error recovery:

```python
class MyPipe(ConfigurablePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        try:
            return await self._process_data(data)
        except ValueError as e:
            # Handle value error
            return self._handle_value_error(data, e)
        except KeyError as e:
            # Handle key error
            return self._handle_key_error(data, e)
```

## Dead Letter Queues

Handle unprocessable messages:

```python
class DeadLetterConfig(PipeConfig):
    queue_url: str

class ProcessingPipe(ConfigurablePipe[Dict, Dict]):
    def __init__(self, config: PipeConfig, dlq_config: DeadLetterConfig):
        super().__init__(config)
        self.dlq = DeadLetterQueue(dlq_config)
    
    async def process(self, data: Dict) -> Dict:
        try:
            return await self._process_data(data)
        except UnprocessableError as e:
            await self.dlq.send(data, error=e)
            return None
```

## Error Monitoring

Monitor errors in your pipeline:

```python
from rivusio.monitoring import PipelineMonitor

monitor = PipelineMonitor()
pipeline.set_error_monitor(monitor)

# Process data
await pipeline.process(data)

# Get error metrics
error_metrics = monitor.get_metrics()
print(f"Total errors: {error_metrics['error_count']}")
print(f"Error rate: {error_metrics['error_rate']}")
```

## Best Practices

1. Use appropriate error types
2. Implement retries for transient errors
3. Add proper error logging
4. Monitor error rates
5. Handle unprocessable messages with DLQ
6. Document error handling behavior
