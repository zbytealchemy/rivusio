"""Plugin system for rivusio."""
from rivusio.plugins.plugins import (
    PluginRegistry,
    register_async_sink,
    register_async_source,
    register_sync_sink,
    register_sync_source,
    registry,
)

__all__ = [
    "PluginRegistry",
    "registry",
    "register_async_source",
    "register_async_sink",
    "register_sync_source",
    "register_sync_sink",
]
