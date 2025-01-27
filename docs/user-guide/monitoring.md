# Monitoring

## Overview

Rivusio provides built-in monitoring capabilities for tracking pipeline performance metrics. The monitoring system supports:

- Processing time tracking
- Error rate monitoring
- Throughput measurement
- Time-windowed metrics collection

## Basic Metrics Collection

Use `MetricsCollector` for basic metrics collection:

```python
from datetime import timedelta
from rivusio.monitoring import MetricsCollector

# Create collector with 5-minute window
collector = MetricsCollector(window_size=timedelta(minutes=5))

# Record metrics
collector.record_processing_time(0.123)  # 123ms processing time
collector.record_success()  # Record successful operation
collector.record_throughput(100)  # Processed 100 items

# Get metrics
metrics = collector.get_metrics()
print(f"Avg processing time: {metrics['processing_time']['avg']:.3f}")
print(f"Error rate: {metrics['error_rate']['avg']:.1f}")
print(f"Throughput: {metrics['throughput']['avg']:.0f}")
```

## Pipeline Monitoring

Use `PipelineMonitor` for pipeline-specific monitoring:

```python
from rivusio.monitoring import PipelineMonitor

# Create and attach monitor
monitor = PipelineMonitor(window_size=timedelta(minutes=10))
pipeline.set_monitor(monitor)

# Start monitoring
monitor.start()

try:
    # Process data
    await pipeline.process(data)
    monitor.record_success()
except Exception as e:
    monitor.record_error()
    raise
finally:
    monitor.stop()

# Get metrics
metrics = monitor.get_metrics()
print(f"Total time: {metrics['total_time']:.2f}s")
print(f"Error rate: {metrics['error_rate']['avg']:.2%}")
```

## Metric Types

### Processing Time

Tracks how long operations take:

```python
# Record processing duration
collector.record_processing_time(duration_seconds)

# Get processing time metrics
metrics = collector.get_metrics()
processing_stats = metrics['processing_time']
print(f"Average: {processing_stats['avg']:.3f}s")
print(f"Maximum: {processing_stats['max']:.3f}s")
print(f"Latest: {processing_stats['latest']:.3f}s")
```

### Error Rate

Tracks success/failure ratio:

```python
# Record outcomes
try:
    # Process data
    collector.record_success()
except Exception:
    collector.record_error()
    raise

# Get error rate metrics
metrics = collector.get_metrics()
error_stats = metrics['error_rate']
print(f"Error rate: {error_stats['avg']:.2%}")
```

### Throughput

Tracks items processed per time window:

```python
# Record batch processing
collector.record_throughput(items_processed)

# Get throughput metrics
metrics = collector.get_metrics()
throughput_stats = metrics['throughput']
print(f"Average throughput: {throughput_stats['avg']:.0f} items")
print(f"Peak throughput: {throughput_stats['max']:.0f} items")
```

## Time Windows

Metrics are collected in sliding time windows:

```python
# Create collector with custom window
collector = MetricsCollector(
    window_size=timedelta(minutes=15)  # 15-minute window
)

# Values older than window_size are automatically discarded
# Each metric type (processing_time, error_rate, throughput)
# maintains its own window
```

## Best Practices

1. Choose appropriate window sizes:
   - Shorter windows (1-5 minutes) for real-time monitoring
   - Longer windows (15-60 minutes) for trend analysis

2. Monitor multiple aspects:
   - Processing time for performance
   - Error rates for reliability
   - Throughput for capacity planning

3. Use pipeline monitors for end-to-end visibility:
   - Start/stop timing around pipeline execution
   - Track success/failure at pipeline level
   - Monitor overall throughput

4. Clean up resources:
   - Stop monitors when done
   - Clear old metrics if needed
   - Use monitors in context managers when possible
