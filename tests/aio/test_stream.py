"""Tests for asynchronous stream processing."""
import asyncio
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Any

import pytest

from rivusio.aio.pipeline import AsyncBasePipe
from rivusio.aio.stream import AsyncStream
from rivusio.config.stream import StreamConfig
from rivusio.core.exceptions import PipeError


async def async_iter(items: list[Any]) -> AsyncIterator[Any]:
    """Create an asynchronous iterator."""
    for item in items:
        yield item


@pytest.mark.asyncio()
async def test_stream_time_window_processing() -> None:
    """Test window-based processing."""
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
    """Test handling when buffer is full."""
    items = list(range(100))
    config = StreamConfig(buffer_size=5)
    stream = AsyncStream(async_iter(items), config=config)

    class SlowPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            await asyncio.sleep(0.01)
            return data

    results: list[int] = []
    async for result in stream.process(SlowPipe()):
        results.append(result)
        metrics = stream.metrics_dict()
        assert metrics["buffer_size"] <= config.buffer_size

    assert len(results) == len(items)


@pytest.mark.asyncio()
async def test_stream_window_edge_cases() -> None:
    """Test window processing edge cases."""
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
    """Test empty window processing."""
    stream = AsyncStream(async_iter([]))

    windows = []
    async for window in stream.time_window(duration=timedelta(milliseconds=50)):
        windows.append(window)

    assert len(windows) == 0


@pytest.mark.asyncio()
async def test_stream_pipe_cleanup() -> None:
    """Test pipe cleanup."""
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
    results: list[int] = []
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

    results: list[int] = []
    async for result in stream.process(BatchPipe()):
        results.append(result)

    assert results == [3, 12, 21, 9]  # [0+1+2, 3+4+5, 6+7+8, 9]


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
        batch_size=5,
        window_size=timedelta(milliseconds=100),
    )
    stream = AsyncStream(async_iter(items), config=config)

    class BatchPipe(AsyncBasePipe[list[int], list[int]]):
        async def process(self, data: list[int]) -> list[int]:
            return data

    results: list[int] = []
    async for batch in stream.process(BatchPipe()):
        results.extend(batch)

    assert sorted(results) == sorted(items)


@pytest.mark.asyncio()
async def test_stream_backpressure_handling() -> None:
    """Test stream backpressure with slow consumer."""
    items = list(range(20))
    config = StreamConfig(buffer_size=3)
    stream = AsyncStream(async_iter(items), config=config)

    class SlowConsumerPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            await asyncio.sleep(0.01)
            return data

    results: list[int] = []
    async for result in stream.process(SlowConsumerPipe()):
        results.append(result)
        metrics = stream.metrics_dict()
        assert metrics["buffer_size"] <= config.buffer_size

    assert len(results) == len(items)
    assert sorted(results) == items


@pytest.mark.asyncio()
async def test_stream_multiple_windows() -> None:
    """Test multiple consecutive time windows."""
    items = list(range(10))
    config = StreamConfig(window_size=timedelta(milliseconds=50))
    stream = AsyncStream(async_iter(items), config=config)

    windows: list[list[int]] = []
    async for window in stream.time_window(duration=timedelta(milliseconds=20)):
        windows.append(window)
        if len(windows) >= 1:
            break
        await asyncio.sleep(0.03)

    assert len(windows) == 1
    assert isinstance(windows[0], list)
    assert len(windows[0]) > 0


@pytest.mark.asyncio()
async def test_stream_metrics_recording() -> None:
    """Test detailed metrics recording during stream processing."""
    items = list(range(5))
    config = StreamConfig(collect_metrics=True)
    stream = AsyncStream(async_iter(items), config=config)

    class MetricsTestPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            if data % 2 == 0:
                stream.metrics.record_processing_time(0.01)
                await asyncio.sleep(0.01)
            else:
                stream.metrics.record_error()
            stream.metrics.record_throughput(1)
            return data

    results: list[int] = []
    async for result in stream.process(MetricsTestPipe()):
        results.append(result)

    metrics = stream.metrics_dict()
    assert "buffer_size" in metrics
    assert "metrics" in metrics
    assert "error_rate" in metrics["metrics"]
    assert "throughput" in metrics["metrics"]


@pytest.mark.asyncio()
async def test_stream_sliding_window() -> None:
    """Test sliding window processing."""
    items = list(range(10))
    stream = AsyncStream(async_iter(items))

    windows: list[list[int]] = []
    async for window in stream.sliding_window(window_size=3, step_size=2):
        windows.append(window)
        if len(windows) >= 2:
            break

    assert len(windows) == 2
    assert len(windows[0]) == 3
    assert len(windows[1]) == 3
    assert windows[0] != windows[1]


@pytest.mark.asyncio()
async def test_stream_error_propagation() -> None:
    """Test error propagation in stream processing."""
    items = list(range(5))
    stream = AsyncStream(async_iter(items))

    class ErrorPropagationPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            if data == 3:
                raise ValueError("Test error at value 3")
            return data

    results: list[int] = []
    with pytest.raises(PipeError) as exc_info:
        async for result in stream.process(ErrorPropagationPipe()):
            results.append(result)

    assert "Test error at value 3" in str(exc_info.value)
    assert len(results) == 3
    assert results == [0, 1, 2]
