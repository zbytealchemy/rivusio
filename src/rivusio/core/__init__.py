"""Core module for Rivusio."""

from rivusio.core.base import BasePipe
from rivusio.core.exceptions import PipeError, PipelineError
from rivusio.core.execution_strategy import ExecutionStrategy
from rivusio.core.message import Message, MessageMetadata
from rivusio.core.metrics import PipelineMetricsMixin
from rivusio.core.types import BatchT, InputType, OutputType, StreamType, T

__all__ = [
    # Base classes
    "BasePipe",
    # Messages
    "Message",
    "MessageMetadata",
    # Metrics
    "PipelineMetricsMixin",
    # Exceptions
    "PipeError",
    "PipelineError",
    # Execution
    "ExecutionStrategy",
    # Types
    "BatchT",
    "InputType",
    "OutputType",
    "StreamType",
    "T",
]
