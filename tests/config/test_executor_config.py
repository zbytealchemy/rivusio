"""Tests for executor configuration."""
import multiprocessing

from rivusio import ExecutionStrategy, ParallelConfig


def test_parallel_config_defaults() -> None:
    """Test ParallelConfig default values."""
    config = ParallelConfig()
    assert config.strategy == ExecutionStrategy.GATHER
    assert config.chunk_size == 1000
    assert config.max_workers is None


def test_parallel_config_process_pool() -> None:
    """Test ParallelConfig with process pool strategy."""
    config = ParallelConfig(strategy=ExecutionStrategy.PROCESS_POOL)
    expected_workers = max(1, multiprocessing.cpu_count() - 1)
    assert config.max_workers == expected_workers


def test_parallel_config_thread_pool() -> None:
    """Test ParallelConfig with thread pool strategy."""
    config = ParallelConfig(strategy=ExecutionStrategy.THREAD_POOL)
    expected_workers = min(32, (multiprocessing.cpu_count() or 1) * 4)
    assert config.max_workers == expected_workers


def test_parallel_config_custom_workers() -> None:
    """Test ParallelConfig with custom max_workers."""
    config = ParallelConfig(max_workers=5)
    assert config.max_workers == 5
    assert config.strategy == ExecutionStrategy.GATHER


def test_parallel_config_custom_chunk_size() -> None:
    """Test ParallelConfig with custom chunk size."""
    config = ParallelConfig(chunk_size=500)
    assert config.chunk_size == 500
