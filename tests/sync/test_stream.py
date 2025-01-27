"""Tests for synchronous stream processing."""
import threading
import time
from collections.abc import Iterator
from datetime import timedelta
from typing import Any, Union

import pytest

from rivusio.config.stream import StreamConfig
from rivusio.core.exceptions import PipeError
from rivusio.sync.pipeline import SyncBasePipe
from rivusio.sync.stream import SyncStream


def test_sync_stream_batch_processing() -> None:
    """Test synchronous batch processing."""
    items = list(range(10))
    config = StreamConfig(batch_size=3)
    stream = SyncStream(iter(items), config=config)

    class BatchPipe(SyncBasePipe[Any, Any]):
        def process(self, data: Any) -> Any:
            return sum(data) if isinstance(data, list) else data

    results: list[int] = []
    for result in stream.process(BatchPipe()):
        results.append(result)

    assert results == [3, 12, 21, 9]


def test_sync_stream_error_handling() -> None:
    """Test synchronous error handling."""
    items = list(range(5))
    stream = SyncStream(iter(items))

    class ErrorPipe(SyncBasePipe[Any, Any]):
        def process(self, data: Any) -> Any:
            if data == 2:
                raise ValueError("Test error")
            return data

    with pytest.raises(PipeError):
        list(stream.process(ErrorPipe()))


def test_sync_stream_metrics() -> None:
    """Test synchronous metrics collection."""
    items = list(range(5))
    config = StreamConfig(collect_metrics=True)
    stream = SyncStream(iter(items), config=config)

    class CountingPipe(SyncBasePipe[Any, Any]):
        def process(self, data: Any) -> Any:
            start_time = time.time()
            time.sleep(0.001)
            if stream.metrics is not None:
                stream.metrics.record_processing_time(time.time() - start_time)
                stream.metrics.record_success()
                stream.metrics.record_throughput(1)
            return data

    list(stream.process(CountingPipe()))

    assert stream.metrics is not None
    metrics = stream.metrics.get_metrics()
    processing_time = metrics["processing_time"].average
    assert processing_time is not None and processing_time > 0
    assert metrics["error_rate"].average == 0.0
    throughput = metrics["throughput"].average
    assert throughput is not None and throughput > 0


def test_sync_stream_empty() -> None:
    """Test synchronous processing of empty stream."""
    stream: SyncStream[Any] = SyncStream(iter([]))

    class NoopPipe(SyncBasePipe[Any, Any]):
        def process(self, data: Any) -> Any:
            return data

    results: list[Any] = list(stream.process(NoopPipe()))
    assert len(results) == 0


def test_sync_stream_custom_serialization() -> None:
    """Test synchronous custom serialization."""
    class CustomObject:
        def __init__(self, value: Any) -> None:
            self.value = value

        def serialize(self) -> dict:
            return {"value": self.value}

    items = [CustomObject(i) for i in range(3)]

    class SerializePipe(SyncBasePipe[Any, Any]):
        def process(self, data: Any) -> Any:
            if isinstance(data, CustomObject):
                return data.serialize()
            return data

    stream = SyncStream(iter(items))
    results: list[dict] = list(stream.process(SerializePipe()))

    assert all(isinstance(r, dict) for r in results)
    assert [r["value"] for r in results] == [0, 1, 2]


def test_sync_stream_buffer_handling() -> None:
    """Test synchronous buffer handling."""
    items = list(range(10))
    config = StreamConfig(buffer_size=3)
    stream = SyncStream(iter(items), config=config)

    class SlowPipe(SyncBasePipe[Any, Any]):
        def process(self, data: Any) -> Any:
            time.sleep(0.01)
            return data

    results: list[int] = list(stream.process(SlowPipe()))
    assert results == list(range(10))
    assert len(stream._buffer) <= 3


def test_sync_stream_batch_timeout() -> None:
    """Test synchronous batch processing with timeout."""
    items = list(range(3))
    config = StreamConfig(
        batch_size=5,
        window_size=timedelta(milliseconds=100),
    )
    stream = SyncStream(iter(items), config=config)

    class BatchPipe(SyncBasePipe[Union[int, list[int]], Union[int, list[int]]]):
        def process(self, data: Union[int, list[int]]) -> Union[int, list[int]]:
            return data

    results: list[int] = []
    for batch in stream.process(BatchPipe()):
        if isinstance(batch, list):
            results.extend(batch)

    assert sorted(results) == sorted(items)


def test_sync_stream_context_manager() -> None:
    """Test stream usage with context manager."""
    items = list(range(5))
    results = []

    with SyncStream(iter(items)) as stream:
        for item in stream:
            results.append(item)

    assert results == items


