"""Tests for stream configuration."""
from datetime import timedelta

import pytest
from pydantic import ValidationError

from rivusio.config.stream import StreamConfig


def test_stream_config_defaults() -> None:
    """Test StreamConfig default values."""
    config = StreamConfig()
    assert config.name is None
    assert config.retry_attempts == 3
    assert config.retry_delay == 1.0
    assert config.retry_backoff == 2.0
    assert config.timeout == 30.0
    assert config.batch_size == 1
    assert config.window_size == timedelta(seconds=0)
    assert config.buffer_size == 1000
    assert config.collect_metrics is True
    assert config.skip_none is True


def test_stream_config_custom_values() -> None:
    """Test StreamConfig with custom values."""
    config = StreamConfig(
        name="test_stream",
        batch_size=100,
        window_size=timedelta(minutes=5),
        buffer_size=5000,
    )
    assert config.name == "test_stream"
    assert config.batch_size == 100
    assert config.window_size == timedelta(minutes=5)
    assert config.buffer_size == 5000


def test_stream_config_validation() -> None:
    """Test StreamConfig validation."""
    with pytest.raises(ValidationError):
        StreamConfig(retry_attempts=-1)

    with pytest.raises(ValidationError):
        StreamConfig(batch_size=0)

    with pytest.raises(ValidationError):
        StreamConfig(buffer_size=0)


def test_stream_config_retry_settings() -> None:
    """Test StreamConfig retry settings."""
    config = StreamConfig(
        retry_attempts=5,
        retry_delay=2.0,
        retry_backoff=1.5,
    )
    assert config.retry_attempts == 5
    assert config.retry_delay == 2.0
    assert config.retry_backoff == 1.5


def test_stream_config_metrics_settings() -> None:
    """Test StreamConfig metrics settings."""
    config = StreamConfig(collect_metrics=False)
    assert config.collect_metrics is False
