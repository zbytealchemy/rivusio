"""Stream processing implementation.

This module provides the core stream processing functionality, supporting both
synchronous and asynchronous data streams with features like:
- Single item processing
- Batch processing
- Time-based window processing
- Error handling with retries
- Configurable processing parameters
"""
import asyncio
import logging
import time
from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import timedelta
from typing import (
    Any,
    Generic,
    Optional,
    TypeVar,
    Union,
    cast,
)

from pydantic import BaseModel, ConfigDict, field_validator

from rivusio.core.exceptions import PipeError
from rivusio.core.pipe import AsyncBasePipe, OutputType, SyncBasePipe
from rivusio.monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)

T = TypeVar("T")
BatchT = TypeVar("BatchT", bound=Sequence[Any])
InputType = Union[T, BatchT]


class StreamConfig(BaseModel):
    """Configuration for stream processing behavior.

    Controls various aspects of stream processing including retry behavior,
    timeouts, batch sizes, and window settings.

    Attributes:
    ----------
        name: Optional name for the stream instance
        retry_attempts: Number of retry attempts for failed operations
        retry_delay: Initial delay between retries in seconds
        retry_backoff: Multiplier for retry delay after each attempt
        timeout: Operation timeout in seconds
        batch_size: Number of items to process in each batch
        window_size: Time window duration for window-based processing
        buffer_size: Maximum number of items to buffer
        collect_metrics: Whether to collect processing metrics

    Example:
    -------
        ```python
        config = StreamConfig(
            name="sensor_stream",
            batch_size=100,
            window_size=timedelta(minutes=5),
            buffer_size=1000
        )
        ```

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: Optional[str] = None
    retry_attempts: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    timeout: float = 30.0
    batch_size: int = 1
    window_size: timedelta = timedelta(seconds=0)
    buffer_size: int = 1000
    collect_metrics: bool = True
    skip_none: bool = True

    @field_validator("retry_attempts")
    @classmethod
    def validate_retry_attempts(cls, v: int) -> int:
        """Validate retry attempts."""
        if v < 0:
            raise ValueError("retry_attempts must be non-negative")
        return v

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        """Validate batch size."""
        if v < 1:
            raise ValueError("batch_size must be positive")
        return v


class AsyncStream(Generic[T]):
    """An asynchronous stream of data that can be processed through a pipeline.

    Provides functionality for processing data streams with support for batching,
    windowing, and error handling. Designed for async operations.

    Attributes:
    ----------
        source: The async iterator providing the data
        config: Stream processing configuration
        metrics: Optional metrics collector for monitoring

    Example:
    -------
        ```python
        async def data_source():
            for i in range(100):
                yield {"value": i}

        config = StreamConfig(batch_size=10)
        stream = AsyncStream(data_source(), config=config)

        async def process_batch(items):
            return [item["value"] * 2 for item in items]

        async for result in stream.process(process_batch):
            print(f"Processed batch: {result}")
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
        ----
            source: Source iterator providing data
            config: Stream processing configuration
            metrics: Optional metrics collector for monitoring

        """
        self.source = source
        self.config = config or StreamConfig()
        self.metrics = metrics or MetricsCollector()
        self._buffer: list[T] = []
        self._window_buffer: list[T] = []
        self._last_window_time = time.time()

    @property
    def buffer(self) -> list[T]:
        """Get buffer."""
        return self._buffer

    def metrics_dict(self) -> dict:
        """Get current metrics including buffer size."""
        return {
            "buffer_size": len(self._buffer),
            "metrics": self.metrics.get_metrics() if self.metrics else {},
        }

    async def sliding_window(self, window_size: int, step_size: int) -> AsyncIterator[list[T]]:
        """Process items using sliding window.

        Args:
        ----
            window_size: Size of the sliding window
            step_size: Number of items to slide by

        Yields:
        ------
            List of items in the current window

        """
        window: list[T] = []
        async for item in self.source:
            window.append(item)
            if len(window) >= window_size:
                yield window[-window_size:]
                window = window[step_size:]

    async def tumbling_window(self, window_size: int) -> AsyncIterator[list[T]]:
        """Process items using tumbling window.

        Args:
        ----
            window_size: Size of the tumbling window

        Yields:
        ------
            List of items in the current window

        """
        window: list[T] = []
        async for item in self.source:
            window.append(item)
            if len(window) >= window_size:
                yield window
                window = []
        if window:
            yield window

    async def time_window(self, duration: timedelta) -> AsyncIterator[list[T]]:
        """Process items using time-based window.

        Args:
        ----
            duration: Time duration for the window

        Yields:
        ------
            List of items collected within the time window

        """
        window: list[T] = []
        start_time = time.time()
        async for item in self.source:
            current_time = time.time()
            if current_time - start_time >= duration.total_seconds():
                if window:
                    yield window
                    window = []
                start_time = current_time
            window.append(item)
        if window:
            yield window

    async def process(
        self, pipe: AsyncBasePipe[InputType, OutputType | BatchT],
    ) -> AsyncIterator[Any]:
        """Process the stream through the provided pipeline.

        Automatically selects the appropriate processing mode based on configuration:
        - Single item mode if batch_size=1 and window_size=0
        - Batch mode if batch_size > 1
        - Window mode if window_size > 0

        Args:
        ----
            pipe: Pipeline to process items/batches/windows

        Yields:
        ------
            Processed items/batches/windows depending on processing mode

        Raises:
        ------
            PipeError: If processing fails and retries are exhausted

        Example:
        -------
            ```python
            from rivusio.streams import AsyncStream, StreamConfig
            from rivusio.core import AsyncBasePipe

            async def data_source():
                for i in range(5):
                    yield {"value": i}

            class MultiplyPipe(AsyncBasePipe[Dict, Dict]):
                async def process(self, data: Dict) -> Dict:
                    return {"value": data["value"] * 2}

            config = StreamConfig(batch_size=2)
            stream = AsyncStream(data_source(), config=config)
            pipe = MultiplyPipe()

            async for result in stream.process(pipe):
                print(result)
            ```

        """
        if self.config.batch_size > 1:
            async for batch in self._process_batches(pipe):
                yield batch
        elif self.config.window_size.total_seconds() > 0:
            async for window in self._process_windows(pipe):
                yield window
        else:
            async for item in self.source:
                yield await pipe.process(item)

    async def _process_item(
        self, pipe: AsyncBasePipe[InputType, OutputType], item: T,
    ) -> Optional[OutputType]:
        """Process a single item with retry logic.

        Args:
        ----
            pipe: Pipeline to process the item
            item: Item to process

        Returns:
        -------
            Processed item or None if processing failed

        Raises:
        ------
            PipeError: If all retry attempts fail

        """
        for attempt in range(self.config.retry_attempts):
            try:
                result = await pipe(item)
                return result if not isinstance(result, list) else result[0]
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise PipeError(pipe.__class__.__name__, e) from e
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        return None

    async def _process_batches(self, pipe: AsyncBasePipe[BatchT, BatchT]) -> AsyncIterator[BatchT]:
        """Process items in batches.

        Args:
        ----
            pipe: Pipeline to process batches

        Yields:
        ------
            Processed batches of items

        Raises:
        ------
            PipeError: If batch processing fails

        """
        batch: list[T] = []
        async for item in self.source:
            batch.append(item)
            if len(batch) >= self.config.batch_size:
                try:
                    yield await pipe.process(cast(BatchT, batch))
                    batch = []
                except Exception as e:
                    raise PipeError(pipe.__class__.__name__, e) from e

        # Process remaining items if any
        if batch:
            try:
                yield await pipe.process(cast(BatchT, batch))
            except Exception as e:
                raise PipeError(pipe.__class__.__name__, e) from e

    async def _process_windows(self, pipe: AsyncBasePipe[BatchT, BatchT]) -> AsyncIterator[BatchT]:
        """Process items in time-based windows.

        Collects items into windows based on configured window_size.

        Args:
        ----
            pipe: Pipeline to process windows

        Yields:
        ------
            Processed windows of items

        Raises:
        ------
            PipeError: If window processing fails

        """
        async for item in self.source:
            current_time = time.time()
            if current_time - self._last_window_time >= self.config.window_size.total_seconds():
                if self._window_buffer:
                    try:
                        yield await pipe(cast(BatchT, self._window_buffer))
                    except Exception as e:
                        raise PipeError(pipe.__class__.__name__, e) from e
                    self._window_buffer = []
                self._last_window_time = current_time
            self._window_buffer.append(item)

        if self._window_buffer:
            try:
                yield await pipe(cast(BatchT, self._window_buffer))
            except Exception as e:
                raise PipeError(pipe.__class__.__name__, e) from e


class SyncStream(Generic[T]):
    """A synchronous stream of data that can be processed through a pipeline.

    Provides the same functionality as AsyncStream but for synchronous operations.
    Supports batching, windowing, and error handling for sync data sources.

    Attributes:
    ----------
        source: The iterator providing the data
        config: Stream processing configuration
        metrics: Optional metrics collector for monitoring

    Example:
    -------
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
        metrics: Optional[MetricsCollector] = None,
    ) -> None:
        """Initialize sync stream.

        Args:
        ----
            source: Source iterator providing data
            config: Stream processing configuration
            metrics: Optional metrics collector for monitoring

        """
        self.source = source
        self.config = config or StreamConfig()
        self.metrics = metrics or MetricsCollector()
        self._buffer: list[T] = []
        self._window_buffer: list[T] = []
        self._last_window_time = time.time()

    def process(self, pipe: SyncBasePipe[InputType, OutputType]) -> Iterator[OutputType]:
        """Process the stream through the provided pipeline.

        Synchronous version of AsyncStream.process().
        See AsyncStream.process() for detailed documentation.

        Args:
        ----
            pipe: Pipeline to process data through

        Yields:
        ------
            Processed items/batches/windows depending on processing mode

        Raises:
        ------
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
        """Process a single item with retry logic.

        Synchronous version of AsyncStream._process_item().
        See AsyncStream._process_item() for detailed documentation.
        """
        for attempt in range(self.config.retry_attempts):
            try:
                return pipe(item)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise PipeError(pipe.__class__.__name__, e) from e
                time.sleep(self.config.retry_delay * (attempt + 1))

        raise RuntimeError(f"Runtime error in: {pipe.__class__.__name__}")

    def _process_batches(self, pipe: SyncBasePipe[BatchT, BatchT]) -> Iterator[BatchT]:
        """Process items in batches.

        Args:
        ----
            pipe: Pipeline to process data through

        Yields:
        ------
            Processed batches of items

        """
        batch: list[T] = []

        for item in self.source:
            batch.append(item)
            if len(batch) >= self.config.batch_size:
                yield pipe(cast(BatchT, batch))
                batch = []

        # Process remaining items
        if batch:
            yield pipe(cast(BatchT, batch))

    def _process_windows(self, pipe: SyncBasePipe[BatchT, BatchT]) -> Iterator[BatchT]:
        """Process items in time-based windows.

        Synchronous version of AsyncStream._process_windows().
        See AsyncStream._process_windows() for detailed documentation.
        """
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
            yield pipe(batch)

    def sliding_window(self, window_size: int, step_size: int) -> Iterator[list[T]]:
        """Process items using sliding window.

        Args:
        ----
            window_size: Size of the window
            step_size: Number of items to slide window by

        Yields:
        ------
            List of items in current window

        """
        buffer: list[T] = []

        for item in self.source:
            buffer.append(item)
            if len(buffer) >= window_size:
                yield buffer[-window_size:]
                buffer = buffer[step_size:]

    def tumbling_window(self, window_size: int) -> Iterator[list[T]]:
        """Process items using tumbling window.

        Args:
        ----
            window_size: Size of the window

        Yields:
        ------
            List of items in current window

        """
        buffer: list[T] = []

        for item in self.source:
            buffer.append(item)
            if len(buffer) >= window_size:
                yield buffer
                buffer = []

        if buffer:  # Yield remaining items
            yield buffer

    def time_window(self, duration: timedelta) -> Iterator[list[T]]:
        """Process items using time-based window.

        Args:
        ----
            duration: Time duration for each window

        Yields:
        ------
            List of items in current window

        """
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
            time.sleep(duration.total_seconds())  # Force time separation between items

        if buffer:
            yield buffer
