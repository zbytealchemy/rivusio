"""Configuration classes for pipes and streams."""

from pydantic import BaseModel


class PipeConfig(BaseModel):
    """Base configuration model for all pipes.

    All pipe configurations should inherit from this class to ensure
    consistent configuration handling across the pipeline system.

    Attributes:
        name: Optional name for the pipe instance. Defaults to "default"
        description: Optional description of the pipe's purpose. Defaults to empty string

    Example:
        ```python
        class ProcessorConfig(PipeConfig):
            retries: int = 3
            retry_delay: float = 1.0
            timeout: float = 5.0

        config = ProcessorConfig(
            name="data_processor",
            description="Processes incoming data with retries"
        )
        pipe = AsyncPipe(processor_func, config=config)
        ```
    """

    name: str = "default"
    description: str = ""

    model_config = {
        "extra": "allow",  # Allow additional fields in subclasses
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }
