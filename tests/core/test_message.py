from datetime import datetime
from typing import Any

from rivusio.core.message import Message


def test_message_creation() -> None:
    """Test basic message creation and properties."""
    data = {"key": "value"}
    metadata = {"timestamp": datetime.now(), "source": "test_source", "message_id": "123"}
    message = Message(value=data, metadata=metadata)

    assert message.value == data
    assert message.metadata == metadata
    assert message.metadata["source"] == "test_source"
    assert message.metadata["message_id"] == "123"


def test_message_metadata_defaults() -> None:
    """Test message metadata with default values."""
    data = ["item1", "item2"]
    message = Message(value=data)

    assert message.value == data
    assert message.metadata is None


def test_message_metadata_custom() -> None:
    """Test message metadata with custom values."""
    timestamp = datetime.now()
    metadata = {
        "timestamp": timestamp,
        "source": "custom_source",
        "message_id": "custom_id",
        "correlation_id": "corr_123",
        "headers": {"content-type": "application/json"},
    }
    message = Message(value="test", metadata=metadata)

    assert message.metadata is not None  # Type guard
    assert message.metadata["timestamp"] == timestamp
    assert message.metadata["source"] == "custom_source"
    assert message.metadata["message_id"] == "custom_id"
    assert message.metadata["correlation_id"] == "corr_123"
    assert message.metadata["headers"] == {"content-type": "application/json"}


def test_message_metadata_optional_fields() -> None:
    """Test message metadata with optional fields."""
    metadata = {
        "timestamp": datetime.now(),
    }
    message = Message(value="test", metadata=metadata)

    assert message.metadata is not None  # Type guard
    assert "source" not in message.metadata
    assert "correlation_id" not in message.metadata
    assert "headers" not in message.metadata


def test_message_equality() -> None:
    """Test message equality comparison."""
    metadata = {"timestamp": datetime.now(), "source": "source", "message_id": "id1"}

    msg1 = Message(value={"key": "value"}, metadata=metadata)
    msg2 = Message(value={"key": "value"}, metadata=metadata.copy())
    msg3 = Message(value={"key": "different"}, metadata=metadata.copy())

    assert msg1 == msg2
    assert msg1 != msg3
    assert msg1 != "not a message"


def test_message_repr() -> None:
    """Test string representation of message."""
    data = {"test": "data"}
    message = Message(value=data)

    repr_str = repr(message)
    assert "Message" in repr_str
    assert str(data) in repr_str


def test_message_with_none_value() -> None:
    """Test message creation with None value."""
    message = Message(value=None)
    assert message.value is None


def test_message_custom_type() -> None:
    """Test message with custom type value."""

    class CustomType:
        def __init__(self, x: Any) -> None:
            self.x = x

    value = CustomType(42)
    message = Message(value=value)
    assert message.value.x == 42
