"""Parallel execution strategies for pipelines."""
import asyncio
import multiprocessing
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Any, Optional, TypeVar

T = TypeVar("T")
U = TypeVar("U")


class ExecutionStrategy(str, Enum):
    """Execution strategy for parallel processing."""

    # ayncio.gather for I/O-bound tasks
    GATHER = "gather"

    # ThreadPoolExecutor for I/O and light CPU tasks
    THREAD_POOL = "thread_pool"

    # ProcessPoolExecutor for CPU-intensive tasks
    PROCESS_POOL = "process_pool"


@dataclass
class ParallelConfig:
    """Configuration for parallel execution."""

    strategy: ExecutionStrategy = ExecutionStrategy.GATHER
    max_workers: Optional[int] = None
    chunk_size: int = 1000  # For process pool batching

    def __post_init__(self) -> None:
        """Set default max_workers based on strategy."""
        if self.max_workers is None:
            if self.strategy == ExecutionStrategy.PROCESS_POOL:
                self.max_workers = max(1, multiprocessing.cpu_count() - 1)
            elif self.strategy == ExecutionStrategy.THREAD_POOL:
                self.max_workers = min(32, (multiprocessing.cpu_count() or 1) * 4)
            else:
                self.max_workers = None


def _worker(func: Callable[..., Any], item: Any) -> Any:
    """Run async function in a thread with a new event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(func(item))
    finally:
        loop.close()


def _process_worker(process_func: Callable[..., Any], item: Any) -> Any:
    """Process a single item in a worker process."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(process_func(item))
    finally:
        loop.close()


def _map_worker(worker: Callable[..., Any], chunk: list[Any]) -> list[Any]:
    """Map worker function over a chunk of data."""
    return [worker(item) for item in chunk]


def chunk_data(data: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split data into chunks of specified size."""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


class ExecutionStrategyHandler(ABC):
    """Abstract base class for execution strategies."""

    @abstractmethod
    async def execute(self, func: Callable[..., Any], data: list[Any]) -> list[Any]:
        """Execute the function on the data using the specific strategy."""


class GatherStrategyHandler(ExecutionStrategyHandler):
    """Handler for asyncio.gather strategy."""

    async def execute(self, func: Callable[..., Any], data: list[Any]) -> list[Any]:
        """Execute using asyncio.gather."""
        if not data:
            return []
        return await asyncio.gather(*[func(item) for item in data])


class ThreadPoolStrategyHandler(ExecutionStrategyHandler):
    """Handler for ThreadPoolExecutor strategy."""

    def __init__(self, max_workers: Optional[int] = None) -> None:
        """Initialize handler."""
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)

    async def execute(self, func: Callable[..., Any], data: list[Any]) -> list[Any]:
        """Execute using ThreadPoolExecutor."""
        if not data:
            return []
        loop = asyncio.get_event_loop()
        worker = partial(_worker, func)
        futures = [loop.run_in_executor(self._thread_pool, worker, item) for item in data]
        return await asyncio.gather(*futures)

    def shutdown(self) -> None:
        """Shutdown the thread pool."""
        self._thread_pool.shutdown()


class ProcessPoolStrategyHandler(ExecutionStrategyHandler):
    """Handler for ProcessPoolExecutor strategy."""

    def __init__(self, max_workers: Optional[int] = None, chunk_size: int = 1000) -> None:
        """Initialize handler."""
        self._process_pool = ProcessPoolExecutor(max_workers=max_workers)
        self._chunk_size = chunk_size

    async def execute(self, func: Callable[..., Any], data: list[Any]) -> list[Any]:
        """Execute using ProcessPoolExecutor without pickling."""
        if not data:
            return []

        # Split data into chunks
        chunks = list(chunk_data(data, self._chunk_size))

        # Create worker function that processes a chunk of data
        worker = partial(_map_worker, partial(_process_worker, func))

        # Process chunks in parallel and gather results
        results = await self._gather(worker, chunks)

        # Flatten results
        return [item for chunk in results for item in chunk]

    async def _gather(self, worker: Callable[..., Any], chunks: list[list[Any]]) -> Any:
        """Gather results from process pool."""
        loop = asyncio.get_event_loop()
        futures = [loop.run_in_executor(self._process_pool, worker, chunk) for chunk in chunks]
        return await asyncio.gather(*futures)

    def shutdown(self) -> None:
        """Shutdown the process pool."""
        self._process_pool.shutdown()
