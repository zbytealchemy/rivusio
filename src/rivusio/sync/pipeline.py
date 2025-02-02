"""Sync pipeline implementations for composing pipes."""

import types
from abc import abstractmethod
from collections.abc import Callable
from typing import Any, Optional, Union, cast

from rivusio.config import ParallelConfig
from rivusio.core.base import BasePipe
from rivusio.core.exceptions import PipelineError
from rivusio.core.execution_strategy import ExecutionStrategy
from rivusio.core.metrics import PipelineMetricsMixin
from rivusio.core.types import InputType, OutputType
from rivusio.sync.parallel import (
    ExecutionStrategyHandler,
    ProcessPoolStrategyHandler,
    ThreadPoolStrategyHandler,
)


class SyncBasePipe(BasePipe[InputType, OutputType]):
    """Base class for sync pipes."""

    @abstractmethod
    def process(self, data: InputType) -> OutputType:
        """Process the data."""

    def __call__(self, data: InputType) -> OutputType:
        """Process data when pipe is called as a function."""
        return self.process(data)

    def __rshift__(
        self,
        other: "SyncBasePipe[OutputType, OutputType]",
    ) -> "SyncPipeline[InputType, OutputType]":
        """Compose this pipe with another pipe using the >> operator."""
        return SyncPipeline([self, other])


class SyncPipeline(SyncBasePipe[InputType, OutputType], PipelineMetricsMixin):
    """Pipeline for composing sync pipes."""

    def __init__(self, pipes: list[SyncBasePipe[Any, Any]], name: Optional[str] = None) -> None:
        """Initialize pipeline."""
        super().__init__()
        if not pipes:
            raise ValueError("Pipeline must contain at least one pipe")
        self._pipes = pipes
        self.name = name or "SyncPipeline"
        self._pipe_outputs: dict[SyncBasePipe, list[Any]] = {pipe: [] for pipe in self._pipes}
        self._parallel_config: Optional[ParallelConfig] = None
        self._parallel_executor: Optional[SyncParallelExecutor] = None

    def __enter__(self) -> "SyncPipeline[InputType, OutputType]":
        """Initialize resources."""
        if self._parallel_config:
            self._parallel_executor = SyncParallelExecutor(self._parallel_config)
            self._parallel_executor.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> None:
        """Clean up resources."""
        if self._parallel_executor:
            self._parallel_executor.__exit__(exc_type, exc_val, exc_tb)

    def __rshift__(
        self,
        other: SyncBasePipe[OutputType, OutputType],
    ) -> "SyncPipeline[InputType, OutputType]":
        """Compose this pipeline with another pipe."""
        return SyncPipeline([*self._pipes, other])

    def __getstate__(self) -> dict[str, Any]:
        """Get pipeline state."""
        state = self.__dict__.copy()
        state.pop("_parallel_executor", None)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore pipeline state."""
        self.__dict__.update(state)
        self._parallel_executor = None

    @property
    def pipes(self) -> list[SyncBasePipe[Any, Any]]:
        """Get pipeline's pipes."""
        return self._pipes

    def process(self, data: InputType) -> OutputType:
        """Process data through all pipes in the pipeline."""
        result = data
        for pipe in self._pipes:
            try:
                result = pipe.process(result)
                self._pipe_outputs[pipe].append(result)
            except Exception as e:
                raise PipelineError(pipe.__class__.__name__, e) from e
        return cast(OutputType, result)

    def execute_parallel(self, data: list[Any]) -> list[Any]:
        """Execute the pipeline on multiple inputs in parallel."""
        if not self._parallel_executor:
            raise PipelineError(
                self.name, RuntimeError("Must use context manager for parallel execution"),
            )
        return self._parallel_executor.execute(self, data)

    def configure_parallel(
        self,
        strategy: Union[ExecutionStrategy, str],
        max_workers: Optional[int] = None,
        chunk_size: int = 1000,
    ) -> None:
        """Configure parallel execution."""
        if isinstance(strategy, str):
            strategy = ExecutionStrategy(strategy)
        self._parallel_config = ParallelConfig(
            strategy=strategy, max_workers=max_workers, chunk_size=chunk_size,
        )

    def execute_conditional(
        self, data: InputType, condition: Callable[[InputType], bool],
    ) -> Union[InputType, OutputType]:
        """Execute pipeline only if condition is met."""
        if condition(data):
            return self.process(data)
        return data


class SyncParallelExecutor:
    """Executor for parallel processing."""

    def __init__(self, config: ParallelConfig) -> None:
        """Initialize executor."""
        self.config = config
        self._strategy_handler: Optional[ExecutionStrategyHandler] = None

    def __enter__(self) -> "SyncParallelExecutor":
        """Initialize resources."""
        if self.config.strategy == ExecutionStrategy.THREAD_POOL:
            self._strategy_handler = ThreadPoolStrategyHandler(max_workers=self.config.max_workers)
        elif self.config.strategy == ExecutionStrategy.PROCESS_POOL:
            self._strategy_handler = ProcessPoolStrategyHandler(
                max_workers=self.config.max_workers,
                chunk_size=self.config.chunk_size,
            )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Clean up resources."""
        if isinstance(
            self._strategy_handler,
            ThreadPoolStrategyHandler | ProcessPoolStrategyHandler,
        ):
            self._strategy_handler.__exit__(exc_type, exc_val, exc_tb)

    def execute(
        self,
        pipeline: SyncPipeline[Any, Any],
        data: list[Any],
    ) -> list[Any]:
        """Execute pipeline in parallel."""
        if self._strategy_handler is None:
            raise ValueError("Strategy handler not initialized.")
        return self._strategy_handler.execute(pipeline.process, data)
