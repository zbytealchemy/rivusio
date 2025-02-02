import asyncio
from typing import Optional

import pytest

from rivusio import (
    AsyncBasePipe,
    AsyncPipeline,
    ExecutionStrategy,
    PipelineError,
)


class AsyncMultiplyByTwo(AsyncBasePipe[int, int]):
    """Async pipe that multiplies input by 2."""

    async def process(self, data: int) -> int:
        return data * 2


class AsyncAddOne(AsyncBasePipe[int, int]):
    """Async pipe that adds 1 to input."""

    async def process(self, data: int) -> int:
        return data + 1


class MockAsyncPipe(AsyncBasePipe[int, int]):
    async def process(self, data: int) -> int:
        return data * 2


class ErrorPipe(AsyncBasePipe[int, int]):
    """Pipe that raises an error."""

    async def process(self, data: int) -> int:
        raise ValueError("Test error")


class NullPipe(AsyncBasePipe[int, Optional[int]]):
    """Pipe that returns None."""

    async def process(self, data: int) -> Optional[int]:
        return None


class CPUIntensivePipe(AsyncBasePipe[int, int]):
    """Pipe that performs CPU-intensive operations."""

    async def process(self, data: int) -> int:
        # Simulate CPU-intensive work
        result = data
        for _ in range(1000):
            result = (result * 17 + 23) % 1000
        return result


class IOIntensivePipe(AsyncBasePipe[int, int]):
    """Pipe that performs I/O-intensive operations."""

    async def process(self, data: int) -> int:
        await asyncio.sleep(0.1)  # Simulate I/O operation
        return data * 2


@pytest.mark.asyncio()
async def test_async_pipeline_composition() -> None:
    """Test async pipeline composition with >> operator."""
    pipeline: AsyncPipeline[int, int] = (
        AsyncPipeline([AsyncMultiplyByTwo()]) >> AsyncAddOne()  # type: ignore
    )
    result = await pipeline.process(2)
    assert result == 5  # (2 * 2) + 1 = 5


@pytest.mark.asyncio()
async def test_async_pipeline_multiple_composition() -> None:
    """Test async pipeline composition with multiple pipes."""
    pipeline: AsyncPipeline[int, int] = (
        AsyncPipeline([AsyncMultiplyByTwo()]) >> AsyncAddOne() >> AsyncMultiplyByTwo()  # type: ignore
    )
    result = await pipeline.process(2)
    assert result == 10  # ((2 * 2) + 1) * 2 = 10


@pytest.mark.asyncio()
async def test_async_pipeline_empty() -> None:
    """Test behavior with empty pipeline."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([MockAsyncPipe()])
    result = await pipeline.process(1)
    assert result == 2


@pytest.mark.asyncio()
async def test_pipeline_error_propagation() -> None:
    """Test error handling in pipeline processing."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([ErrorPipe()])
    with pytest.raises(PipelineError):
        await pipeline.process(1)


@pytest.mark.asyncio()
async def test_pipeline_get_outputs() -> None:
    """Test getting intermediate outputs from pipeline."""
    pipe1 = MockAsyncPipe()
    pipe2 = MockAsyncPipe()
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([pipe1, pipe2])
    await pipeline.process(2)
    outputs1 = pipeline.get_pipe_outputs(pipe1)
    outputs2 = pipeline.get_pipe_outputs(pipe2)

    assert outputs1 == [4]
    assert outputs2 == [8]


@pytest.mark.asyncio()
async def test_pipeline_none_handling() -> None:
    """Test handling of None values in pipeline."""
    pipeline: AsyncPipeline[int, Optional[int]] = AsyncPipeline([NullPipe()])
    result = await pipeline.process(1)
    assert result is None


@pytest.mark.asyncio()
async def test_pipeline_empty_outputs() -> None:
    """Test getting outputs from non-existent pipe."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([MockAsyncPipe()])
    pipe = MockAsyncPipe()

    outputs = pipeline.get_pipe_outputs(pipe)
    assert outputs == []


@pytest.mark.asyncio()
async def test_pipeline_error_handling() -> None:
    """Test error handling in pipeline."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([ErrorPipe()])
    with pytest.raises(PipelineError):
        await pipeline.process(1)


