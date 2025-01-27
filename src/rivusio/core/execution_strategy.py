"""Execution strategy definitions."""
from enum import Enum


class ExecutionStrategy(str, Enum):
    """Execution strategy for parallel processing.

    Attributes
        GATHER: Uses asyncio.gather for I/O-bound tasks
        THREAD_POOL: Uses ThreadPoolExecutor for I/O and light CPU tasks
        PROCESS_POOL: Uses ProcessPoolExecutor for CPU-intensive tasks

    """

    GATHER = "gather"

    THREAD_POOL = "thread_pool"

    PROCESS_POOL = "process_pool"




