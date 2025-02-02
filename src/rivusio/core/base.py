"""Base classes and interfaces for Rivusio pipelines."""

from abc import ABC
from typing import Generic, Optional

from rivusio.core.types import InputType, OutputType


class BasePipe(ABC, Generic[InputType, OutputType]):
    """Base class for all pipes."""

    def __init__(self, name: Optional[str] = None) -> None:
        """Initialize pipe.

        Args:
            name: Name of the pipe
        """
        self.name = name or self.__class__.__name__

    def __str__(self) -> str:
        """Get string representation of pipe."""
        return self.name

    def __repr__(self) -> str:
        """Get string representation of pipe."""
        return f"<{self.name}>"