@pytest.mark.asyncio()
async def test_pipeline_pipe_cleanup() -> None:
    """Test pipeline pipe cleanup."""

    class CleanupPipe(AsyncBasePipe[int, int]):
        cleaned: bool

        def __init__(self) -> None:
            super().__init__()
            self.cleaned = False

        async def process(self, data: int) -> int:
            return data * 2

        async def cleanup(self) -> None:
            self.cleaned = True

    pipeline: AsyncPipeline[int, int] = AsyncPipeline([CleanupPipe()])
    pipe = pipeline._pipes[0]
    await pipeline.process(2)
    await pipe.cleanup()  # type: ignore
    assert pipe.cleaned  # type: ignore


@pytest.mark.asyncio()
async def test_pipeline_multiple_pipe_cleanups() -> None:
    """Test multiple pipe cleanups."""

    class CleanupPipe(AsyncBasePipe[int, int]):
        cleanup_count: int

        def __init__(self) -> None:
            super().__init__()
            self.cleanup_count = 0

        async def process(self, data: int) -> int:
            return data

        async def cleanup(self) -> None:
            self.cleanup_count += 1

    pipeline: AsyncPipeline[int, int] = AsyncPipeline([CleanupPipe()])
    pipe = pipeline._pipes[0]
    await pipe.cleanup()  # type: ignore
    await pipe.cleanup()  # type: ignore
    assert pipe.cleanup_count == 2  # type: ignore


@pytest.mark.asyncio()
async def test_mixed_pipeline_error_handling() -> None:
    class AsyncErrorPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            raise ValueError("Async error")

    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncErrorPipe()])

    with pytest.raises(PipelineError) as exc_info:
        await pipeline.process(1)
    assert isinstance(exc_info.value.__cause__, ValueError)


@pytest.mark.asyncio()
async def test_pipeline_parallel_execution() -> None:
    """Test parallel execution of pipeline."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo(), AsyncAddOne()])
    pipeline.configure_parallel(ExecutionStrategy.GATHER)
    async with pipeline:
        results = await pipeline.execute_parallel([1, 2, 3])
        assert results == [3, 5, 7]  # (1*2)+1, (2*2)+1, (3*2)+1


@pytest.mark.asyncio()
async def test_pipeline_parallel_execution_empty_input() -> None:
    """Test parallel execution with empty input."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo()])
    pipeline.configure_parallel(ExecutionStrategy.GATHER)
    async with pipeline:
        results = await pipeline.execute_parallel([])
        assert results == []


@pytest.mark.asyncio()
async def test_pipeline_parallel_execution_error() -> None:
    """Test error handling in parallel execution."""

    class ErrorPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            if data == 2:
                raise ValueError("Error processing 2")
            return data * 2

    pipeline: AsyncPipeline[int, int] = AsyncPipeline([ErrorPipe()])
    pipeline.configure_parallel(ExecutionStrategy.GATHER)

    async with pipeline:
        with pytest.raises(PipelineError) as exc_info:
            await pipeline.execute_parallel([1, 2, 3])
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert str(exc_info.value.__cause__) == "Error processing 2"


@pytest.mark.asyncio()
async def test_pipeline_parallel_thread_pool_execution() -> None:
    """Test parallel execution using thread pool strategy."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo(), AsyncAddOne()])
    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL, max_workers=2)

    async with pipeline:
        results = await pipeline.execute_parallel([1, 2, 3])
        assert results == [3, 5, 7]  # (1*2)+1, (2*2)+1, (3*2)+1


@pytest.mark.asyncio()
async def test_pipeline_parallel_process_pool_execution() -> None:
    """Test parallel execution using process pool strategy."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo(), AsyncAddOne()])
    pipeline.configure_parallel(ExecutionStrategy.PROCESS_POOL, max_workers=2, chunk_size=2)

    async with pipeline:
        results = await pipeline.execute_parallel([1, 2, 3, 4])
        assert results == [3, 5, 7, 9]  # (1*2)+1, (2*2)+1, (3*2)+1, (4*2)+1


