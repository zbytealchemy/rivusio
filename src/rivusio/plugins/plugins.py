"""Plugin system for rivusio."""

from collections.abc import Callable
from typing import Optional, TypeVar, Union, cast

from rivusio.aio import AsyncBasePipe
from rivusio.sync import SyncBasePipe

AsyncT = TypeVar("AsyncT", bound=AsyncBasePipe)
SyncT = TypeVar("SyncT", bound=SyncBasePipe)
AnyPipe = Union[AsyncBasePipe, SyncBasePipe]


class PluginRegistry:
    """Registry for rivusio plugins."""

    _instance: Optional["PluginRegistry"] = None
    _initialized: bool
    _async_sources: dict[str, type[AsyncBasePipe]]
    _async_sinks: dict[str, type[AsyncBasePipe]]
    _sync_sources: dict[str, type[SyncBasePipe]]
    _sync_sinks: dict[str, type[SyncBasePipe]]

    def __new__(cls) -> "PluginRegistry":
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize plugin registry."""
        if not hasattr(self, "_initialized") or not self._initialized:
            self._async_sources = {}
            self._async_sinks = {}
            self._sync_sources = {}
            self._sync_sinks = {}
            self._initialized = True

    def register_async_source(self, name: str) -> Callable[[type[AsyncT]], type[AsyncT]]:
        """Register an async source pipe.

        Args:
            name: Name of the source pipe

        Returns:
            Decorator function

        """

        def decorator(cls: type[AsyncT]) -> type[AsyncT]:
            if not issubclass(cls, AsyncBasePipe):
                raise TypeError(f"{cls.__name__} must inherit from AsyncBasePipe")
            if name in self._async_sources:
                raise ValueError(f"Async source '{name}' is already registered")
            self._async_sources[name] = cls
            return cls

        return decorator

    def register_async_sink(self, name: str) -> Callable[[type[AsyncT]], type[AsyncT]]:
        """Register an async sink pipe.

        Args:
            name: Name of the sink pipe

        Returns:
            Decorator function

        """

        def decorator(cls: type[AsyncT]) -> type[AsyncT]:
            if not issubclass(cls, AsyncBasePipe):
                raise TypeError(f"{cls.__name__} must inherit from AsyncBasePipe")
            if name in self._async_sinks:
                raise ValueError(f"Async sink '{name}' is already registered")
            self._async_sinks[name] = cls
            return cls

        return decorator

    def register_sync_source(self, name: str) -> Callable[[type[SyncT]], type[SyncT]]:
        """Register a sync source pipe.

        Args:
            name: Name of the source pipe

        Returns:
            Decorator function

        """

        def decorator(cls: type[SyncT]) -> type[SyncT]:
            if not issubclass(cls, SyncBasePipe):
                raise TypeError(f"{cls.__name__} must inherit from SyncBasePipe")
            if name in self._sync_sources:
                raise ValueError(f"Sync source '{name}' is already registered")
            self._sync_sources[name] = cls
            return cls

        return decorator

    def register_sync_sink(self, name: str) -> Callable[[type[SyncT]], type[SyncT]]:
        """Register a sync sink pipe.

        Args:
            name: Name of the sink pipe

        Returns:
            Decorator function

        """

        def decorator(cls: type[SyncT]) -> type[SyncT]:
            if not issubclass(cls, SyncBasePipe):
                raise TypeError(f"{cls.__name__} must inherit from SyncBasePipe")
            if name in self._sync_sinks:
                raise ValueError(f"Sync sink '{name}' is already registered")
            self._sync_sinks[name] = cls
            return cls

        return decorator

    def get_async_source(self, name: str) -> type[AsyncBasePipe]:
        """Get an async source pipe by name.

        Args:
            name: Name of the source pipe

        Returns:
            Source pipe class

        Raises:
            KeyError: If source pipe not found

        """
        try:
            return self._async_sources[name]
        except KeyError as e:
            raise KeyError(f"Async source '{name}' not found") from e

    def get_async_sink(self, name: str) -> type[AsyncBasePipe]:
        """Get an async sink pipe by name.

        Args:
            name: Name of the sink pipe

        Returns:
            Sink pipe class

        Raises:
            KeyError: If sink pipe not found

        """
        try:
            return self._async_sinks[name]
        except KeyError as e:
            raise KeyError(f"Async sink '{name}' not found") from e

    def get_sync_source(self, name: str) -> type[SyncBasePipe]:
        """Get a sync source pipe by name.

        Args:
            name: Name of the source pipe

        Returns:
            Source pipe class

        Raises:
            KeyError: If source pipe not found

        """
        try:
            return self._sync_sources[name]
        except KeyError as e:
            raise KeyError(f"Sync source '{name}' not found") from e

    def get_sync_sink(self, name: str) -> type[SyncBasePipe]:
        """Get a sync sink pipe by name.

        Args:
            name: Name of the sink pipe

        Returns:
            Sink pipe class

        Raises:
            KeyError: If sink pipe not found

        """
        try:
            return self._sync_sinks[name]
        except KeyError as e:
            raise KeyError(f"Sync sink '{name}' not found") from e

    def list_async_sources(self) -> dict[str, type[AsyncBasePipe]]:
        """List all registered async source pipes.

        Returns
            Dictionary of registered async source pipes

        """
        return self._async_sources.copy()

    def list_async_sinks(self) -> dict[str, type[AsyncBasePipe]]:
        """List all registered async sink pipes.

        Returns
            Dictionary of registered async sink pipes

        """
        return self._async_sinks.copy()

    def list_sync_sources(self) -> dict[str, type[SyncBasePipe]]:
        """List all registered sync source pipes.

        Returns
            Dictionary of registered sync source pipes

        """
        return self._sync_sources.copy()

    def list_sync_sinks(self) -> dict[str, type[SyncBasePipe]]:
        """List all registered sync sink pipes.

        Returns
            Dictionary of registered sync sink pipes

        """
        return self._sync_sinks.copy()

    def get_registered_plugins(self) -> dict[str, dict[str, type[AnyPipe]]]:
        """Get all registered plugins.

        Returns
            Dictionary containing all registered plugins grouped by type:
            {
                "async_sources": {...},
                "async_sinks": {...},
                "sync_sources": {...},
                "sync_sinks": {...}
            }

        """
        return {
            "async_sources": cast(dict, self._async_sources.copy()),
            "async_sinks": cast(dict, self._async_sinks.copy()),
            "sync_sources": cast(dict, self._sync_sources.copy()),
            "sync_sinks": cast(dict, self._sync_sinks.copy()),
        }


# Global registry instance
registry = PluginRegistry()

# Decorator exports
register_async_source = registry.register_async_source
register_async_sink = registry.register_async_sink
register_sync_source = registry.register_sync_source
register_sync_sink = registry.register_sync_sink
