
"""Sync parallel execution implementations."""

import types
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import cpu_count
from typing import Generic, Optional, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class ExecutionStrategyHandler(Generic[T, R]):
    """Base class for execution strategy handlers."""

    def execute(self, func: Callable[[T], R], data: list[T]) -> list[R]:
        """Execute function on data using the strategy."""
        raise NotImplementedError


class ThreadPoolStrategyHandler(ExecutionStrategyHandler[T, R]):
    """Thread pool execution strategy."""

    def __init__(self, max_workers: Optional[int] = None) -> None:
        """Initialize thread pool executor."""
        self.max_workers = max_workers or cpu_count()
        self._thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

    def __enter__(self) -> "ThreadPoolStrategyHandler[T, R]":
        """Initialize executor."""
        self._thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Shutdown executor."""
        if self._thread_pool:
            self._thread_pool.shutdown()

    def execute(self, func: Callable[[T], R], data: list[T]) -> list[R]:
        """Execute function on data using thread pool."""
        if not self._thread_pool:
            raise RuntimeError("Executor not initialized")
        return list(self._thread_pool.map(func, data))

    def shutdown(self) -> None:
        """Shutdown the thread pool."""
        self._thread_pool.shutdown()


class ProcessPoolStrategyHandler(ExecutionStrategyHandler[T, R]):
    """Process pool execution strategy."""

    def __init__(self, max_workers: Optional[int] = None, chunk_size: int = 1000) -> None:
        """Initialize process pool executor."""
        self.max_workers = max_workers or cpu_count()
        self.chunk_size = chunk_size
        self._process_pool = ProcessPoolExecutor(max_workers=self.max_workers)

    def __enter__(self) -> "ProcessPoolStrategyHandler[T, R]":
        """Return executor."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> None:
        """Shutdown executor."""
        if self._process_pool:
            self._process_pool.shutdown()

    def execute(self, func: Callable[[T], R], data: list[T]) -> list[R]:
        """Execute function on data using process pool."""
        if not self._process_pool:
            raise RuntimeError("Executor not initialized")
        return list(self._process_pool.map(func, data, chunksize=self.chunk_size))

    def shutdown(self) -> None:
        """Shutdown the process pool."""
        self._process_pool.shutdown()
