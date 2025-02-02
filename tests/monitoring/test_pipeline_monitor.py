"""Tests for pipeline monitoring functionality."""
import asyncio
from datetime import timedelta
from time import sleep

import pytest

from rivusio import PipelineMonitor


def test_pipeline_monitor_initialization() -> None:
    """Test PipelineMonitor initialization."""
    window_size = timedelta(minutes=10)
    monitor = PipelineMonitor(window_size=window_size)
    assert monitor.window_size == window_size
    assert monitor.start_time is None
    assert monitor.end_time is None


def test_pipeline_monitor_start_stop() -> None:
    """Test start and stop timing functionality."""
    monitor = PipelineMonitor()

    assert monitor.total_time == 0.0

    monitor.start()
    assert monitor.start_time is not None
    assert monitor.end_time is None

    sleep(0.1)

    monitor.stop()
    assert monitor.end_time is not None


def test_pipeline_monitor_total_time_without_stop() -> None:
    """Test total_time calculation when stop hasn't been called."""
    monitor = PipelineMonitor()
    monitor.start()

    sleep(0.1)

    total_time = monitor.total_time
    assert total_time > 0.0
    assert total_time >= 0.1


def test_pipeline_monitor_total_time_without_start() -> None:
    """Test total_time when start hasn't been called."""
    monitor = PipelineMonitor()
    assert monitor.total_time == 0.0


def test_pipeline_monitor_metrics() -> None:
    """Test metrics collection including total time."""
    monitor = PipelineMonitor()

    monitor.start()

    monitor.record_processing_time(0.5)
    monitor.record_success()
    monitor.record_error()

    sleep(0.1)

    monitor.stop()

    metrics = monitor.get_metrics()

    assert "processing_time" in metrics
    assert "error_rate" in metrics
    assert "throughput" in metrics

    assert "total_time" in metrics
    assert metrics["total_time"] > 0.0
    assert metrics["total_time"] >= 0.1  # At least our sleep time


@pytest.mark.asyncio()
async def test_pipeline_monitor_async_execution() -> None:
    """Test monitoring of async pipeline execution."""
    monitor = PipelineMonitor()

    monitor.start()

    await asyncio.sleep(0.1)
    monitor.record_processing_time(0.1)
    monitor.record_success()

    monitor.stop()

    metrics = monitor.get_metrics()
    assert metrics["total_time"] >= 0.1
    assert metrics["processing_time"].average == 0.1
    assert metrics["error_rate"].average == 0.0


def test_pipeline_monitor_with_context_manager() -> None:
    """Test using monitor with try/finally pattern as shown in docstring."""
    monitor = PipelineMonitor()

    try:
        monitor.start()

        sleep(0.1)
        monitor.record_success()

    except Exception:
        monitor.record_error()
        raise
    finally:
        monitor.stop()

    metrics = monitor.get_metrics()
    assert metrics["total_time"] >= 0.1
    assert metrics["error_rate"].average == 0.0


def test_pipeline_monitor_with_error() -> None:
    """Test monitoring when processing raises an error."""
    monitor = PipelineMonitor()

    with pytest.raises(ValueError):
        try:
            monitor.start()

            sleep(0.1)
            raise ValueError("Test error")

        except Exception:
            monitor.record_error()
            raise
        finally:
            monitor.stop()

    metrics = monitor.get_metrics()
    assert metrics["total_time"] >= 0.1
    assert metrics["error_rate"].average == 1.0
