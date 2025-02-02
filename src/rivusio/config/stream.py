"""Stream configuration."""

from datetime import timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StreamConfig(BaseModel):
    """Configuration for stream processing behavior.

    Controls various aspects of stream processing including retry behavior,
    timeouts, batch sizes, and window settings.

    Attributes:
        name: Optional name for the stream instance
        retry_attempts: Number of retry attempts for failed operations
        retry_delay: Initial delay between retries in seconds
        retry_backoff: Multiplier for retry delay after each attempt
        timeout: Operation timeout in seconds
        batch_size: Number of items to process in each batch
        window_size: Time window duration for window-based processing
        buffer_size: Maximum number of items to buffer
        collect_metrics: Whether to collect processing metrics

    Example:
        ```python
        config = StreamConfig(
            name="sensor_stream",
            batch_size=100,
            window_size=timedelta(minutes=5),
            buffer_size=1000
        )
        ```
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: Optional[str] = None
    retry_attempts: int = Field(default=3, ge=0)
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    timeout: float = 30.0
    batch_size: int = Field(default=1, gt=0)
    window_size: timedelta = timedelta(seconds=0)
    buffer_size: int = Field(default=1000, gt=0)
    collect_metrics: bool = True
    skip_none: bool = True

    @field_validator("retry_attempts")
    @classmethod
    def validate_retry_attempts(cls, v: int) -> int:
        """Validate retry attempts."""
        if v < 0:
            raise ValueError("retry_attempts must be non-negative")
        return v

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        """Validate batch size."""
        if v < 1:
            raise ValueError("batch_size must be positive")
        return v
