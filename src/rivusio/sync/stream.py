"""Synchronous stream processing implementation."""

import logging
import time
import types
from collections.abc import Iterator
from datetime import timedelta
from typing import Generic, Optional, cast

from rivusio.config.stream import StreamConfig
from rivusio.core.exceptions import PipeError
from rivusio.core.types import BatchT, OutputType, StreamType, T
from rivusio.monitoring.metrics import MetricsCollector
from rivusio.sync.pipeline import SyncBasePipe

logger = logging.getLogger(__name__)

InputType = StreamType


class SyncStream(Generic[T]):
    """A synchronous stream of data that can be processed through a pipeline.

    Provides the same functionality as AsyncStream but for synchronous operations.
    Supports batching, windowing, and error handling for sync data sources.

    Attributes:
        source: The iterator providing the data
        config: Stream processing configuration
        metrics: Optional metrics collector for monitoring

    Example:
        ```python
        def data_source():
            for i in range(100):
                yield {"value": i}

        config = StreamConfig(window_size=timedelta(seconds=30))
        stream = SyncStream(data_source(), config=config)

        def process_window(items):
            return [sum(item["value"] for item in items)]

        for result in stream.process(process_window):
            print(f"Window sum: {result[0]}")
        ```
    """

    def __init__(
        self,
        source: Iterator[T],
        config: Optional[StreamConfig] = None,
    ) -> None:
        """Initialize the stream with a data source and optional configuration."""
        self.source = source
        self.config = config or StreamConfig()
        self.metrics = MetricsCollector() if self.config.collect_metrics else None
        self._buffer: list[T] = []
        self._window_buffer: list[T] = []
        self._last_window_time: float = time.time()
        self._closed = False

    def __iter__(self) -> Iterator[T]:
        """Make the stream iterable."""
        try:
            if self._closed:
                yield from iter([])
            yield from self.source
        except Exception:
            self.close()
            raise

    def __enter__(self) -> "SyncStream[T]":
        """Enter the context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit the context manager."""
        self.close()

    def close(self) -> None:
        """Close the stream and release resources."""
        self._buffer.clear()
        self._closed = True

    def is_closed(self) -> bool:
        """Check if the stream is closed."""
        return self._closed

    def process(self, pipe: SyncBasePipe[InputType, OutputType]) -> Iterator[OutputType]:
        """Process the stream through the provided pipeline.

        Synchronous version of AsyncStream.process().
        See AsyncStream.process() for detailed documentation.

        Args:
            pipe: Pipeline to process data through

        Yields:
            Processed items/batches/windows depending on processing mode

        Raises:
            PipeError: If processing fails
            Exception: If pipe raises an unhandled exception
        """
        if self.config.batch_size > 1:
            yield from self._process_batches(pipe)
        elif self.config.window_size.total_seconds() > 0:
            yield from self._process_windows(pipe)
        else:
            for item in self.source:
                try:
                    yield self._process_item(pipe, item)
                except Exception as e:
                    raise PipeError(pipe.__class__.__name__, e) from e

    def _process_item(self, pipe: SyncBasePipe[InputType, OutputType], item: T) -> OutputType:
        """Process a single item with retry logic."""
        for attempt in range(self.config.retry_attempts):
            try:
                return pipe(item)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise PipeError(pipe.__class__.__name__, e) from e
                time.sleep(self.config.retry_delay * (attempt + 1))

        raise RuntimeError(f"Runtime error in: {pipe.__class__.__name__}")

    def _process_batches(self, pipe: SyncBasePipe[BatchT, BatchT]) -> Iterator[BatchT]:
        """Process items in batches."""
        batch: list[T] = []

        for item in self.source:
            batch.append(item)
            if len(batch) >= self.config.batch_size:
                yield pipe(cast(BatchT, batch))
                batch = []

        if batch:
            yield pipe(cast(BatchT, batch))

    def _process_windows(self, pipe: SyncBasePipe[BatchT, BatchT]) -> Iterator[BatchT]:
        """Process items in time-based windows."""
        for item in self.source:
            current_time = time.time()
            if current_time - self._last_window_time >= self.config.window_size.total_seconds():
                if self._window_buffer:
                    batch: BatchT = cast(BatchT, self._window_buffer)
                    yield pipe(batch)
                    self._window_buffer = []
                self._last_window_time = current_time
            self._window_buffer.append(item)

        if self._window_buffer:
            yield pipe(cast(BatchT, self._window_buffer))

    def sliding_window(self, window_size: int, step_size: int) -> Iterator[list[T]]:
        """Process items using sliding window."""
        buffer: list[T] = []

        for item in self.source:
            buffer.append(item)
            if len(buffer) >= window_size:
                yield buffer[-window_size:]
                buffer = buffer[step_size:]

    def tumbling_window(self, window_size: int) -> Iterator[list[T]]:
        """Process items using tumbling window."""
        buffer: list[T] = []

        for item in self.source:
            buffer.append(item)
            if len(buffer) >= window_size:
                yield buffer
                buffer = []

        if buffer:  # Yield remaining items
            yield buffer

    def time_window(self, duration: timedelta) -> Iterator[list[T]]:
        """Process items using time-based window."""
        buffer: list[T] = []
        window_start = time.time()

        for item in self.source:
            current_time = time.time()
            if current_time - window_start >= duration.total_seconds():
                if buffer:
                    yield buffer
                buffer = []
                window_start = current_time
            buffer.append(item)

        if buffer:
            yield buffer

    def metrics_dict(self) -> dict:
        """Get current metrics including buffer size.

        Returns
            Dictionary containing metrics and buffer size
        """
        return {
            "buffer_size": len(self._buffer),
            "metrics": self.metrics.get_metrics() if self.metrics else {},
        }
