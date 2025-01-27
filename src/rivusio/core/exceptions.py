"""Core exceptions for the Rivusio pipeline framework.

This module defines the base exception hierarchy used throughout the framework
for error handling and reporting.
"""


class PipeError(Exception):
    """Exception raised when an error occurs within a single pipe.

    This exception wraps the original error that occurred during pipe processing
    and provides context about which pipe failed.

    Attributes:
        pipe: Name or identifier of the pipe where the error occurred
        error: The original exception that was raised

    Example:
        ```python
        from rivusio.core.pipe import BasePipe
        from typing import Dict

        class DataValidationPipe(BasePipe[Dict, Dict]):
            async def process(self, data: Dict) -> Dict:
                try:
                    return await validate_data(data)
                except ValidationError as e:
                    raise PipeError(self.__class__.__name__, e)

        # Create and use the pipe
        pipe = DataValidationPipe()
        try:
            await pipe.process({"invalid": "data"})
        except PipeError as e:
            print(f"Pipe: {e.pipe}, Error: {e.error}")
        ```
    """

    def __init__(self, pipe: str, error: Exception) -> None:
        """Initialize a PipeError.

        Args:
            pipe: Name or identifier of the pipe where the error occurred
            error: The original exception that was raised
        """
        self.pipe = pipe
        self.error = error
        super().__init__(f"Error in pipe {pipe}: {error}")


class PipelineError(PipeError):
    """Exception raised when an error occurs at the pipeline level.

    This exception is typically raised when there's an error coordinating
    multiple pipes or when pipeline-wide operations fail. It captures both
    the failing pipe and the original error.

    Attributes:
        pipe: Name or identifier of the pipe where the error occurred
        error: The original exception that was raised

    Example:
        ```python
        from rivusio.core.pipeline import AsyncPipeline

        # Create pipeline with multiple pipes
        pipeline = AsyncPipeline([pipe1, pipe2, pipe3])

        try:
            await pipeline.process(data)
        except PipelineError as e:
            print(f"Failed pipe: {e.pipe}")
            print(f"Error details: {e.error}")
        ```
    """

    def __init__(self, pipe: str, error: Exception) -> None:
        """Initialize a PipelineError.

        Args:
            pipe: Name or identifier of the pipe where the error occurred
            error: The original exception that was raised
        """
        super().__init__(pipe, error)
