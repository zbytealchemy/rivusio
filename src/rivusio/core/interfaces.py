"""Common interfaces for Rivusio components."""
from typing import Any, Protocol, TypeVar, runtime_checkable

# Contravariant - can accept more general types)
InputType = TypeVar("InputType", contravariant=True)

# Covariant output type (can return more specific types)
OutputType = TypeVar("OutputType", covariant=True)
IntermediateType = TypeVar("IntermediateType")


@runtime_checkable
class ParallelizablePipeline(Protocol[InputType, OutputType]):
    """Protocol for pipelines that support parallel execution."""

    @property
    def pipes(self) -> list[Any]:
        """Get pipeline's pipes."""

    async def process(self, data: InputType) -> OutputType:
        """Process a single item through the pipeline."""
