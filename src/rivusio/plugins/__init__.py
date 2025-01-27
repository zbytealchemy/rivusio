"""Plugin system for rivusio."""
from rivusio.plugins.plugins import (
    register_async_sink,
    register_async_source,
    register_sync_sink,
    register_sync_source,
)

__all__ = [
    "register_async_source",
    "register_async_sink",
    "register_sync_source",
    "register_sync_sink",
]
