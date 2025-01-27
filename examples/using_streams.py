"""Example of using streams with Rivusio."""
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Optional, Union

from rivusio import AsyncBasePipe, AsyncPipeline, AsyncStream, StreamConfig


class TransformPipe(AsyncBasePipe[Union[dict, list[dict]], Union[dict, list[dict]]]):
    """Transform pipe that adds a processed timestamp to records."""

    async def process(self, data: Union[dict, list[dict]]) -> Union[dict, list[dict]]:
        """Transform string values to uppercase.

        Args:
        ----
            data: Dictionary or list of dictionaries with string values to transform

        Returns:
        -------
            Dictionary or list of dictionaries with uppercase string values

        """
        if isinstance(data, list):
            return [await self._transform_dict(item) for item in data]
        return await self._transform_dict(data)

    async def _transform_dict(self, data: dict) -> dict:
        """Transform a single dictionary's string values to uppercase."""
        result = data.copy()
        for key, value in result.items():
            if isinstance(value, str):
                result[key] = value.upper()
        return result


class FilterPipe(AsyncBasePipe[Union[dict, list[dict]], Optional[Union[dict, list[dict]]]]):
    """Filter pipe that only allows records with specific fields."""

    async def process(self, data: Union[dict, list[dict]]) -> Optional[Union[dict, list[dict]]]:
        """Filter records that don't have required fields.

        Args:
        ----
            data: Dictionary or list of dictionaries to check for required fields

        Returns:
        -------
            Dictionary/list if it has required fields, None otherwise

        """
        if isinstance(data, list):
            filtered = [d for d in data if self._has_required_fields(d)]
            return filtered if filtered else None
        return data if self._has_required_fields(data) else None

    def _has_required_fields(self, data: dict) -> bool:
        """Check if a dictionary has the required fields."""
        return "name" in data and "status" in data


async def data_source() -> AsyncIterator[dict[str, str]]:
    """Sample data generator.

    Returns
    -------
        AsyncStream yielding sample records

    """
    sample_data = [
        {"name": "alice", "status": "active", "role": "user"},
        {"name": "bob", "status": "inactive"},
        {"role": "admin"},  # Will be filtered out
        {"name": "charlie", "status": "active", "role": "admin"},
    ]
    for item in sample_data:
        yield item


async def example() -> None:
    """Run the stream processing example."""
    # Create pipeline
    pipeline: AsyncPipeline[dict[str, str], Optional[dict[str, str]]] = \
          AsyncPipeline([TransformPipe(), FilterPipe()])

    # Configure stream processing
    config = StreamConfig(
        batch_size=2,  # Process two records at a time
        window_size=timedelta(seconds=30),
        retry_attempts=3,
    )

    # Create and process stream
    stream = AsyncStream(data_source(), config)
    async for result in stream.process(pipeline):
        if result:
            print(f"Processed record: {result}")
        else:
            print("Record filtered out")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example())
