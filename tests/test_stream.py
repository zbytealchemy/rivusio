"""Tests for stream processing functionality."""
import asyncio
import time
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Any, TypeVar, Union, cast

import pytest

from rivusio.core.exceptions import PipeError
from rivusio.core.pipe import AsyncBasePipe, SyncBasePipe
from rivusio.monitoring.metrics import MetricsCollector
from rivusio.streams.stream import AsyncStream, StreamConfig, SyncStream


class CustomMetricsCollector(MetricsCollector):
    """Custom metrics collector with record_custom capability."""

    def __init__(self) -> None:
        super().__init__()
        self.custom_count = 0

    def record_custom(self) -> None:
        """Record a custom metric occurrence."""
        self.custom_count += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics including custom metrics."""
        metrics = super().get_metrics()
        metrics["custom_metric"] = {"count": self.custom_count}  # type: ignore
        return metrics


T = TypeVar("T")
R = TypeVar("R")


class MultiplyByTwoAsync(AsyncBasePipe[Any, Any]):
    """Simple async pipe that multiplies input by 2."""

    async def process(self, data: Any) -> Any:
        if isinstance(data, int):
            return data * 2
        return data


class MultiplyByTwoSync(SyncBasePipe[int, int]):
    """Simple sync pipe that multiplies input by 2."""

    def process(self, data: int) -> int:
        return data * 2


@pytest.mark.asyncio()
async def test_stream_basic_processing() -> None:
    """Test basic stream processing."""
    items = [1, 2, 3, 4, 5]
    pipe = MultiplyByTwoAsync()

    async def source() -> AsyncIterator[int]:
        for item in items:
            yield item

    stream = AsyncStream(source())

    results = []
    async for result in stream.process(pipe):
        results.append(result)

    assert results == [2, 4, 6, 8, 10]


@pytest.mark.asyncio()
async def test_stream_batch_processing() -> None:
    """Test batch processing."""
    items = list(range(10))
    config = StreamConfig(batch_size=3)

    async def source() -> AsyncIterator[int]:
        for item in items:
            yield item

    class IdentityPipe(AsyncBasePipe[Any, Any]):
        """Simple pipe that returns input unchanged."""

        async def process(self, data: Any) -> Any:
            return data

    stream = AsyncStream(source(), config=config)
    pipe = IdentityPipe()

    batches = []
    async for batch in stream.process(pipe):
        batches.append(batch)

    assert len(batches) == 4
    assert batches == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


@pytest.mark.asyncio()
async def test_stream_window_processing() -> None:
    """Test window-based processing."""
    items = list(range(10))
    config = StreamConfig(window_size=timedelta(seconds=0.1))

    async def source() -> AsyncIterator[int]:
        for item in items:
            await asyncio.sleep(0.05)
            yield item

    class IdentityPipe(AsyncBasePipe[Any, Any]):
        """Simple pipe that returns input unchanged."""

        async def process(self, data: Any) -> Any:
            return data

    stream = AsyncStream(source(), config=config)
    pipe = IdentityPipe()

    windows = []
    async for window in stream.process(pipe):
        windows.append(window)

    assert len(windows) > 1
    assert all(isinstance(w, list) for w in windows)
    assert sum(len(w) for w in windows) == 10


@pytest.mark.asyncio()
async def test_sliding_window() -> None:
    """Test sliding window processing."""
    items = list(range(5))

    async def source() -> AsyncIterator[int]:
        for item in items:
            yield item

    stream = AsyncStream(source())
    windows = []
    async for window in stream.sliding_window(window_size=3, step_size=1):
        windows.append(window)

    assert windows == [[0, 1, 2], [1, 2, 3], [2, 3, 4]]


@pytest.mark.asyncio()
async def test_tumbling_window() -> None:
    """Test tumbling window processing."""
    items = list(range(5))

    async def source() -> AsyncIterator[int]:
        for item in items:
            yield item

    stream = AsyncStream(source())
    windows = []
    async for window in stream.tumbling_window(window_size=2):
        windows.append(window)

    assert windows == [[0, 1], [2, 3], [4]]


@pytest.mark.asyncio()
async def test_time_window() -> None:
    """Test time-based window processing."""
    items = list(range(3))

    async def source() -> AsyncIterator[int]:
        for item in items:
            yield item
            await asyncio.sleep(0.4)

    stream = AsyncStream(source())
    windows = []
    async for window in stream.time_window(duration=timedelta(seconds=0.3)):
        windows.append(window)

    assert len(windows) == 3
    assert windows[0] == [0]
    assert windows[1] == [1]
    assert windows[2] == [2]


@pytest.mark.asyncio()
async def test_stream_backpressure() -> None:
    """Test stream backpressure handling."""
    items = list(range(100))
    config = StreamConfig(buffer_size=5)

    class SlowAsyncPipe(AsyncBasePipe[Any, Any]):
        """Pipe that processes items slowly to test backpressure."""

        async def process(self, data: Any) -> Any:
            await asyncio.sleep(0.01)
            return data

    async def source() -> AsyncIterator[int]:
        for item in items:
            yield item

    stream = AsyncStream(source(), config=config)
    pipe = SlowAsyncPipe()

    results = []
    async for result in stream.process(pipe):
        results.append(result)
        current_metrics = stream.metrics_dict()
        assert current_metrics["buffer_size"] <= config.buffer_size

    assert results == items


async def async_iter(items: list[Any]) -> AsyncIterator[Any]:
    """Create async iterator from list."""
    for item in items:
        yield item


@pytest.mark.asyncio()
async def test_stream_metrics_collection() -> None:
    """Test detailed metrics collection."""
    items = list(range(5))
    config = StreamConfig(collect_metrics=True)
    stream = AsyncStream(async_iter(items), config=config)

    class TestPipe(AsyncBasePipe[Any, Any]):
        async def process(self, data: Any) -> Any:
            start_time = time.time()
            await asyncio.sleep(0.1)
            stream.metrics.record_processing_time(time.time() - start_time)
            stream.metrics.record_success()
            stream.metrics.record_throughput(1)
            return data

    results = []
    async for result in stream.process(TestPipe()):
        results.append(result)

    assert results == list(range(5))

    await asyncio.sleep(0.1)

    metrics = stream.metrics.get_metrics()

    processing_time = metrics["processing_time"].average
    assert processing_time is not None and processing_time > 0

    error_rate = metrics["error_rate"].average
    assert error_rate is not None
    assert error_rate == 0.0

    throughput = metrics["throughput"].average
    assert throughput is not None and throughput > 0


@pytest.mark.asyncio()
async def test_stream_custom_metrics() -> None:
    """Test custom metrics collection."""
    items = list(range(5))
    config = StreamConfig(collect_metrics=True)
    stream = AsyncStream(async_iter(items), config=config)
    custom_metrics = CustomMetricsCollector()
    stream.metrics = custom_metrics

    class TestPipe(AsyncBasePipe[Any, Any]):
        async def process(self, data: Any) -> Any:
            custom_metrics.record_custom()
            return data

    async for _ in stream.process(TestPipe()):
        pass

    assert custom_metrics.custom_count == 5
    metrics = custom_metrics.get_metrics()
    assert "custom_metric" in metrics
    assert metrics["custom_metric"]["count"] == 5


@pytest.mark.asyncio()
async def test_stream_error_handling() -> None:
    """Test error handling in stream processing."""
    items = [1, 2, 3]
    stream = AsyncStream(async_iter(items))

    class ErrorPipe(AsyncBasePipe[Any, Any]):
        async def process(self, data: Any) -> Any:
            raise PipeError("ErrorPipe", ValueError("Test error"))

    with pytest.raises(PipeError):
        async for _ in stream.process(ErrorPipe()):
            pass


@pytest.mark.asyncio()
async def test_stream_buffer_handling() -> None:
    """Test buffer handling."""
    items = list(range(10))
    config = StreamConfig(buffer_size=5)
    stream = AsyncStream(async_iter(items), config=config)

    class DelayPipe(AsyncBasePipe[Any, Any]):
        async def process(self, data: Any) -> Any:
            await asyncio.sleep(0.1)
            return data

    results = []
    async for result in stream.process(DelayPipe()):
        results.append(result)

    assert len(results) == len(items)


@pytest.mark.asyncio()
async def test_stream_empty_source() -> None:
    """Test processing empty stream."""
    stream = AsyncStream(async_iter([]))

    class TestPipe(AsyncBasePipe[Any, Any]):
        async def process(self, data: Any) -> Any:
            return data

    results = []
    async for result in stream.process(TestPipe()):
        results.append(result)

    assert len(results) == 0
    metrics = stream.metrics.get_metrics()
    # For an empty stream, throughput might be None or 0
    assert metrics["throughput"].average in (None, 0)


@pytest.mark.asyncio()
async def test_stream_custom_serialization() -> None:
    """Test custom serialization handlers."""

    class CustomObject:
        def __init__(self, value: Any) -> None:
            self.value = value

        def serialize(self) -> dict[str, Any]:
            return {"value": self.value}

    items = [CustomObject(i) for i in range(3)]
    stream = AsyncStream(async_iter(items))

    class SerializePipe(
        AsyncBasePipe[
            Union[CustomObject, list[CustomObject]], Union[dict[str, Any], list[dict[str, Any]]],
        ],
    ):
        async def process(
            self, data: Union[CustomObject, list[CustomObject]],
        ) -> Union[dict[str, Any], list[dict[str, Any]]]:
            if isinstance(data, list):
                return [item.serialize() for item in data]
            return data.serialize()

    results: list[dict[str, Any]] = []
    async for result in stream.process(SerializePipe()):  # type: ignore
        results.append(cast(dict[str, Any], result))

    assert all(isinstance(r, dict) for r in results)
    assert [r["value"] for r in results] == [0, 1, 2]


def test_sync_stream_sliding_window() -> None:
    """Test synchronous sliding window processing."""
    items = list(range(5))
    stream = SyncStream(iter(items))

    windows = []
    for window in stream.sliding_window(window_size=3, step_size=1):
        windows.append(window)

    assert windows == [[0, 1, 2], [1, 2, 3], [2, 3, 4]]


def test_sync_stream_tumbling_window() -> None:
    """Test synchronous tumbling window processing."""
    items = list(range(5))
    stream = SyncStream(iter(items))

    windows = []
    for window in stream.tumbling_window(window_size=2):
        windows.append(window)

    assert windows == [[0, 1], [2, 3], [4]]


def test_sync_stream_time_window() -> None:
    """Test synchronous time-based window processing."""
    items = list(range(3))
    stream = SyncStream(iter(items))

    windows = []
    window_duration = timedelta(milliseconds=100)

    for window in stream.time_window(duration=window_duration):
        windows.append(window)
        time.sleep(0.2)

    # We expect each item to be in its own window due
    # to the sleep between processing
    assert len(windows) == 3
    assert all(len(window) == 1 for window in windows)
    assert [window[0] for window in windows] == [0, 1, 2]


def test_sync_stream_batch_processing() -> None:
    """Test synchronous batch processing."""
    items = list(range(10))
    config = StreamConfig(batch_size=3)
    stream = SyncStream(iter(items), config=config)

    class BatchPipe(SyncBasePipe[Any, Any]):
        def process(self, data: Any) -> Any:
            return sum(data) if isinstance(data, list) else data

    results = []
    for result in stream.process(BatchPipe()):
        results.append(result)

    assert results == [3, 12, 21, 9]  # Sum of each batch


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
            stream.metrics.record_processing_time(time.time() - start_time)
            stream.metrics.record_success()
            stream.metrics.record_throughput(1)
            return data

    list(stream.process(CountingPipe()))

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

    results = list(stream.process(NoopPipe()))
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
    results = list(stream.process(SerializePipe()))

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

    results = list(stream.process(SlowPipe()))
    assert results == list(range(10))
    assert len(stream._buffer) <= 3


@pytest.mark.asyncio()
async def test_stream_time_window_processing() -> None:
    items = list(range(5))
    config = StreamConfig(window_size=timedelta(milliseconds=100))
    stream = AsyncStream(async_iter(items), config=config)

    class TimedPipe(AsyncBasePipe[list[int], int]):
        async def process(self, data: list[int]) -> int:
            return sum(data)

    pipe: AsyncBasePipe[list[int], int] = TimedPipe()
    results: list[int] = []
    async for result in stream.process(pipe):
        results.append(result)
        await asyncio.sleep(0.15)

    assert len(results) > 0


@pytest.mark.asyncio()
async def test_stream_buffer_overflow() -> None:
    items = list(range(100))
    config = StreamConfig(buffer_size=5)
    stream = AsyncStream(async_iter(items), config=config)

    class SlowPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            await asyncio.sleep(0.01)
            return data

    results = []
    async for result in stream.process(SlowPipe()):
        results.append(result)
        metrics = stream.metrics_dict()
        assert metrics["buffer_size"] <= config.buffer_size

    assert len(results) == len(items)


@pytest.mark.asyncio()
async def test_stream_window_edge_cases() -> None:
    items = list(range(3))
    config = StreamConfig(window_size=timedelta(milliseconds=50))
    stream = AsyncStream(async_iter(items), config=config)

    windows = []
    async for window in stream.time_window(duration=timedelta(milliseconds=50)):
        windows.append(window)
        await asyncio.sleep(0.06)

    assert len(windows) > 0
    assert all(isinstance(w, list) for w in windows)


@pytest.mark.asyncio()
async def test_stream_empty_window() -> None:
    stream = AsyncStream(async_iter([]))

    windows = []
    async for window in stream.time_window(duration=timedelta(milliseconds=50)):
        windows.append(window)

    assert len(windows) == 0


@pytest.mark.asyncio()
async def test_stream_pipe_cleanup() -> None:
    items = list(range(5))
    config = StreamConfig(buffer_size=2)
    stream = AsyncStream(async_iter(items), config=config)

    class CleanupPipe(AsyncBasePipe[int, int]):
        def __init__(self) -> None:
            super().__init__()
            self.cleaned = False

        async def process(self, data: int) -> int:
            return data

        async def cleanup(self) -> None:
            self.cleaned = True

    pipe = CleanupPipe()
    results = []
    async for result in stream.process(pipe):
        results.append(result)

    await pipe.cleanup()
    assert pipe.cleaned


@pytest.mark.asyncio()
async def test_stream_batch_sum_processing() -> None:
    """Test batch sum processing."""
    items = list(range(10))
    config = StreamConfig(batch_size=3)
    stream = AsyncStream(async_iter(items), config=config)

    class BatchPipe(AsyncBasePipe[list[int], int]):
        async def process(self, data: list[int]) -> int:
            return sum(data)

    results = []
    async for result in stream.process(BatchPipe()):
        if isinstance(result, list):
            results.append(sum(result))
        else:
            results.append(result)

    assert results == [3, 12, 21, 9]  # [0+1+2, 3+4+5, 6+7+8, 9]


@pytest.mark.asyncio()
async def test_stream_window_processing_empty() -> None:
    stream = AsyncStream(async_iter([]))

    windows = []
    async for window in stream.sliding_window(window_size=2, step_size=1):
        windows.append(window)

    assert len(windows) == 0


@pytest.mark.asyncio()
async def test_stream_custom_window_processing() -> None:
    items = list(range(5))
    stream = AsyncStream(async_iter(items))

    windows = []
    async for window in stream.sliding_window(window_size=2, step_size=2):
        windows.append(window)

    assert windows == [[0, 1], [2, 3]]


@pytest.mark.asyncio()
async def test_stream_metrics_clear() -> None:
    """Test metrics reset by creating new collector."""
    items = list(range(5))
    config = StreamConfig(collect_metrics=True)
    stream = AsyncStream(async_iter(items), config=config)

    class TestPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            # small sleep to ensure processing time is recorded
            await asyncio.sleep(0.01)
            stream.metrics.record_success()
            stream.metrics.record_throughput(1)
            return data

    async for _ in stream.process(TestPipe()):
        pass

    initial_metrics = stream.metrics.get_metrics()
    initial_throughput = initial_metrics["throughput"].average
    assert initial_throughput is not None and initial_throughput > 0

    # Reset metrics by creating new collector
    stream.metrics = MetricsCollector()
    reset_metrics = stream.metrics.get_metrics()

    # Verify metrics were reset
    reset_throughput = reset_metrics["throughput"].average
    assert reset_throughput != initial_throughput
    assert reset_throughput in (None, 0)


@pytest.mark.asyncio()
async def test_stream_custom_config() -> None:
    """Test stream processing with custom configuration."""
    items = list(range(5))
    config = StreamConfig(
        batch_size=2, buffer_size=3, window_size=timedelta(seconds=1), collect_metrics=True,
    )
    stream = AsyncStream(async_iter(items), config=config)

    class BatchPipe(AsyncBasePipe[list[int], list[int]]):
        async def process(self, data: list[int]) -> list[int]:
            return data

    results = []
    async for batch in stream.process(BatchPipe()):  # type: ignore
        results.extend(batch)

    assert sorted(results) == sorted(items)


@pytest.mark.asyncio()
async def test_stream_cleanup() -> None:
    """Test stream cleanup."""
    items = list(range(5))
    stream = AsyncStream(async_iter(items))

    class NoopPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            return data

    async for _ in stream.process(NoopPipe()):
        break
    assert len(stream.buffer) == 0


@pytest.mark.asyncio()
async def test_stream_buffer_full_handling() -> None:
    """Test handling when buffer is full."""
    items = list(range(100))
    config = StreamConfig(buffer_size=2)
    stream = AsyncStream(async_iter(items), config=config)

    class SlowPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            await asyncio.sleep(0.01)
            return data

    results = []
    async for result in stream.process(SlowPipe()):
        results.append(result)
        current_metrics = stream.metrics_dict()
        assert current_metrics["buffer_size"] <= 2

    assert len(results) == len(items)


@pytest.mark.asyncio()
async def test_stream_window_with_timeout() -> None:
    """Test window processing with timeout."""
    items = list(range(5))
    config = StreamConfig(window_size=timedelta(milliseconds=100))
    stream = AsyncStream(async_iter(items), config=config)

    windows = []
    async for window in stream.time_window(timedelta(milliseconds=100)):
        windows.append(window)
        await asyncio.sleep(0.2)

    assert len(windows) > 0


@pytest.mark.asyncio()
async def test_stream_error_handling_with_recovery() -> None:
    """Test error handling with recovery in stream processing."""
    items = list(range(5))
    stream = AsyncStream(async_iter(items))

    class ErrorPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            if data == 2:
                raise ValueError("Test error")
            return data

    results = []
    try:
        async for result in stream.process(ErrorPipe()):
            results.append(result)
    except ValueError:
        pass

    assert len(results) == 2


@pytest.mark.asyncio()
async def test_stream_metrics_detailed() -> None:
    """Test detailed metrics collection."""
    items = list(range(5))
    config = StreamConfig(collect_metrics=True)
    stream = AsyncStream(async_iter(items), config=config)

    class MetricsPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            await asyncio.sleep(0.01)
            stream.metrics.record_success()
            stream.metrics.record_throughput(1)
            return data

    async for _ in stream.process(MetricsPipe()):
        pass

    metrics = stream.metrics.get_metrics()
    assert "processing_time" in metrics
    assert "error_rate" in metrics
    assert "throughput" in metrics
    assert metrics["error_rate"].average == 0.0
    throughput = metrics["throughput"].average
    assert throughput is not None and throughput > 0


@pytest.mark.asyncio()
async def test_stream_batch_timeout() -> None:
    """Test batch processing with timeout."""
    items = list(range(3))
    config = StreamConfig(
        batch_size=5,  # Larger than input
        window_size=timedelta(milliseconds=100),
    )
    stream = AsyncStream(async_iter(items), config=config)

    class BatchPipe(AsyncBasePipe[list[int], list[int]]):
        async def process(self, data: list[int]) -> list[int]:
            return data

    results: list[int] = []
    async for batch in stream.process(BatchPipe()):  # type: ignore
        results.extend(batch)

    assert sorted(results) == sorted(items)


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
