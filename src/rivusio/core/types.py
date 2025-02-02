"""Type definitions for Rivusio."""

from collections.abc import Sequence
from typing import Any, TypeVar, Union

# Generic type parameter
T = TypeVar("T")

# Batch type must be a sequence
BatchT = TypeVar("BatchT", bound=Sequence[Any])

# Contravariant - can accept more general types)
InputType = TypeVar("InputType", contravariant=True)

# Covariant output type (can return more specific types)
OutputType = TypeVar("OutputType", covariant=True)

StreamType = Union[T, BatchT]
