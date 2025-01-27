"""Example of basic data transformation using Rivusio."""
import asyncio

from pydantic import ConfigDict

from rivusio import AsyncBasePipe, PipeConfig


class FilterConfig(PipeConfig):
    """Configuration for filtering records."""

    field: str
    value: str


class FilterPipe(AsyncBasePipe[list[dict], list[dict]]):
    """Filter records based on a field value."""

    def __init__(self, config: FilterConfig) -> None:
        """Initialize FilterPipe with config."""
        super().__init__()
        self.config = config
        self.name = config.name or self.__class__.__name__

    async def process(self, data: list[dict]) -> list[dict]:
        """Filter records where field matches value."""
        return [record for record in data if record.get(self.config.field) == self.config.value]


class TransformConfig(PipeConfig):
    """Configuration for data transformation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    columns: list[str]
    operation: str


class TransformPipe(AsyncBasePipe[list[dict], list[dict]]):
    """Transform records by converting specified fields to uppercase."""

    def __init__(self, config: TransformConfig) -> None:
        """Initialize TransformPipe with config."""
        super().__init__()
        self.config = config
        self.name = config.name or self.__class__.__name__

    async def process(self, data: list[dict]) -> list[dict]:
        """Convert specified fields to uppercase."""
        result = []
        for record in data:
            transformed = record.copy()
            for field in self.config.columns:
                if field in transformed:
                    transformed[field] = str(transformed[field]).upper()
            result.append(transformed)
        return result


async def main() -> None:
    """Run the example."""
    # Sample data
    data = [
        {"name": "Alice", "status": "active", "role": "admin"},
        {"name": "Bob", "status": "inactive", "role": "user"},
        {"name": "Charlie", "status": "active", "role": "user"},
    ]

    # Create pipeline
    filter_pipe = FilterPipe(FilterConfig(field="status", value="active"))
    transform_pipe = TransformPipe(TransformConfig(columns=["role"], operation="uppercase"))

    # Process data through pipes
    filtered_data = await filter_pipe.process(data)
    final_data = await transform_pipe.process(filtered_data)

    print("Original data:")
    print(data)
    print("\nFiltered and transformed data:")
    print(final_data)


if __name__ == "__main__":
    asyncio.run(main())
