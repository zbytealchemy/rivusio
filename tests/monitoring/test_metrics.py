import time
from datetime import datetime, timedelta

from rivusio import (
    MetricsCollector,
    MetricValue,
    MetricWindow,
    PipelineMetricsMixin,
)


def test_metric_value() -> None:
    """Test MetricValue creation and properties."""
    timestamp = datetime.now()
    value = 42.0
    metric = MetricValue(timestamp=timestamp, value=value)

    assert metric.timestamp == timestamp
    assert metric.value == value


def test_metrics_collector_initialization() -> None:
    """Test MetricsCollector initialization with custom window size."""
    window_size = timedelta(minutes=10)
    collector = MetricsCollector(window_size=window_size)
    assert collector.window_size == window_size


def test_record_processing_time() -> None:
    """Test recording and retrieving processing times."""
    collector = MetricsCollector()
    collector.record_processing_time(0.5)
    collector.record_processing_time(1.5)

    metrics = collector.get_metrics()
    assert "processing_time" in metrics
    assert metrics["processing_time"].average == 1.0
    assert metrics["processing_time"].min == 0.5
    assert metrics["processing_time"].max == 1.5


def test_record_error() -> None:
    """Test recording and retrieving errors."""
    collector = MetricsCollector()
    collector.record_error()
    collector.record_error()

    metrics = collector.get_metrics()
    assert metrics["error_rate"].average == 1.0


def test_record_success() -> None:
    """Test recording and retrieving successes."""
    collector = MetricsCollector()
    collector.record_success()
    collector.record_success()
    collector.record_success()

    metrics = collector.get_metrics()
    assert metrics["error_rate"].average == 0.0


def test_record_throughput() -> None:
    """Test recording and retrieving throughput."""
    collector = MetricsCollector()
    collector.record_throughput(100)
    collector.record_throughput(200)

    metrics = collector.get_metrics()
    assert metrics["throughput"].average == 150.0


def test_window_cleanup() -> None:
    """Test that old metrics are cleaned up."""
    collector = MetricsCollector(window_size=timedelta(milliseconds=100))
    collector.record_processing_time(1.0)
    time.sleep(0.2)

    collector.record_processing_time(2.0)
    metrics = collector.get_metrics()

    assert metrics["processing_time"].average == 2.0


def test_empty_metrics() -> None:
    """Test metrics when no values have been recorded."""
    collector = MetricsCollector()
    metrics = collector.get_metrics()

    assert metrics["processing_time"].average is None
    assert metrics["error_rate"].average is None
    assert metrics["throughput"].average is None


def test_metric_window() -> None:
    """Test MetricWindow basic functionality."""
    window = MetricWindow(values=[], window_size=timedelta(minutes=5))
    window.add_value(1.0)
    window.add_value(2.0)
    window.add_value(3.0)

    assert window.average == 2.0
    assert window.min == 1.0
    assert window.max == 3.0


def test_metric_window_cleanup() -> None:
    """Test that old values are removed from window."""
    window = MetricWindow(values=[], window_size=timedelta(milliseconds=100))
    window.add_value(1.0)

    import time

    time.sleep(0.2)

    window.add_value(2.0)
    assert window.average == 2.0  # Only the new value should remain


class MockPipe:
    """Mock pipe for testing metrics collection."""

    def __init__(self, name: str, *, include_metrics: bool = True) -> None:
        self.name = name
        if include_metrics:
            self.metrics = MetricsCollector()
            self.metrics.record_processing_time(1.0)


class MockPipelineWithList(PipelineMetricsMixin):
    """Mock pipeline with _pipes attribute."""

    def __init__(self) -> None:
        self._pipes = [
            MockPipe("pipe1"),
            MockPipe("pipe2", include_metrics=False),
            MockPipe("pipe3"),
        ]


class MockPipelineWithMethod(PipelineMetricsMixin):
    """Mock pipeline with pipes method."""

    def __init__(self) -> None:
        self._internal_pipes = [
            MockPipe("pipe1"),
            MockPipe("pipe2"),
        ]

    def pipes(self) -> list[MockPipe]:
        """Get pipeline's pipes."""
        return self._internal_pipes


class MockPipelineWithoutPipes(PipelineMetricsMixin):
    """Mock pipeline without pipes."""



def test_pipeline_metrics_with_pipes_list() -> None:
    """Test metrics collection from pipeline with _pipes list."""
    pipeline = MockPipelineWithList()
    metrics = pipeline.get_metrics()

    assert "pipe1" in metrics
    assert "pipe2" not in metrics  # No metrics for this pipe
    assert "pipe3" in metrics
    assert "processing_time" in metrics["pipe1"]
    assert metrics["pipe1"]["processing_time"].min == 1.0
    assert metrics["pipe1"]["processing_time"].max == 1.0
    assert metrics["pipe1"]["processing_time"].average == 1.0


def test_pipeline_metrics_with_pipes_method() -> None:
    """Test metrics collection from pipeline with pipes method."""
    pipeline = MockPipelineWithMethod()
    metrics = pipeline.get_metrics()

    assert "pipe1" in metrics
    assert "pipe2" in metrics
    assert "processing_time" in metrics["pipe1"]
    assert metrics["pipe1"]["processing_time"].min == 1.0
    assert metrics["pipe1"]["processing_time"].max == 1.0
    assert metrics["pipe1"]["processing_time"].average == 1.0


def test_pipeline_metrics_without_pipes() -> None:
    """Test metrics collection from pipeline without pipes."""
    pipeline = MockPipelineWithoutPipes()
    metrics = pipeline.get_metrics()

    assert metrics == {}
