"""Asynchronous stream processing implementation."""

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Generic, Optional, cast

from rivusio.aio.pipeline import AsyncBasePipe
from rivusio.config.stream import StreamConfig
from rivusio.core.exceptions import PipeError
from rivusio.core.types import BatchT, OutputType, StreamType, T
from rivusio.monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)

InputType = StreamType


class AsyncStream(Generic[T]):
    """An asynchronous stream of data that can be processed through a pipeline.

    Provides functionality for processing data streams with support for batching,
    windowing, and error handling. Designed for async operations.

    Attributes:
        source: The async iterator providing the data
        config: Stream processing configuration
        metrics: Optional metrics collector for monitoring

    Example:
        ```python
        async def data_source():
            for i in range(100):
                yield {"value": i}

        config = StreamConfig(batch_size=10)
        stream = AsyncStream(data_source(), config=config)

        async def process_batch(items):
            return [item["value"] * 2 for item in items]

        async for result in stream.process(process_batch):
            print(result)
        ```
    """

    def __init__(
        self,
        source: AsyncIterator[T],
        config: Optional[StreamConfig] = None,
        metrics: Optional[MetricsCollector] = None,
    ) -> None:
        """Initialize async stream.

        Args:
            source: Source async iterator providing data
            config: Stream processing configuration
            metrics: Optional metrics collector for monitoring
        """
        self.source = source
        self.config = config or StreamConfig()
        self.metrics = metrics or MetricsCollector()
        self._buffer: list[T] = []
        self._window_buffer: list[T] = []
        self._last_window_time = asyncio.get_event_loop().time()
        self._closed = False

    async def close(self) -> None:
        """Close the stream and release resources."""
        self._buffer.clear()
        self._closed = True

    def is_closed(self) -> bool:
        """Check if the stream is closed."""
        return self._closed

    @property
    def buffer(self) -> list[T]:
        """Get buffer.

        Returns
            Current buffer
        """
        return self._buffer

    def metrics_dict(self) -> dict:
        """Get current metrics including buffer size.

        Returns
            Dictionary containing metrics and buffer size
        """
        return {
            "buffer_size": len(self._buffer),
            "metrics": self.metrics.get_metrics() if self.metrics else {},
        }

    async def process(
        self, pipe: AsyncBasePipe[InputType, OutputType],
    ) -> AsyncIterator[OutputType]:
        """Process the stream through the provided pipeline.

        Args:
            pipe: Pipeline to process data through

        Yields:
            Processed items/batches/windows depending on processing mode

        Raises:
            PipeError: If processing fails
            Exception: If pipe raises an unhandled exception
        """
        if self.config.batch_size > 1:
            async for result in self._process_batches(pipe):
                yield result
        elif self.config.window_size.total_seconds() > 0:
            async for result in self._process_windows(pipe):
                yield result
        else:
            async for item in self.source:
                try:
                    yield await self._process_item(pipe, item)
                except Exception as e:
                    raise PipeError(pipe.__class__.__name__, e) from e

    async def _process_item(
        self, pipe: AsyncBasePipe[InputType, OutputType], item: T,
    ) -> OutputType:
        """Process a single item with retry logic."""
        for attempt in range(self.config.retry_attempts):
            try:
                return await pipe(item)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise PipeError(pipe.__class__.__name__, e) from e
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        raise RuntimeError(f"Runtime error in: {pipe.__class__.__name__}")

    async def _process_batches(
        self, pipe: AsyncBasePipe[BatchT, BatchT],
    ) -> AsyncIterator[BatchT]:
        """Process items in batches."""
        batch: list[T] = []

        async for item in self.source:
            batch.append(item)
            if len(batch) >= self.config.batch_size:
                yield await pipe(cast(BatchT, batch))
                batch = []

        if batch:
            yield await pipe(cast(BatchT, batch))

    async def _process_windows(
        self, pipe: AsyncBasePipe[BatchT, BatchT],
    ) -> AsyncIterator[BatchT]:
        """Process items in time-based windows."""
        async for item in self.source:
            current_time = asyncio.get_event_loop().time()
            if (
                current_time - self._last_window_time
                >= self.config.window_size.total_seconds()
            ):
                if self._window_buffer:
                    yield await pipe(cast(BatchT, self._window_buffer))
                    self._window_buffer = []
                self._last_window_time = current_time
            self._window_buffer.append(item)

        if self._window_buffer:
            yield await pipe(cast(BatchT, self._window_buffer))

    async def sliding_window(
        self, window_size: int, step_size: int,
    ) -> AsyncIterator[list[T]]:
        """Process items using sliding window."""
        buffer: list[T] = []

        async for item in self.source:
            buffer.append(item)
            if len(buffer) >= window_size:
                yield buffer[-window_size:]
                buffer = buffer[step_size:]

    async def tumbling_window(self, window_size: int) -> AsyncIterator[list[T]]:
        """Process items using tumbling window."""
        buffer: list[T] = []

        async for item in self.source:
            buffer.append(item)
            if len(buffer) >= window_size:
                yield buffer
                buffer = []

        if buffer:  # Yield remaining items
            yield buffer

    async def time_window(self, duration: timedelta) -> AsyncIterator[list[T]]:
        """Process items using time-based window."""
        buffer: list[T] = []
        window_start = asyncio.get_event_loop().time()

        async for item in self.source:
            current_time = asyncio.get_event_loop().time()
            if current_time - window_start >= duration.total_seconds():
                if buffer:
                    yield buffer
                buffer = []
                window_start = current_time
            buffer.append(item)
            await asyncio.sleep(0)

        if buffer:
            yield buffer
