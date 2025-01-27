"""Rivusio - A type-safe data processing pipeline framework with async/sync support.

Copyright (C) 2025 Zbigniew Mastylo
Licensed under the MIT License. See LICENSE for details.
"""
from rivusio.aio import AsyncBasePipe, AsyncPipeline, AsyncStream
from rivusio.config import ParallelConfig, PipeConfig, StreamConfig
from rivusio.core import (
	BasePipe,
    BatchT,
    ExecutionStrategy,
    InputType,
    OutputType,
    PipeError,
    PipelineError,
    T,
)
from rivusio.sync import SyncBasePipe, SyncPipeline, SyncStream

__version__ = "0.2.0"

__all__ = [
    # Base pipe`
    "BasePipe",
    "AsyncBasePipe",
    "SyncBasePipe",
    # Execution
    "ExecutionStrategy",
    # Pipelines
    "AsyncPipeline",
    "SyncPipeline",
    # Streams
    "AsyncStream",
    "SyncStream",
    # Configuration
    "StreamConfig",
    "PipeConfig",
    "ParallelConfig",
    # Errors
    "PipeError",
    "PipelineError",
    # Types
    "T",
    "BatchT",
    "InputType",
    "OutputType",
]
