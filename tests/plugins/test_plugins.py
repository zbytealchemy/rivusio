"""Test plugin system functionality."""
from typing import Any

import pytest

from rivusio import AsyncBasePipe, SyncBasePipe
from rivusio.plugins.plugins import (
    PluginRegistry,
    register_async_sink,
    register_async_source,
    register_sync_sink,
    register_sync_source,
)


class MockAsyncSource(AsyncBasePipe[Any, Any]):
    async def process(self, data: Any) -> Any:
        return data


class MockAsyncSink(AsyncBasePipe[Any, Any]):
    async def process(self, data: Any) -> Any:
        return data


class MockSyncSource(SyncBasePipe[Any, Any]):
    def process(self, data: Any) -> Any:
        return data


class MockSyncSink(SyncBasePipe[Any, Any]):
    def process(self, data: Any) -> Any:
        return data


def test_plugin_registry_initialization() -> None:
    """Test PluginRegistry initialization."""
    registry = PluginRegistry()
    assert len(registry._async_sources) == 0
    assert len(registry._async_sinks) == 0
    assert len(registry._sync_sources) == 0
    assert len(registry._sync_sinks) == 0


def test_plugin_registry_singleton() -> None:
    """Test PluginRegistry singleton pattern."""
    registry1 = PluginRegistry()
    registry2 = PluginRegistry()
    assert registry1 is registry2


def test_register_async_source() -> None:
    """Test registering async source."""
    registry = PluginRegistry()

    @registry.register_async_source("test_source")
    class DummyAsyncSource(MockAsyncSource):
        pass

    assert len(registry._async_sources) == 1
    assert "test_source" in registry._async_sources


def test_register_async_sink() -> None:
    """Test registering async sink."""
    registry = PluginRegistry()

    @registry.register_async_sink("test_sink")
    class DummyAsyncSink(MockAsyncSink):
        pass

    assert len(registry._async_sinks) == 1
    assert "test_sink" in registry._async_sinks


def test_register_sync_source() -> None:
    """Test registering sync source."""
    registry = PluginRegistry()

    @registry.register_sync_source("test_source")
    class DummySyncSource(MockSyncSource):
        pass

    assert len(registry._sync_sources) == 1
    assert "test_source" in registry._sync_sources


def test_register_sync_sink() -> None:
    """Test registering sync sink."""
    registry = PluginRegistry()

    @registry.register_sync_sink("test_sink")
    class DummySyncSink(MockSyncSink):
        pass

    assert len(registry._sync_sinks) == 1
    assert "test_sink" in registry._sync_sinks


def test_register_invalid_async_source() -> None:
    """Test registering invalid async source."""
    registry = PluginRegistry()

    with pytest.raises(TypeError):
        @registry.register_async_source("test_source")  # type: ignore[type-var]
        class DummyAsyncSource:
            async def process(self, data: Any) -> Any:
                return data


def test_register_invalid_async_sink() -> None:
    """Test registering invalid async sink."""
    registry = PluginRegistry()

    with pytest.raises(TypeError):
        @registry.register_async_sink("test_sink")  # type: ignore[type-var]
        class DummyAsyncSink:
            pass


def test_register_invalid_sync_source() -> None:
    """Test registering invalid sync source."""
    registry = PluginRegistry()

    with pytest.raises(TypeError):
        @registry.register_sync_source("test_source")  # type: ignore[type-var]
        class DummySyncSource:
            pass


def test_register_invalid_sync_sink() -> None:
    """Test registering invalid sync sink."""
    registry = PluginRegistry()

    with pytest.raises(TypeError):
        @registry.register_sync_sink("test_sink")  # type: ignore[type-var]
        class DummySyncSink:
            pass


def test_duplicate_registration() -> None:
    """Test registering duplicate names."""
    registry = PluginRegistry()

    @registry.register_async_source("test_source")
    class DummyAsyncSource1(MockAsyncSource):
        pass

    with pytest.raises(ValueError):
        @registry.register_async_source("test_source")
        class DummyAsyncSource2(MockAsyncSource):
            pass


def test_global_registry_functions() -> None:
    """Test global registry decorator functions."""

    @register_async_source("test_source")
    class DummyAsyncSource(MockAsyncSource):
        pass

    @register_async_sink("test_sink")
    class DummyAsyncSink(MockAsyncSink):
        pass

    @register_sync_source("test_source")
    class DummySyncSource(MockSyncSource):
        pass

    @register_sync_sink("test_sink")
    class DummySyncSink(MockSyncSink):
        pass

    registry = PluginRegistry()
    assert "test_source" in registry._async_sources
    assert "test_sink" in registry._async_sinks
    assert "test_source" in registry._sync_sources
    assert "test_sink" in registry._sync_sinks


def test_get_registered_plugins() -> None:
    """Test getting all registered plugins."""
    registry = PluginRegistry()

    @registry.register_async_source("source1")
    class DummyAsyncSource(MockAsyncSource):
        pass

    @registry.register_async_sink("sink1")
    class DummyAsyncSink(MockAsyncSink):
        pass

    @registry.register_sync_source("source2")
    class DummySyncSource(MockSyncSource):
        pass

    @registry.register_sync_sink("sink2")
    class DummySyncSink(MockSyncSink):
        pass

    plugins = registry.get_registered_plugins()

    # Check all plugin types are present
    assert "async_sources" in plugins
    assert "async_sinks" in plugins
    assert "sync_sources" in plugins
    assert "sync_sinks" in plugins

    # Check specific plugins are registered
    assert "source1" in plugins["async_sources"]
    assert "sink1" in plugins["async_sinks"]
    assert "source2" in plugins["sync_sources"]
    assert "sink2" in plugins["sync_sinks"]


def test_get_nonexistent_plugins() -> None:
    """Test getting nonexistent plugins."""
    registry = PluginRegistry()
    with pytest.raises(KeyError):
        registry.get_async_source("nonexistent")
    with pytest.raises(KeyError):
        registry.get_async_sink("nonexistent")
    with pytest.raises(KeyError):
        registry.get_sync_source("nonexistent")
    with pytest.raises(KeyError):
        registry.get_sync_sink("nonexistent")
