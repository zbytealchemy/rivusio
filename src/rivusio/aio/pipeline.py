"""Async pipeline implementations for composing pipes."""
import types
from abc import abstractmethod
from collections.abc import Callable
from typing import Any, Optional, Union, cast

from rivusio.aio.parallel import (
    ExecutionStrategyHandler,
    GatherStrategyHandler,
    ProcessPoolStrategyHandler,
    ThreadPoolStrategyHandler,
)
from rivusio.config import ParallelConfig
from rivusio.core.base import BasePipe
from rivusio.core.exceptions import PipelineError
from rivusio.core.execution_strategy import ExecutionStrategy
from rivusio.core.metrics import PipelineMetricsMixin
from rivusio.core.types import InputType, OutputType


class AsyncBasePipe(BasePipe[InputType, OutputType]):
    """Base class for async pipes."""

    @abstractmethod
    async def process(self, data: InputType) -> OutputType:
        """Process the data.

        Args:
            data: Data to process

        Returns:
            Processed data
        """

    async def __call__(self, data: InputType) -> OutputType:
        """Process data when pipe is called as a function.

        Args:
            data: Input data

        Returns:
            Processed data
        """
        return await self.process(data)

    def __rshift__(
        self,
        other: "AsyncBasePipe[OutputType, OutputType]",
    ) -> "AsyncPipeline[InputType, OutputType]":
        """Compose this pipe with another pipe using the >> operator."""
        return AsyncPipeline([self, other])


class AsyncPipeline(AsyncBasePipe[InputType, OutputType], PipelineMetricsMixin):
    """Pipeline for composing async pipes."""

    def __init__(self, pipes: list[AsyncBasePipe[Any, Any]], name: Optional[str] = None) -> None:
        """Initialize pipeline."""
        super().__init__()
        if not pipes:
            raise ValueError("Pipeline must contain at least one pipe")
        self._pipes = pipes
        self.name = name or "AsyncPipeline"
        self._pipe_outputs: dict[AsyncBasePipe, list[Any]] = {pipe: [] for pipe in self._pipes}
        self._parallel_config: Optional[ParallelConfig] = None
        self._parallel_executor: Optional[AsyncParallelExecutor] = None

    async def __aenter__(self) -> "AsyncPipeline[InputType, OutputType]":
        """Initialize resources."""
        if self._parallel_config:
            self._parallel_executor = AsyncParallelExecutor(self._parallel_config)
            await self._parallel_executor.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Clean up resources."""
        if self._parallel_executor:
            await self._parallel_executor.__aexit__(exc_type, exc_val, exc_tb)

    def __rshift__(
        self,
        other: AsyncBasePipe[OutputType, OutputType],
    ) -> "AsyncPipeline[InputType, OutputType]":
        """Compose this pipeline with another pipe."""
        return AsyncPipeline([*self._pipes, other])

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
    def pipes(self) -> list[AsyncBasePipe[Any, Any]]:
        """Get pipeline's pipes."""
        return self._pipes

    async def process(self, data: InputType) -> OutputType:
        """Process data through all pipes in the pipeline."""
        result = data
        for pipe in self._pipes:
            try:
                result = await pipe.process(result)
                self._pipe_outputs[pipe].append(result)
            except Exception as e:
                raise PipelineError(pipe.__class__.__name__, e) from e
        return cast(OutputType, result)

    async def execute_parallel(self, data: list[Any]) -> list[Any]:
        """Execute the pipeline on multiple inputs in parallel."""
        if not self._parallel_executor:
            raise PipelineError(
                self.name, RuntimeError("Must use async context manager for parallel execution"),
            )
        return await self._parallel_executor.execute(self, data)

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

    async def execute_conditional(
        self, data: InputType, condition: Callable[[InputType], bool],
    ) -> Union[InputType, OutputType]:
        """Execute pipeline only if condition is met."""
        if condition(data):
            return await self.process(data)
        return data


class AsyncParallelExecutor:
    """Executor for parallel processing."""

    def __init__(self, config: ParallelConfig) -> None:
        """Initialize executor."""
        self.config = config
        self._strategy_handler: Optional[ExecutionStrategyHandler] = None

    async def __aenter__(self) -> "AsyncParallelExecutor":
        """Initialize resources."""
        if self.config.strategy == ExecutionStrategy.GATHER:
            self._strategy_handler = GatherStrategyHandler()
        elif self.config.strategy == ExecutionStrategy.THREAD_POOL:
            self._strategy_handler = ThreadPoolStrategyHandler(max_workers=self.config.max_workers)
        elif self.config.strategy == ExecutionStrategy.PROCESS_POOL:
            self._strategy_handler = ProcessPoolStrategyHandler(
                max_workers=self.config.max_workers,
                chunk_size=self.config.chunk_size,
            )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Clean up resources."""
        if isinstance(
            self._strategy_handler,
            ThreadPoolStrategyHandler | ProcessPoolStrategyHandler,
        ):
            self._strategy_handler.shutdown()

    async def execute(
        self,
        pipeline: AsyncPipeline[Any, Any],
        data: list[Any],
    ) -> list[Any]:
        """Execute pipeline in parallel."""
        if self._strategy_handler is None:
            raise ValueError("Strategy handler not initialized.")
        return await self._strategy_handler.execute(pipeline.process, data)
