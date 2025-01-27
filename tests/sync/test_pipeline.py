
import pytest

from rivusio import ExecutionStrategy, SyncBasePipe, SyncPipeline
from rivusio.core.exceptions import PipelineError


class MockSyncPipe(SyncBasePipe[int, int]):
    """Mock sync pipe that multiplies input by 3."""

    def process(self, data: int) -> int:
        return data * 3

class SyncMultiplyByTwo(SyncBasePipe[int, int]):
    """Sync pipe that multiplies input by 2."""

    def process(self, data: int) -> int:
        return data * 2

class SyncErrorPipe(SyncBasePipe[int, int]):
    """Sync pipe that raises an error."""

    def process(self, data: int) -> int:
        raise ValueError("Test error")

class AddPipe(SyncBasePipe[int, int]):
    """Sync pipe that adds 1 to input."""

    def process(self, data: int) -> int:
        return data + 1

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


def test_sync_pipeline_context() -> None:
    """Test sync pipeline with context manager."""
    pipeline: SyncPipeline[int, int] = SyncPipeline([SyncMultiplyByTwo()])

    with pipeline as p:
        result = p.process(2)
        assert result == 4


def test_sync_pipeline_error_handling() -> None:
    """Test error handling in sync pipeline."""
    pipeline: SyncPipeline[int, int] = SyncPipeline([SyncErrorPipe()])
    with pytest.raises(PipelineError):
        pipeline.process(1)


def test_pipeline_empty_initialization() -> None:
    """Test pipeline initialization with empty pipes list."""
    with pytest.raises(ValueError) as exc_info:
        SyncPipeline([])
    assert "Pipeline must contain at least one pipe" in str(exc_info.value)


def test_pipeline_parallel_execution_new() -> None:
    """Test parallel execution with proper initialization."""
    pipeline: SyncPipeline[int, int] = SyncPipeline([AddPipe()])
    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL)

    with pipeline:
        result = pipeline.execute_parallel([1, 2, 3])

    assert result == [2, 3, 4]


def test_pipeline_parallel_execution_without_context_new() -> None:
    """Test parallel execution without context manager."""
    pipeline: SyncPipeline[int, int] = SyncPipeline([AddPipe()])
    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL)

    with pytest.raises(PipelineError) as exc_info:
        pipeline.execute_parallel([1, 2, 3])
    assert "Must use context manager for parallel execution" in str(exc_info.value)


def test_pipeline_conditional_execution() -> None:
    """Test conditional execution."""
    pipeline: SyncPipeline[int, int] = SyncPipeline([AddPipe()])

    result = pipeline.execute_conditional(1, lambda x: x > 0)
    assert result == 2

    result = pipeline.execute_conditional(1, lambda x: x < 0)
    assert result == 1


def test_pipeline_composition_operators() -> None:
    """Test pipeline composition using >> operator."""
    pipe1 = AddPipe()
    pipe2 = AddPipe()
    pipeline1: SyncPipeline[int, int] = SyncPipeline([pipe1])

    pipeline2 = pipe2 >> pipeline1
    assert len(pipeline2.pipes) == 2

    pipeline3 = pipeline1 >> pipe2
    assert len(pipeline3.pipes) == 2


def test_pipeline_custom_name() -> None:
    """Test pipeline with custom name."""
    pipeline: SyncPipeline[int, int] = SyncPipeline([AddPipe()], name="CustomPipeline")
    assert pipeline.name == "CustomPipeline"

def test_pipeline_get_pipes() -> None:
    """Test getting pipeline's pipes."""
    pipe1 = AddPipe()
    pipe2 = SyncMultiplyByTwo()
    pipeline: SyncPipeline[int, int] = SyncPipeline([pipe1, pipe2])

    assert pipeline.pipes == [pipe1, pipe2]

def test_pipeline_state_copy() -> None:
    """Test pipeline state copying."""
    pipeline: SyncPipeline[int, int] = SyncPipeline([AddPipe()])
    state = pipeline.__getstate__()

    new_pipeline: SyncPipeline[int, int] = SyncPipeline([AddPipe()])
    new_pipeline.__setstate__(state)

    assert new_pipeline.name == pipeline.name