@pytest.mark.asyncio()
async def test_pipeline_parallel_strategy_reconfiguration() -> None:
    """Test reconfiguring parallel execution strategy."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo()])

    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL, max_workers=2)
    async with pipeline:
        results1 = await pipeline.execute_parallel([1, 2])
        assert results1 == [2, 4]

    pipeline.configure_parallel(ExecutionStrategy.PROCESS_POOL, max_workers=2)
    async with pipeline:
        results2 = await pipeline.execute_parallel([3, 4])
        assert results2 == [6, 8]


@pytest.mark.asyncio()
async def test_pipeline_parallel_cpu_intensive() -> None:
    """Test parallel execution with CPU-intensive operations."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([CPUIntensivePipe()])
    pipeline.configure_parallel(ExecutionStrategy.PROCESS_POOL, max_workers=2)

    async with pipeline:
        results = await pipeline.execute_parallel([1, 2, 3])
        assert len(results) == 3
        assert all(isinstance(x, int) for x in results)


@pytest.mark.asyncio()
async def test_pipeline_parallel_io_intensive() -> None:
    """Test parallel execution with I/O-intensive operations."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([IOIntensivePipe()])
    pipeline.configure_parallel(ExecutionStrategy.GATHER)

    async with pipeline:
        results = await pipeline.execute_parallel([1, 2, 3])
        assert results == [2, 4, 6]


@pytest.mark.asyncio()
async def test_pipeline_conditional_execution() -> None:
    """Test conditional execution of pipeline."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo()])

    result = await pipeline.execute_conditional(2, lambda x: x > 0)
    assert result == 4

    result = await pipeline.execute_conditional(2, lambda x: x < 0)
    assert result == 2


@pytest.mark.asyncio()
async def test_pipeline_parallel_chunk_size() -> None:
    """Test parallel execution with different chunk sizes."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo()])
    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL, chunk_size=2)

    async with pipeline:
        result = await pipeline.execute_parallel([1, 2, 3, 4])
        assert result == [2, 4, 6, 8]


@pytest.mark.asyncio()
async def test_pipeline_parallel_max_workers() -> None:
    """Test parallel execution with custom max_workers."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([CPUIntensivePipe()])
    pipeline.configure_parallel(ExecutionStrategy.PROCESS_POOL, max_workers=2)

    async with pipeline:
        result = await pipeline.execute_parallel([1, 2, 3, 4])
        assert len(result) == 4


@pytest.mark.asyncio()
async def test_pipeline_parallel_gather_strategy() -> None:
    """Test parallel execution with gather strategy."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([IOIntensivePipe()])
    pipeline.configure_parallel(ExecutionStrategy.GATHER)

    async with pipeline:
        result = await pipeline.execute_parallel([1, 2, 3])
        assert result == [2, 4, 6]


@pytest.mark.asyncio()
async def test_pipeline_state_serialization() -> None:
    """Test pipeline state serialization."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo()])
    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL)

    # Get state
    state = pipeline.__getstate__()
    assert "_parallel_executor" not in state
    assert "_parallel_config" in state

    # Set state
    new_pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo()])
    new_pipeline.__setstate__(state)
    assert new_pipeline._parallel_config == pipeline._parallel_config
    assert new_pipeline._parallel_executor is None


@pytest.mark.asyncio()
async def test_pipeline_parallel_execution_without_context() -> None:
    """Test parallel execution without context manager."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo()])
    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL)

    with pytest.raises(PipelineError) as exc_info:
        await pipeline.execute_parallel([1, 2, 3])
    assert "Must use async context manager for parallel execution" in str(exc_info.value)


@pytest.mark.asyncio()
async def test_pipeline_empty_initialization() -> None:
    """Test pipeline initialization with empty pipes list."""
    with pytest.raises(ValueError) as exc_info:
        AsyncPipeline([])
    assert "Pipeline must contain at least one pipe" in str(exc_info.value)


class CleanupTestPipe(AsyncBasePipe[int, int]):
    """Test pipe with cleanup tracking."""

    def __init__(self) -> None:
        super().__init__()
        self.cleaned_up = False

    async def process(self, data: int) -> int:
        return data * 2

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.cleaned_up = True


@pytest.mark.asyncio()
async def test_pipeline_cleanup_on_error() -> None:
    """Test pipeline cleanup when error occurs."""
    pipe = CleanupTestPipe()
    error_pipe = ErrorPipe()
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([pipe, error_pipe])

    try:
        async with pipeline:
            await pipeline.process(1)
    except PipelineError:
        pass
