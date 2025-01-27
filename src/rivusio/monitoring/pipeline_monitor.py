"""Pipeline monitoring and metrics collection.

This module provides specialized monitoring capabilities for data processing pipelines,
extending the base metrics collection system with pipeline-specific features like
execution timing and pipeline-level statistics.
"""
from datetime import datetime, timedelta
from typing import Any, Optional

from .metrics import MetricsCollector


class PipelineMonitor(MetricsCollector):
    """Monitor for collecting pipeline execution metrics with timing capabilities.

    Extends the base MetricsCollector with pipeline-specific features:
    - Pipeline execution timing (start/stop/total time)
    - Pipeline-level success/error rates
    - Processing throughput monitoring

    Example:
    -------
        ```python
        from datetime import timedelta
        from rivusio.monitoring import PipelineMonitor

        # Create and attach monitor to pipeline
        monitor = PipelineMonitor(window_size=timedelta(minutes=10))
        pipeline.set_monitor(monitor)

        # Start monitoring
        monitor.start()

        try:
            # Process data
            await pipeline.process(data)
            monitor.record_success()
        except Exception as e:
            monitor.record_error()
            raise
        finally:
            monitor.stop()

        # Get metrics
        metrics = monitor.get_metrics()
        print(f"Total time: {metrics['total_time']:.2f}s")  # Total time: 1.23s
        print(f"Error rate: {metrics['error_rate']['avg']:.2%}")  # Error rate: 0.00%
        ```

    """

    def __init__(self, window_size: timedelta = timedelta(minutes=5)) -> None:
        """Initialize pipeline monitor.

        Args:
        ----
            window_size: Time window for metrics aggregation. Controls how long
                        measurements are kept for calculating statistics.
                        Defaults to 5 minutes.

        """
        super().__init__(window_size=window_size)
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None

    @property
    def start_time(self) -> Optional[datetime]:
        """Return the start time of the pipeline execution."""
        return self._start_time

    @property
    def end_time(self) -> Optional[datetime]:
        """Return the end time of the pipeline execution."""
        return self._end_time

    def start(self) -> None:
        """Start monitoring pipeline execution.

        Records the start time for pipeline execution timing. Should be called
        before pipeline processing begins.
        """
        self._start_time = datetime.now()

    def stop(self) -> None:
        """Stop monitoring pipeline execution.

        Records the end time for pipeline execution timing. Should be called
        after pipeline processing completes (in success or failure cases).

        Note:
        ----
            Should typically be called in a finally block to ensure timing
            is recorded even if processing fails.

        """
        self._end_time = datetime.now()

    @property
    def total_time(self) -> float:
        """Get total execution time in seconds.

        Calculates the total time elapsed between start() and stop() calls.
        If stop() hasn't been called yet, uses the current time as end time.
        If start() hasn't been called, returns 0.0.

        Returns
        -------
            Total execution time in seconds as a float.
            Returns 0.0 if monitoring hasn't started.

        """
        if not self._start_time:
            return 0.0
        end = self._end_time or datetime.now()
        return (end - self._start_time).total_seconds()

    def get_metrics(self) -> dict[str, Any]:
        """Get all collected metrics including total execution time.

        Extends the base metrics collection with pipeline-specific metrics
        including total execution time.

        Returns
        -------
            Dictionary containing all metrics:
            - All base metrics (processing_time, error_rate, throughput)
            - total_time: Total pipeline execution time in seconds

        """
        metrics = super().get_metrics()
        metrics["total_time"] = self.total_time  # type: ignore
        return metrics
