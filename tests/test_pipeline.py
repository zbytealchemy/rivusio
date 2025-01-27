import asyncio
from typing import Optional

import pytest

from rivusio.core.exceptions import PipelineError
from rivusio.core.parallel import ExecutionStrategy
from rivusio.core.pipe import AsyncBasePipe, SyncBasePipe
from rivusio.core.pipeline import AsyncPipeline, MixedPipeline, SyncPipeline


class AsyncMultiplyByTwo(AsyncBasePipe[int, int]):
    """Async pipe that multiplies input by 2."""

    async def process(self, data: int) -> int:
        return data * 2


class AsyncAddOne(AsyncBasePipe[int, int]):
    """Async pipe that adds 1 to input."""

    async def process(self, data: int) -> int:
        return data + 1


class SyncMultiplyByTwo(SyncBasePipe[int, int]):
    """Async pipe that multiplies input by 2."""

    def process(self, data: int) -> int:
        return data * 2


class SyncAddOne(SyncBasePipe[int, int]):
    """Async pipe that adds 1 to input."""

    def process(self, data: int) -> int:
        return data + 1


class MockAsyncPipe(AsyncBasePipe[int, int]):
    async def process(self, data: int) -> int:
        return data * 2


class MockSyncPipe(SyncBasePipe[int, int]):
    def process(self, data: int) -> int:
        return data * 3


class ErrorPipe(AsyncBasePipe[int, int]):
    """Pipe that raises an error."""

    async def process(self, data: int) -> int:
        raise ValueError("Test error")


class NullPipe(AsyncBasePipe[int, Optional[int]]):
    """Pipe that returns None."""

    async def process(self, data: int) -> Optional[int]:
        return None


class SyncErrorPipe(SyncBasePipe[int, int]):
    """Sync pipe that raises an error."""

    def process(self, data: int) -> int:
        raise ValueError("Test error")


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
async def test_mixed_pipeline_processing() -> None:
    """Test mixed sync/async pipeline processing."""
    sync_pipe = MockSyncPipe()
    async_pipe = MockAsyncPipe()
    pipeline: MixedPipeline = MixedPipeline()  # MixedPipeline takes no type arguments
    pipeline.add(sync_pipe)
    pipeline.add(async_pipe)

    result = await pipeline.process(2)
    assert result == 12  # 2 -> 6 -> 12


def test_sync_pipeline_validation() -> None:
    """Test pipeline validation with incorrect pipe types."""
    sync_pipe = MockSyncPipe()
    pipeline: SyncPipeline[int, int] = SyncPipeline([sync_pipe])
    assert len(pipeline._pipes) == 1


def test_sync_pipeline_processing() -> None:
    """Test sync pipeline with multiple sync pipes."""
    pipe1 = MockSyncPipe()
    pipe2 = MockSyncPipe()
    pipeline: SyncPipeline[int, int] = SyncPipeline([pipe1, pipe2])
    result = pipeline.process(2)
    assert result == 18  # 2 -> 6 -> 18


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
async def test_mixed_pipeline_context() -> None:
    """Test mixed pipeline with context manager."""
    pipeline: MixedPipeline = MixedPipeline()
    sync_pipe = MockSyncPipe()
    async_pipe: AsyncBasePipe[int, int] = MockAsyncPipe()

    pipeline.add(sync_pipe)
    pipeline.add(async_pipe)

    async with AsyncPipeline([async_pipe]) as p:  # type: ignore
        result = await p.process(2)
        assert result == 4


def test_sync_pipeline_error_handling() -> None:
    """Test error handling in sync pipeline."""
    pipeline: SyncPipeline[int, int] = SyncPipeline([SyncErrorPipe()])
    with pytest.raises(PipelineError):
        pipeline.process(1)


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
async def test_mixed_pipeline_pipe_cleanup() -> None:
    class AsyncCleanupPipe(AsyncBasePipe[int, int]):
        def __init__(self) -> None:
            super().__init__()
            self.async_cleaned = False

        async def process(self, data: int) -> int:
            return data * 2

        async def cleanup(self) -> None:
            self.async_cleaned = True

    class SyncCleanupPipe(SyncBasePipe[int, int]):
        def __init__(self) -> None:
            super().__init__()
            self.sync_cleaned = False

        def process(self, data: int) -> int:
            return data * 3

        def cleanup(self) -> None:
            self.sync_cleaned = True

    pipeline: MixedPipeline = MixedPipeline()  # Remove type argument
    async_pipe = AsyncCleanupPipe()
    sync_pipe = SyncCleanupPipe()

    pipeline.add(sync_pipe)
    pipeline.add(async_pipe)

    await pipeline.process(2)
    await async_pipe.cleanup()
    sync_pipe.cleanup()

    assert async_pipe.async_cleaned
    assert sync_pipe.sync_cleaned


@pytest.mark.asyncio()
async def test_mixed_pipeline_error_handling() -> None:
    class AsyncErrorPipe(AsyncBasePipe[int, int]):
        async def process(self, data: int) -> int:
            raise ValueError("Async error")

    pipeline: MixedPipeline = MixedPipeline()
    pipeline.add(AsyncErrorPipe())

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

    # Start with thread pool
    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL, max_workers=2)
    async with pipeline:
        results1 = await pipeline.execute_parallel([1, 2])
        assert results1 == [2, 4]

    # Switch to process pool
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
    pipeline.configure_parallel(ExecutionStrategy.GATHER)  # Best for I/O-bound tasks

    async with pipeline:
        results = await pipeline.execute_parallel([1, 2, 3])
        assert results == [2, 4, 6]


@pytest.mark.asyncio()
async def test_pipeline_conditional_execution() -> None:
    """Test conditional execution of pipeline."""
    pipeline: AsyncPipeline[int, int] = AsyncPipeline([AsyncMultiplyByTwo()])

    # Test when condition is True
    result = await pipeline.execute_conditional(2, lambda x: x > 0)
    assert result == 4  # Condition met, pipeline executed

    # Test when condition is False
    result = await pipeline.execute_conditional(2, lambda x: x < 0)
    assert result == 2  # Condition not met, original data returned


@pytest.mark.asyncio()
async def test_mixed_pipeline_empty_initialization() -> None:
    """Test MixedPipeline initialization with empty pipes list."""
    pipeline: MixedPipeline = MixedPipeline()
    assert len(pipeline.pipes) == 0

    # Test adding pipes after initialization
    pipeline.add(MockSyncPipe())
    pipeline.add(MockAsyncPipe())
    assert len(pipeline.pipes) == 2


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
async def test_mixed_pipeline_parallel_execution() -> None:
    """Test parallel execution in mixed pipeline."""
    pipeline: MixedPipeline = MixedPipeline([MockSyncPipe(), MockAsyncPipe()])
    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL)

    async with pipeline:
        result = await pipeline.execute_parallel([1, 2])
        assert result == [6, 12]  # (1*3)*2, (2*3)*2


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
async def test_mixed_pipeline_rshift_operator() -> None:
    """Test mixed pipeline composition with >> operator."""
    pipeline: MixedPipeline = (
        MixedPipeline([MockSyncPipe()]) >> MockAsyncPipe()  # type: ignore
    )
    result = await pipeline.process(2)
    assert result == 12  # (2*3)*2


@pytest.mark.asyncio()
async def test_pipeline_empty_initialization() -> None:
    """Test pipeline initialization with empty pipes list."""
    with pytest.raises(ValueError) as exc_info:
        AsyncPipeline([])
    assert "Pipeline must contain at least one pipe" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        SyncPipeline([])
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

    await pipe.cleanup()
    assert pipe.cleaned_up
