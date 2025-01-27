# Troubleshooting Guide

This guide helps you diagnose and resolve common issues you might encounter while using Rivusio.

## Common Issues

### 1. Pipeline Performance Issues

#### Symptoms
- Slow processing speed
- High memory usage
- Increasing latency

#### Solutions
1. **Check Batch Size**
   ```python
   # Optimize batch size for your use case
   config = StreamConfig(batch_size=1000)  # Adjust based on your data
   stream = AsyncStream(source, config=config)
   ```

2. **Monitor Memory Usage**
   ```python
   from rivusio.monitoring import PipelineMonitor
   
   monitor = PipelineMonitor()
   pipeline.set_monitor(monitor)
   ```

3. **Use Windowing for Large Datasets**
   ```python
   from datetime import timedelta
   config = StreamConfig(window_size=timedelta(seconds=30))
   ```

### 2. Memory Leaks

#### Symptoms
- Increasing memory usage over time
- Out of memory errors

#### Solutions
1. **Proper Resource Cleanup**
   ```python
   async with pipeline:
       await pipeline.process(data)
   ```

2. **Manual Cleanup**
   ```python
   try:
       await pipeline.process(data)
   finally:
       await pipeline.cleanup()
   ```

### 3. Data Loss or Corruption

#### Symptoms
- Missing data in output
- Unexpected data transformations

#### Solutions
1. **Enable Detailed Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Add Validation Pipes**
   ```python
   class ValidationPipe(AsyncBasePipe[Data, Data]):
       async def process(self, data: Data) -> Data:
           # Add your validation logic
           assert data.required_field is not None
           return data
   ```

### 4. Pipeline Configuration Issues

#### Symptoms
- Pipeline fails to start
- Configuration not applied

#### Solutions
1. **Verify Configuration**
   ```python
   from pydantic import ValidationError
   
   try:
       config = PipeConfig(param1="value1")
   except ValidationError as e:
       print(f"Invalid configuration: {e}")
   ```

2. **Check Plugin Registration**
   ```python
   from rivusio.plugins import PluginRegistry
   
   registry = PluginRegistry()
   print(registry.list_plugins())  # Verify your plugins are registered
   ```

## Debugging Techniques

### 1. Enable Debug Logging
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. Use Pipeline Monitoring
```python
from rivusio.monitoring import PipelineMonitor

monitor = PipelineMonitor()
pipeline.set_monitor(monitor)

# Check metrics after processing
print(monitor.get_metrics())
```

### 3. Add Debug Pipes
```python
class DebugPipe(AsyncBasePipe[Any, Any]):
    async def process(self, data: Any) -> Any:
        print(f"Debug: Processing data: {data}")
        return data

pipeline.add_pipe(DebugPipe())
```

## Performance Optimization

### 1. Batch Size Tuning
- Start with small batches (100-1000)
- Gradually increase while monitoring performance
- Monitor memory usage

### 2. Window Size Optimization
- Consider data arrival rate
- Balance between latency and throughput
- Monitor processing time

### 3. Resource Management
- Use async context managers
- Implement proper cleanup
- Monitor system resources

## Getting Help

If you're still experiencing issues:

1. Check the [GitHub Issues](https://github.com/yourusername/rivusio/issues)
2. Review the [API Documentation](../api/core.md)
3. Join our [Community Discussion](https://github.com/yourusername/rivusio/discussions)

## Contributing Bug Reports

When reporting bugs:

1. Provide minimal reproducible example
2. Include full error traceback
3. Share system information:
   - Python version
   - Rivusio version
   - OS details
4. Describe expected vs actual behavior
