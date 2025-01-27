"""Example of using Rivusio for asynchronous pipeline processing."""

import asyncio
import time
from dataclasses import dataclass

from rivusio import AsyncBasePipe, ExecutionStrategy


@dataclass
class UserData:
    """Data class representing user information."""

    id: int
    name: str
    score: float


class AsyncScoreFilterPipe(AsyncBasePipe[UserData, UserData]):
    """Asynchronous pipe that filters users based on score."""

    def __init__(self, min_score: float) -> None:
        """Initialize the pipe with a minimum score threshold."""
        super().__init__()
        self.min_score = min_score

    async def process(self, data: UserData) -> UserData:
        """Filter users with score below minimum."""
        if data.score < self.min_score:
            raise ValueError(f"Score {data.score} below minimum {self.min_score}")
        return data


class UserEnrichmentPipe(AsyncBasePipe[UserData, dict]):
    """Asynchronous pipe that enriches user data."""

    async def process(self, data: UserData) -> dict:
        """Enrich user data with rank and processed timestamp."""
        min_score: int = 90

        await asyncio.sleep(0.1)
        return {
            "id": data.id,
            "name": data.name,
            "score": data.score,
            "rank": "premium" if data.score > min_score else "standard",
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }


class AsyncStatsPipe(AsyncBasePipe[dict, dict]):
    """Asynchronous pipe that adds statistical information."""

    async def process(self, data: dict) -> dict:
        """Add statistical information to the data."""
        data["stats"] = {
            "score_normalized": data["score"] / 100,
            "score_squared": data["score"] ** 2,
        }
        return data


async def main() -> None:
    """Run the async pipeline example."""
    users = [
        UserData(id=1, name="Alice", score=95),
        UserData(id=2, name="Bob", score=85),
    ]

    # Create async pipeline
    pipeline = (
            AsyncScoreFilterPipe(min_score=60)
            >> UserEnrichmentPipe()
            >> AsyncStatsPipe()
    )

    # Configure parallel execution
    pipeline.configure_parallel(
        strategy=ExecutionStrategy.THREAD_POOL,
        max_workers=3,
    )

    # Process batch using context manager
    async with pipeline:
        results = await pipeline.execute_parallel(users)
        for result in results:
            print(f"\nProcessed {result['name']}:")
            print(f"Rank: {result['rank']}")
            print(f"Stats: {result['stats']}")


if __name__ == "__main__":
    asyncio.run(main())
