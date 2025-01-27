# Plugins API Reference

## PluginRegistry

::: rivusio.plugins.plugins.PluginRegistry
    options:
      show_root_heading: true
      show_source: true

## Plugin Decorators

### register_async_source

::: rivusio.plugins.plugins.PluginRegistry.register_async_source
    options:
      show_root_heading: true
      show_source: true

### register_async_sink

::: rivusio.plugins.plugins.PluginRegistry.register_async_sink
    options:
      show_root_heading: true
      show_source: true

### register_sync_source

::: rivusio.plugins.plugins.PluginRegistry.register_sync_source
    options:
      show_root_heading: true
      show_source: true

### register_sync_sink

::: rivusio.plugins.plugins.PluginRegistry.register_sync_sink
    options:
      show_root_heading: true
      show_source: true

## Global Registry

The `registry` object is a global singleton instance of `PluginRegistry` that should be used for all plugin registration:

```python
from rivusio.plugins import registry
```
