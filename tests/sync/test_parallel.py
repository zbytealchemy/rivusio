import pytest

from rivusio.sync.parallel import (
    ProcessPoolStrategyHandler,
    ThreadPoolStrategyHandler,
)


def test_thread_pool_handler() -> None:
    """Test ThreadPoolStrategyHandler execution."""
    handler: ThreadPoolStrategyHandler[int, int] = ThreadPoolStrategyHandler(max_workers=2)

    def process_func(x: int) -> int:
        return x * 2

    with handler:
        results = handler.execute(process_func, [1, 2, 3])

    assert results == [2, 4, 6]

def multiply_by_two(x: int) -> int:
    """Multiply input by 2."""
    return x * 2

def test_process_pool_handler() -> None:
    """Test ProcessPoolStrategyHandler execution."""
    handler: ProcessPoolStrategyHandler[int, int] = ProcessPoolStrategyHandler(max_workers=2)

    with handler:
        results = handler.execute(multiply_by_two, [1, 2, 3])

    assert results == [2, 4, 6]

def test_handler_context_reuse() -> None:
    """Test reusing handler context."""
    handler: ThreadPoolStrategyHandler[int, int] = ThreadPoolStrategyHandler(max_workers=2)

    with handler:
        results = handler.execute(lambda x: x * 2, [1, 2])

    assert results == [2, 4]

def test_handler_cleanup() -> None:
    """Test handler cleanup."""
    handler: ThreadPoolStrategyHandler[int, int] = ThreadPoolStrategyHandler(max_workers=2)

    with handler:
        results = handler.execute(lambda x: x * 2, [1])
        assert results == [2]

    with pytest.raises(RuntimeError, match="cannot schedule new futures after shutdown"):
        handler.execute(lambda x: x * 2, [1])
