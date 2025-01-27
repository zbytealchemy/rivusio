# Streams API Reference

## AsyncStream

::: rivusio.streams.stream.AsyncStream
    options:
      show_root_heading: true
      show_source: true

## SyncStream

::: rivusio.streams.stream.SyncStream
    options:
      show_root_heading: true
      show_source: true

## StreamConfig

::: rivusio.streams.stream.StreamConfig
    options:
      show_root_heading: true
      show_source: true

## Processing Modes

The stream processors support three processing modes:

### Single Item Processing

Process items one at a time:

```python
config = StreamConfig(batch_size=1)
stream = AsyncStream(source, config=config)
async for result in stream.process(pipe):
    print(f"Processed item: {result}")
```

### Batch Processing

Process items in fixed-size batches:

```python
config = StreamConfig(batch_size=10)
stream = AsyncStream(source, config=config)
async for batch in stream.process(pipe):
    print(f"Processed batch: {batch}")
```

### Window Processing

Process items in time-based windows:

```python
config = StreamConfig(window_size=timedelta(minutes=5))
stream = AsyncStream(source, config=config)
async for window in stream.process(pipe):
    print(f"Processed window: {window}")
```

The same modes are available for `SyncStream` without the async/await keywords.
