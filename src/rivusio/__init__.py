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
    Message,
    MessageMetadata,
    OutputType,
    PipeError,
    PipelineError,
    PipelineMetricsMixin,
    T,
)
from rivusio.monitoring import MetricsCollector, MetricValue, MetricWindow, PipelineMonitor
from rivusio.plugins import (
    PluginRegistry,
    register_async_sink,
    register_async_source,
    register_sync_sink,
    register_sync_source,
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
    "PipelineMetricsMixin",
    # Messages
    "Message",
    "MessageMetadata",
    # Streams
    "AsyncStream",
    "SyncStream",
    # Configuration
    "StreamConfig",
    "PipeConfig",
    "ParallelConfig",
    # Monitoring
    "MetricsCollector",
    "PipelineMonitor",
    "MetricValue",
    "MetricWindow",
    # Plugins
    "PluginRegistry",
    "register_async_sink",
    "register_async_source",
    "register_sync_sink",
    "register_sync_source",
    # Errors
    "PipeError",
    "PipelineError",
    # Types
    "T",
    "BatchT",
    "InputType",
    "OutputType",
]
