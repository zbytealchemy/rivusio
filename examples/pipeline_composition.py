"""Example of composing pipes into a pipeline using rivusio."""
import asyncio

from pydantic import BaseModel, Field

from rivusio import AsyncBasePipe, AsyncPipeline, PipeConfig


class Order(BaseModel):
    """Sample order data class."""

    id: str
    customer: str
    amount: float
    status: str


class ValidationPipe(AsyncBasePipe[Order, Order]):
    """Validate order data."""

    async def process(self, data: Order) -> Order:
        """Validate order amount and status.

        Args:
        ----
            data: Order to validate

        Returns:
        -------
            Order if valid, raises ValueError if invalid

        """
        if data.amount <= 0:
            raise ValueError(f"Invalid order {data.id}: amount must be positive")
        if data.status not in ["pending", "completed"]:
            raise ValueError(f"Invalid order {data.id}: status must be 'pending' or 'completed'")
        return data


class EnrichConfig(PipeConfig):
    """Configuration for order enrichment."""

    premium_threshold: float = Field(gt=0)


class EnrichmentPipe(AsyncBasePipe[Order, Order]):
    """Enrich order with customer tier."""

    def __init__(self, config: EnrichConfig) -> None:
        """Initialize EnrichmentPipe with config."""
        super().__init__()
        self.config = config

    async def process(self, data: Order) -> Order:
        """Add premium flag based on order amount.

        Args:
        ----
            data: Order to enrich

        Returns:
        -------
            Enriched order

        """
        if data.amount >= self.config.premium_threshold:
            data.customer = f"{data.customer} (Premium)"
        return data


async def main() -> None:
    """Run the example."""
    # Create sample orders
    orders = [
        Order(id="1", customer="Alice", amount=150.0, status="pending"),
        Order(id="2", customer="Bob", amount=50.0, status="pending"),
        Order(id="3", customer="Charlie", amount=500.0, status="completed"),
        Order(id="4", customer="David", amount=50.0, status="cancelled"),  # Invalid status
    ]

    # Create pipeline
    validation_pipe = ValidationPipe()
    enrichment_pipe = EnrichmentPipe(EnrichConfig(premium_threshold=400.0))
    pipeline: AsyncPipeline[Order, Order] = AsyncPipeline([validation_pipe, enrichment_pipe])

    # Process orders
    for order in orders:
        try:
            result = await pipeline.process(order)
            print(f"Processed order: {result}")
        except Exception as e:
            print(f"Failed to process order {order.id}: {e!s}")


if __name__ == "__main__":
    asyncio.run(main())
