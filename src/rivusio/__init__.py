"""Rivusio - A type-safe data processing pipeline framework with async/sync support.

Copyright (C) 2025 Zbigniew Mastylo
Licensed under the MIT License. See LICENSE for details.
"""
from rivusio.core.config import PipeConfig
from rivusio.core.exceptions import PipeError, PipelineError
from rivusio.core.pipe import AsyncBasePipe, AsyncPipe, SyncBasePipe, SyncPipe
from rivusio.core.pipeline import AsyncPipeline, MixedPipeline, SyncPipeline
from rivusio.streams.stream import AsyncStream, StreamConfig, SyncStream

__version__ = "0.1.0"

__all__ = [
    "AsyncBasePipe",
    "AsyncPipe",
    "SyncBasePipe",
    "SyncPipe",
    "AsyncPipeline",
    "SyncPipeline",
    "MixedPipeline",
    "AsyncStream",
    "SyncStream",
    "StreamConfig",
    "PipeConfig",
    "PipeError",
    "PipelineError",
]
