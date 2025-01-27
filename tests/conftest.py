"""Test configuration and fixtures."""
import asyncio
import warnings
from collections.abc import Generator
from typing import Any

import pytest
from pydantic._internal._config import PydanticDeprecatedSince20

from rivusio.plugins.plugins import PluginRegistry

# Suppress PydanticDeprecatedSince20 warning
warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _clear_plugin_registry() -> Any:  # Added underscore prefix
    """Clear the plugin registry before each test."""
    registry = PluginRegistry()
    registry._async_sources.clear()
    registry._async_sinks.clear()
    registry._sync_sources.clear()
    registry._sync_sinks.clear()
    return
