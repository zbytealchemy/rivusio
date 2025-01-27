"""Message classes for data processing pipelines.

This module provides the base message types used throughout the pipeline system
for data transport and metadata handling.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


class MessageMetadata(BaseModel):
    """Metadata for messages passing through the pipeline.

    Attributes:
        timestamp: When the message was created
        source: Optional source identifier of the message
        message_id: Unique identifier for the message
        correlation_id: Optional ID to correlate related messages
        headers: Optional dictionary of message headers

    Example:
        ```python
        from datetime import datetime
        from rivusio.core.message import MessageMetadata

        # Create metadata with current timestamp
        metadata = MessageMetadata(
            timestamp=datetime.now(),
            source="sensor_1",
            tags=["temperature", "raw"]
        )

        print(metadata.message_id)  # Unique UUID
        print(metadata.timestamp)   # Current timestamp
        print(metadata.source)      # "sensor_1"
        ```
    """

    timestamp: datetime = datetime.now()
    source: Optional[str] = None
    message_id: str = str(uuid4())
    correlation_id: Optional[str] = None
    headers: dict[str, Any] = {}

    model_config = ConfigDict(frozen=True)


class Message(BaseModel):
    """Base message class for data transport in pipelines.

    A Message encapsulates both the data being processed and additional
    context information (metadata) about the data. This allows pipes to pass
    both the data and its context through the pipeline.

    Attributes:
        value: The actual data being processed. Can be of any type.
        metadata: Optional metadata containing additional information
            about the data such as timestamps, source information,
            processing history, etc.

    Example:
        ```python
        from datetime import datetime
        from rivusio.core.message import Message, MessageMetadata

        # Create a message with sensor data
        message = Message(
            value={
                "temperature": 22.5,
                "humidity": 45.2,
                "unit": "celsius"
            },
            metadata=MessageMetadata(
                source="environmental_sensor",
                correlation_id="batch_xyz",
                headers={
                    "device_id": "env_123",
                    "location": "warehouse_a"
                }
            )
        )

        # Access message data
        print(f"Temperature: {message.value['temperature']}°C")
        print(f"Source: {message.metadata.source}")
        print(f"Timestamp: {message.metadata.timestamp}")
        ```
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    value: Any
    metadata: Optional[dict[str, Any]] = None
