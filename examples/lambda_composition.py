"""Example of composing pipes using lambda functions and function composition."""
import asyncio
from collections.abc import Callable
from typing import TypeVar

from rivusio import AsyncBasePipe, AsyncPipeline

T = TypeVar("T")
U = TypeVar("U")


class LambdaPipe(AsyncBasePipe[T, U]):
    """Create a pipe from a lambda or function."""

    def __init__(self, func: Callable[[T], U]) -> None:
        """Initialize the pipe with a function.

        Args:
        ----
            func: Function to execute in the pipe

        """
        super().__init__()
        self.func = func
        self.name = func.__name__ if hasattr(func, "__name__") else "lambda"

    async def process(self, data: T) -> U:
        """Execute the function on the input data.

        Args:
        ----
            data: Input data to process

        Returns:
        -------
            Result of applying the function to the input data

        """
        return self.func(data)


async def main() -> None:
    """Run the example."""
    # Create pipes using lambda functions
    double: LambdaPipe[int, int] = LambdaPipe(lambda x: x * 2)
    add_ten: LambdaPipe[int, int] = LambdaPipe(lambda x: x + 10)
    to_string: LambdaPipe[int, str] = LambdaPipe(lambda x: f"Result: {x}")

    # Create a pipeline
    pipeline: AsyncPipeline[int, str] = AsyncPipeline([double, add_ten, to_string])

    result = await pipeline.process(5)
    print(f"Pipeline: {' -> '.join(p.name for p in pipeline.pipes)}")
    print("Input: 5")
    print(f"Output: {result}")

    numbers = [1, 2, 3, 4, 5]
    list_pipeline: AsyncPipeline[list[int], int] = AsyncPipeline(
        [
            LambdaPipe(lambda nums: [x for x in nums if x % 2 == 0]),
            LambdaPipe(lambda nums: [x * x for x in nums]),
            LambdaPipe(lambda nums: sum(nums)),
        ],
    )

    result = await list_pipeline.process(numbers)
    print(f"\nList Pipeline: {' -> '.join(p.name for p in list_pipeline.pipes)}")
    print(f"Input: {numbers}")
    print(f"Output: {result}")

    data = {"name": "alice", "age": 30, "city": "new york"}
    dict_pipeline = AsyncPipeline(
        [
            LambdaPipe(lambda d: {k: v.upper() if isinstance(v, str) else v for k, v in d.items()}),
            LambdaPipe(
                lambda d: {k: f"{v}!" if isinstance(v, str) else v + 1 for k, v in d.items()},
            ),
        ],
    )

    result = await dict_pipeline.process(data)
    print(f"\nDict Pipeline: {' -> '.join(p.name for p in dict_pipeline.pipes)}")
    print(f"Input: {data}")
    print(f"Output: {result}")


if __name__ == "__main__":
    asyncio.run(main())
