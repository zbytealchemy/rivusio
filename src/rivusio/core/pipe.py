"""Base classes for pipe components."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from rivusio.core.interfaces import InputType, OutputType

Any = TypeVar("Any")


class BasePipe(ABC, Generic[InputType, OutputType]):
    """Base class for all pipes."""

    @abstractmethod
    def __init__(self) -> None:
        """Initialize pipe."""
        self.name: str = self.__class__.__name__


class AsyncBasePipe(BasePipe[InputType, OutputType]):
    """Base class for async pipes."""

    def __init__(self) -> None:
        """Initialize pipe."""
        super().__init__()

    @abstractmethod
    async def process(self, data: InputType) -> OutputType:
        """Process data through the pipe.

        Args:
        ----
            data: Input data

        Returns:
        -------
            Processed data

        """

    async def __call__(self, data: InputType) -> OutputType:
        """Process data when pipe is called as a function."""
        return await self.process(data)


class SyncBasePipe(BasePipe[InputType, OutputType]):
    """Base class for sync pipes."""

    def __init__(self) -> None:
        """Initialize pipe."""
        super().__init__()

    @abstractmethod
    def process(self, data: InputType) -> OutputType:
        """Process data through the pipe.

        Args:
        ----
            data: Input data

        Returns:
        -------
            Processed data

        """

    def __call__(self, data: InputType) -> OutputType:
        """Process data when pipe is called as a function."""
        return self.process(data)


# Simple aliases for backward compatibility
AsyncPipe = AsyncBasePipe
SyncPipe = SyncBasePipe
