"""Parallel execution strategies for pipelines."""
import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
from os import cpu_count
from typing import Any, Optional


def _worker(func: Callable[..., Any], item: Any) -> Any:
    """Run async functions in a thread with a new event loop.

    It is necessary because ThreadPoolExecutor does not support async functions.

    Args:
        func: The async function to run
        item: The item to pass to the function

    Returns:
        The result of the function
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(func(item))
    finally:
        loop.close()


def _process_worker(process_func: Callable[..., Any], item: Any) -> Any:
    """Process a single item in a worker process.

    Args:
        process_func: The async function to run
        item: The item to pass to the function

    Returns:
        The result of the function
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(process_func(item))
    finally:
        loop.close()


def _map_worker(worker: Callable[..., Any], chunk: list[Any]) -> list[Any]:
    """Map worker function over a chunk of data.

    Args:
        worker: The worker function to apply
        chunk: The chunk of data to process

    Returns:
        The results of applying the worker function to each item in the chunk
    """
    return [worker(item) for item in chunk]


def chunk_data(data: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split data into chunks of specified size.

    Args:
        data: The data to split
        chunk_size: The size of each chunk

    Returns:
        A list of chunks
    """
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


class ExecutionStrategyHandler(ABC):
    """Abstract base class for execution strategies."""

    @abstractmethod
    async def execute(self, func: Callable[..., Any], data: list[Any]) -> list[Any]:
        """Execute the function on the data using the specific strategy.

        Args:
            func: The function to execute
            data: The data to process

        Returns:
            The results of the function applied to the data
        """


class GatherStrategyHandler(ExecutionStrategyHandler):
    """Handler for asyncio.gather strategy."""

    async def execute(self, func: Callable[..., Any], data: list[Any]) -> list[Any]:
        """Execute using asyncio.gather.

        Args:
            func: The function to execute
            data: The data to process

        Returns:
            The results of the function applied to the data

        """
        if not data:
            return []
        return await asyncio.gather(*[func(item) for item in data])


class ThreadPoolStrategyHandler(ExecutionStrategyHandler):
    """Handler for ThreadPoolExecutor strategy."""

    def __init__(self, max_workers: Optional[int] = None) -> None:
        """Initialize handler.

        Args:
            max_workers: The maximum number of workers to use
        """
        self.max_workers = max_workers or cpu_count()
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)

    async def execute(self, func: Callable[..., Any], data: list[Any]) -> list[Any]:
        """Execute using ThreadPoolExecutor.

        Args:
            func: The function to execute
            data: The data to process

        Returns:
            The results of the function applied to the data
        """
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
        """Initialize handler.

        Args:
            max_workers: The maximum number of workers to use
            chunk_size: The size of each chunk to process
        """
        self._process_pool = ProcessPoolExecutor(max_workers=max_workers)
        self._chunk_size = chunk_size

    async def execute(self, func: Callable[..., Any], data: list[Any]) -> list[Any]:
        """Execute using ProcessPoolExecutor.

        Args:
            func: The function to execute
            data: The data to process

        Returns:
            The results of the function applied to the data
        """
        if not data:
            return []

        chunks = list(chunk_data(data, self._chunk_size))

        worker = partial(_map_worker, partial(_process_worker, func))

        results = await self._gather(worker, chunks)

        # Flatten results
        return [item for chunk in results for item in chunk]

    async def _gather(self, worker: Callable[..., Any], chunks: list[list[Any]]) -> Any:
        """Gather results from process pool.

        Args:
            worker: The worker function to apply
            chunks: The chunks of data to process

        Returns:
            The results of applying the worker function to each chunk
        """
        loop = asyncio.get_event_loop()
        futures = [loop.run_in_executor(self._process_pool, worker, chunk) for chunk in chunks]
        return await asyncio.gather(*futures)

    def shutdown(self) -> None:
        """Shutdown the process pool."""
        self._process_pool.shutdown()
