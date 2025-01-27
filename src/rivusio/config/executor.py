"""Executor configuration."""
import multiprocessing
from dataclasses import dataclass
from typing import Optional

from rivusio.core.execution_strategy import ExecutionStrategy


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
