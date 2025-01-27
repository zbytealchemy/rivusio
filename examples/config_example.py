"""Example of using configuration with pipes."""

from rivusio import AsyncBasePipe, PipeConfig


class FilterConfig(PipeConfig):
    """Configuration for filtering values."""

    min_value: float
    name: str = "filter"


class FilterPipe(AsyncBasePipe[dict, dict]):
    """Filter dictionary values based on minimum threshold."""

    def __init__(self, config: FilterConfig) -> None:
        """Initialize FilterPipe with config.

        Args:
            config: Configuration for filtering values

        """
        super().__init__()
        self.config = config
        self.name = config.name

    async def process(self, data: dict) -> dict:
        """Filter dictionary items where value is below threshold.

        Args:
            data: Dictionary of values to filter

        Returns:
            Dictionary with values >= min_value

        """
        return {k: v for k, v in data.items() if v >= self.config.min_value}