def test_sync_stream_exhaustion() -> None:
    """Test stream behavior after exhaustion."""
    items = list(range(5))
    stream = SyncStream(iter(items))

    results1 = list(stream)
    assert results1 == items

    results2 = list(stream)
    assert results2 == []


def test_sync_stream_window_processing() -> None:
    """Test time window processing."""
    items = list(range(10))
    window_duration = timedelta(milliseconds=50)
    stream = SyncStream(iter(items))

    windows = []
    for window in stream.time_window(window_duration):
        windows.append(window)
        time.sleep(0.06)  # Ensure window closes

    assert len(windows) > 0
    assert all(isinstance(w, list) for w in windows)


def test_sync_stream_sliding_window() -> None:
    """Test sliding window processing."""
    items = list(range(10))
    stream = SyncStream(iter(items))

    windows = list(stream.sliding_window(window_size=3, step_size=2))
    assert len(windows) > 0
    assert all(len(w) == 3 for w in windows[:-1])


def test_sync_stream_tumbling_window() -> None:
    """Test tumbling window processing."""
    items = list(range(10))
    stream = SyncStream(iter(items))

    windows = list(stream.tumbling_window(window_size=3))
    assert len(windows) == 4
    assert all(len(w) <= 3 for w in windows)


def test_sync_stream_backpressure() -> None:
    """Test backpressure mechanism."""
    class SlowConsumer:
        def __init__(self) -> None:
            self.items = range(10)
            self.index = 0

        def __iter__(self) -> "SlowConsumer":
            return self

        def __next__(self) -> int:
            if self.index >= len(self.items):
                raise StopIteration
            time.sleep(0.01)
            value = self.items[self.index]
            self.index += 1
            return value

    config = StreamConfig(buffer_size=2)
    stream = SyncStream(SlowConsumer(), config=config)

    results = []
    start_time = time.time()

    for item in stream:
        results.append(item)
        assert len(stream._buffer) <= config.buffer_size

    processing_time = time.time() - start_time
    assert processing_time >= 0.1
    assert results == list(range(10))


def test_sync_stream_parallel_processing() -> None:
    """Test parallel processing with multiple consumers."""
    items = list(range(100))
    config = StreamConfig(buffer_size=10)
    stream = SyncStream(iter(items), config=config)

    results = []
    lock = threading.Lock()

    def consumer() -> None:
        for item in stream:
            with lock:
                results.append(item)

    threads = [threading.Thread(target=consumer) for _ in range(3)]
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    assert sorted(results) == items


def test_sync_stream_error_propagation() -> None:
    """Test error propagation in stream processing."""
    def error_generator() -> Iterator[int]:
        yield 1
        yield 2
        raise ValueError("Test error")

    stream = SyncStream(error_generator())

    results = []
    with pytest.raises(ValueError, match="Test error"):
        for item in stream:
            results.append(item)

    assert results == [1, 2]
    assert stream.is_closed()


def test_sync_stream_custom_window_handler() -> None:
    """Test custom window handler functionality."""
    items = list(range(5))
    config = StreamConfig(window_size=timedelta(milliseconds=50))
    stream = SyncStream(iter(items), config=config)

    results = []
    for window in stream.time_window(duration=timedelta(milliseconds=50)):
        window_sum = sum(window)
        results.append(window_sum)
        time.sleep(0.06)

    assert all(isinstance(r, int) for r in results)
    assert sum(results) == sum(items)


def test_sync_stream_metrics_detailed() -> None:
    """Test detailed metrics collection."""
    items = list(range(5))
    config = StreamConfig(collect_metrics=True)
    stream = SyncStream(iter(items), config=config)

    for _ in stream:
        assert stream.metrics is not None
        stream.metrics.record_success()
        stream.metrics.record_processing_time(0.001)
        stream.metrics.record_throughput(1)
        time.sleep(0.001)

    assert stream.metrics is not None
    metrics = stream.metrics.get_metrics()

    processing_time = metrics["processing_time"].average
    throughput = metrics["throughput"].average

    assert metrics["error_rate"].average == 0.0
    assert processing_time is not None and processing_time > 0
    assert throughput is not None and throughput > 0


def test_sync_stream_buffer_overflow_handling() -> None:
    """Test buffer overflow handling."""
    def slow_generator() -> Iterator[int]:
        for i in range(20):
            time.sleep(0.01)
            yield i

    config = StreamConfig(buffer_size=3)
    stream = SyncStream(slow_generator(), config=config)

    results = []
    start_time = time.time()

    for item in stream:
        results.append(item)
        assert len(stream._buffer) <= config.buffer_size

    processing_time = time.time() - start_time
    assert processing_time >= 0.2  # Verify processing was throttled
    assert results == list(range(20))
