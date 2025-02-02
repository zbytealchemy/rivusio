"""Tests for core configuration classes."""
from typing import Any, Optional

import pytest
from pydantic import BaseModel, Field, ValidationError

from rivusio import PipeConfig


def test_base_pipe_config_defaults() -> None:
    """Test PipeConfig with default values."""
    config = PipeConfig()
    assert isinstance(config, BaseModel)
    assert config.name == "default"


def test_pipe_config_custom_values() -> None:
    """Test PipeConfig with custom values."""
    config = PipeConfig(name="custom_pipe")
    assert config.name == "custom_pipe"


def test_pipe_config_inheritance() -> None:
    """Test inheriting from PipeConfig."""
    class CustomConfig(PipeConfig):
        retries: int = 3
        timeout: float = 5.0
        optional_value: Optional[str] = None

    config = CustomConfig(name="custom", timeout=10.0)
    assert config.name == "custom"
    assert config.retries == 3
    assert config.timeout == 10.0
    assert config.optional_value is None


def test_pipe_config_validation() -> None:
    """Test PipeConfig field validation."""
    class ValidatedConfig(PipeConfig):
        count: int = Field(0, ge=0, le=100)
        identifier: str = Field("default", min_length=3)

    config = ValidatedConfig(name="validator", count=50, identifier="test_pipe")
    assert config.name == "validator"
    assert config.count == 50
    assert config.identifier == "test_pipe"

    with pytest.raises(ValidationError):
        ValidatedConfig(name="test", count=-1, identifier="test")

    with pytest.raises(ValidationError):
        ValidatedConfig(name="test", count=101, identifier="test")

    with pytest.raises(ValidationError):
        ValidatedConfig(name="test", count=0, identifier="ab")


def test_pipe_config_nested() -> None:
    """Test nested PipeConfig configurations."""
    class DatabaseConfig(PipeConfig):
        host: str = "localhost"
        port: int = 5432
        username: Optional[str] = None

    class AppConfig(PipeConfig):
        database: DatabaseConfig = DatabaseConfig()
        debug: bool = False

    config = AppConfig(name="app")
    assert config.name == "app"
    assert config.database.host == "localhost"
    assert config.database.port == 5432
    assert config.database.username is None
    assert config.debug is False


def test_pipe_config_dict_conversion() -> None:
    """Test PipeConfig to/from dict conversion."""
    class TestConfig(PipeConfig):
        custom_value: int = 0
        flag: bool = False

    config = TestConfig(name="test", custom_value=42)
    config_dict = config.model_dump()

    assert config_dict["name"] == "test"
    assert config_dict["custom_value"] == 42
    assert config_dict["flag"] is False

    new_config = TestConfig.model_validate(config_dict)
    assert new_config.name == config.name
    assert new_config.custom_value == config.custom_value
    assert new_config.flag == config.flag


def test_pipe_config_custom_validation() -> None:
    """Test PipeConfig with custom validation."""
    class RangeConfig(PipeConfig):
        min_val: int = 0
        max_val: int = 10

        @property
        def range(self) -> int:
            return self.max_val - self.min_val

        def model_post_init(self, __context: Any) -> None:
            super().model_post_init(__context)
            if self.min_val >= self.max_val:
                raise ValueError("min_val must be less than max_val")

    config = RangeConfig(name="range", min_val=0, max_val=10)
    assert config.name == "range"
    assert config.range == 10

    with pytest.raises(ValueError):
        RangeConfig(name="invalid", min_val=10, max_val=0)
