# Working with Plugins

## Overview

The plugin system in Rivusio allows you to extend the framework with custom sources and sinks. Sources are pipes that generate data (like reading from a database or message queue), while sinks are pipes that output data (like writing to a file or sending to an API).

## Creating Plugins

### Async Source Example

```python
from rivusio.plugins import registry
from rivusio import AsyncBasePipe


@registry.register_async_source("kafka")
class KafkaSource(AsyncBasePipe[None, dict]):
    """Source that reads messages from Kafka."""

    async def process(self, _: None) -> dict:
        # Read from Kafka
        message = await self.consumer.get_message()
        return message


# Use the source
source = KafkaSource()
async for message in stream.process(source):
    print(message)
```

### Sync Sink Example

```python
from rivusio.plugins import registry
from rivusio import SyncBasePipe


@registry.register_sync_sink("csv")
class CsvSink(SyncBasePipe[dict, None]):
  """Sink that writes data to CSV files."""

  def process(self, data: dict) -> None:
    # Write to CSV
    with open(self.filename, 'a') as f:
      writer = csv.DictWriter(f, fieldnames=data.keys())
      writer.writerow(data)


# Use the sink
sink = CsvSink(filename="output.csv")
pipeline = transform_pipe >> sink
```

## Plugin Types

Rivusio supports four types of plugins:

1. **Async Sources** (`@registry.register_async_source`)
   - Generate data asynchronously
   - Good for I/O-bound sources like databases or APIs

2. **Async Sinks** (`@registry.register_async_sink`)
   - Write data asynchronously
   - Useful for async APIs or message queues

3. **Sync Sources** (`@registry.register_sync_source`)
   - Generate data synchronously
   - Good for file-based or in-memory sources

4. **Sync Sinks** (`@registry.register_sync_sink`)
   - Write data synchronously
   - Useful for files or simple outputs

## Best Practices

1. **Choose the Right Base**
   - Use AsyncBasePipe for I/O-bound operations
   - Use SyncBasePipe for CPU-bound or simple operations

2. **Error Handling**
   - Catch and handle source-specific errors
   - Convert to PipeError for consistent error handling

3. **Resource Management**
   - Implement `__aenter__` and `__aexit__` for async resources
   - Implement `__enter__` and `__exit__` for sync resources

4. **Configuration**
   - Use PipeConfig for plugin configuration
   - Document configuration options clearly

## Plugin Discovery

Plugins are discovered and registered at runtime when their module is imported. Make sure to import your plugin modules before using them:

```python
# Import plugins
import myapp.plugins.kafka  # Registers KafkaSource
import myapp.plugins.csv    # Registers CsvSink

# Now you can use them
source = KafkaSource()
sink = CsvSink()
```
