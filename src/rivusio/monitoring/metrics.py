"""Metrics collection and monitoring for data processing pipelines.

This module provides a flexible metrics collection system that tracks various
performance indicators over configurable time windows. It supports collecting,
aggregating, and analyzing metrics such as processing times, error rates,
and throughput.
"""
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MetricValue(BaseModel):
    """A single metric measurement with its timestamp.

    Represents an individual metric measurement taken at a specific point in time.
    Used as the basic building block for time-series metrics collection.

    Attributes
    ----------
        timestamp: When the measurement was taken
        value: The measured value

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    timestamp: datetime
    value: float


class MetricWindow(BaseModel):
    """A sliding time window of metric values.

    Maintains a collection of metric values within a specified time window,
    automatically discarding values that fall outside the window. Provides
    statistical aggregations like average, min, and max.

    Attributes:
    ----------
        values: List of MetricValue objects within the current window
        window_size: Duration of the sliding window

    Example:
    -------
        ```python
        from datetime import timedelta

        # Create a 5-minute window for response times
        window = MetricWindow(
            values=[],
            window_size=timedelta(minutes=5)
        )

        # Add measurements
        window.add_value(0.123)  # 123ms response time

        # Get statistics
        print(f"Average: {window.average:.3f}")  # Average: 0.123
        print(f"Peak: {window.max:.3f}")  # Peak: 0.123
        ```

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    values: list[MetricValue]
    window_size: timedelta

    def add_value(self, value: float) -> None:
        """Add a new measurement to the window.

        Records a new metric value with the current timestamp and removes
        any values that have fallen outside the window.

        Args:
        ----
            value: The metric value to record

        """
        now = datetime.now()
        cutoff = now - self.window_size
        self.values = [v for v in self.values if v.timestamp > cutoff]
        self.values.append(MetricValue(timestamp=now, value=value))

    @property
    def average(self) -> Optional[float]:
        """Calculate the mean value within the current window.

        Returns
        -------
            The average value, or None if the window is empty

        """
        if not self.values:
            return None
        return sum(v.value for v in self.values) / len(self.values)

    @property
    def min(self) -> Optional[float]:
        """Find the minimum value within the current window.

        Returns
        -------
            The minimum value, or None if the window is empty

        """
        if not self.values:
            return None
        return min(v.value for v in self.values)

    @property
    def max(self) -> Optional[float]:
        """Find the maximum value within the current window.

        Returns
        -------
            The maximum value, or None if the window is empty

        """
        if not self.values:
            return None
        return max(v.value for v in self.values)


class MetricsCollector:
    """Collects and aggregates multiple types of metrics over time windows.

    Manages multiple metric windows for different performance indicators like
    processing times, error rates, and throughput. Provides a unified interface
    for recording measurements and retrieving aggregated statistics.

    Example:
    -------
        ```python
        from datetime import timedelta

        # Create collector with 5-minute windows
        collector = MetricsCollector(window_size=timedelta(minutes=5))

        # Record various metrics
        collector.record_processing_time(0.123)  # 123ms processing time
        collector.record_success()  # Record successful operation
        collector.record_throughput(100)  # Processed 100 items

        # Get aggregated metrics
        metrics = collector.get_metrics()
        print(f"Avg processing time: {metrics.processing_time.average:.3f}")
        print(f"Error rate: {metrics.error_rate.average:.1f}")  # Error rate: 0.0
        print(f"Throughput: {metrics.throughput.average:.0f}")  # Throughput: 100
        ```

    """

    def __init__(self, window_size: timedelta = timedelta(minutes=5)) -> None:
        """Initialize metrics collector with specified window size.

        Args:
        ----
            window_size: Duration for the sliding windows. Defaults to 5 minutes

        """
        self.window_size = window_size
        self.processing_times = MetricWindow(values=[], window_size=window_size)
        self.error_rates = MetricWindow(values=[], window_size=window_size)
        self.throughput = MetricWindow(values=[], window_size=window_size)

    def record_processing_time(self, duration: float) -> None:
        """Record the duration of a processing operation.

        Args:
        ----
            duration: Processing time in seconds

        """
        self.processing_times.add_value(duration)

    def record_error(self) -> None:
        """Record an error occurrence.

        Adds a value of 1.0 to the error rate window.
        """
        self.error_rates.add_value(1.0)

    def record_success(self) -> None:
        """Record a successful operation.

        Adds a value of 0.0 to the error rate window.
        """
        self.error_rates.add_value(0.0)

    def record_throughput(self, items: int) -> None:
        """Record the number of items processed.

        Args:
        ----
            items: Number of items processed in this operation

        """
        self.throughput.add_value(float(items))

    def get_metrics(self) -> dict[str, MetricWindow]:
        """Get current metrics for all monitored indicators.

        Returns
        -------
            Dictionary containing aggregated statistics for all metrics:
            processing_time: Statistics about processing duration
            error_rate: Statistics about error frequency
            throughput: Statistics about items processed

        """
        return {
            "processing_time": self.processing_times,
            "error_rate": self.error_rates,
            "throughput": self.throughput,
        }
