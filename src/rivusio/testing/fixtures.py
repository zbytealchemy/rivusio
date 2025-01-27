"""Test fixtures and utilities for Rivusio."""
import asyncio
from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from typing import Any, Optional, TypeVar

import pytest

from rivusio import AsyncBasePipe, AsyncStream, StreamConfig, SyncBasePipe, SyncStream

T = TypeVar("T")


class AsyncMockPipe(AsyncBasePipe[Any, Any]):
    """Async mock pipe for testing."""

    def __init__(
        self,
        return_value: Any = None,
        error: Optional[Exception] = None,
        delay: float = 0,
    ) -> None:
        """Initialize mock pipe.

        Args:
        ----
            return_value: Value to return
            error: Error to raise
            delay: Processing delay in seconds

        """
        super().__init__()
        self.return_value = return_value
        self.error = error
        self.delay = delay
        self.calls: list[Any] = []

    async def process(self, data: Any) -> Any:
        """Process data through mock pipe."""
        self.calls.append(data)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return self.return_value if self.return_value is not None else data


class SyncMockPipe(SyncBasePipe[Any, Any]):
    """Sync mock pipe for testing."""

    def __init__(
        self,
        return_value: Any = None,
        error: Optional[Exception] = None,
        delay: float = 0,
    ) -> None:
        """Initialize mock pipe.

        Args:
        ----
            return_value: Value to return
            error: Error to raise
            delay: Processing delay in seconds

        """
        super().__init__()
        self.return_value = return_value
        self.error = error
        self.delay = delay
        self.calls: list[Any] = []

    def process(self, data: Any) -> Any:
        """Process data through mock pipe."""
        self.calls.append(data)
        if self.delay:
            import time

            time.sleep(self.delay)
        if self.error:
            raise self.error
        return self.return_value if self.return_value is not None else data


async def mock_async_source(items: list[T], delay: float = 0) -> AsyncIterator[T]:
    """Create a mock async stream source.

    Args:
    ----
        items: Items to yield
        delay: Delay between items in seconds

    Yields:
    ------
        Items from the list

    """
    for item in items:
        if delay:
            await asyncio.sleep(delay)
        yield item


def mock_sync_source(items: list[T], delay: float = 0) -> Iterator[T]:
    """Create a mock sync stream source.

    Args:
    ----
        items: Items to yield
        delay: Delay between items in seconds

    Yields:
    ------
        Items from the list

    """
    for item in items:
        if delay:
            import time

            time.sleep(delay)
        yield item


@pytest.fixture()
def mock_async_pipe() -> Any:
    """Fixture for creating async mock pipes."""

    def _create_mock_pipe(
        return_value: Any = None, error: Optional[Exception] = None, delay: float = 0,
    ) -> AsyncMockPipe:
        return AsyncMockPipe(return_value, error, delay)

    return _create_mock_pipe


@pytest.fixture()
def mock_sync_pipe() -> Any:
    """Fixture for creating sync mock pipes."""

    def _create_mock_pipe(
        return_value: Any = None, error: Optional[Exception] = None, delay: float = 0,
    ) -> SyncMockPipe:
        return SyncMockPipe(return_value, error, delay)

    return _create_mock_pipe


@pytest.fixture()
def mock_async_stream() -> Any:
    """Fixture for creating async mock streams."""

    def _create_mock_stream(
        items: list[Any], config: Optional[StreamConfig] = None, delay: float = 0,
    ) -> AsyncStream[Any]:
        return AsyncStream(mock_async_source(items, delay), config=config)

    return _create_mock_stream


@pytest.fixture()
def mock_sync_stream() -> Any:
    """Fixture for creating sync mock streams."""

    def _create_mock_stream(
        items: list[Any], config: Optional[StreamConfig] = None, delay: float = 0,
    ) -> SyncStream[Any]:
        return SyncStream(mock_sync_source(items, delay), config=config)

    return _create_mock_stream


@pytest.fixture()
def assert_processing_time() -> Any:
    """Fixture for asserting processing time."""

    def _assert_processing_time(
        start_time: datetime, expected_duration: float, tolerance: float = 0.1,
    ) -> None:
        duration = (datetime.now() - start_time).total_seconds()
        assert abs(duration - expected_duration) <= tolerance

    return _assert_processing_time
