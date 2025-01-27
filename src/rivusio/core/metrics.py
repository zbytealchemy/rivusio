"""Metrics collection functionality for pipelines."""
from typing import Any, cast


class PipelineMetricsMixin:
    """Mixin class providing metrics collection functionality for pipelines.

    Provides functionality for:
    - Collecting pipe outputs
    - Collecting pipe-specific metrics
    - Managing metrics lifecycle
    """

    def __init__(self) -> None:
        """Initialize metrics collection."""
        self._pipe_outputs: dict[Any, list[Any]] = {}

    def get_pipes(self) -> list[Any]:
        """Get list of pipes to collect metrics from.

        This method should be overridden by classes using this mixin.
        """
        if hasattr(self, "_pipes"):
            return cast(list[Any], self._pipes)
        if hasattr(self, "pipes"):
            return cast(list[Any], self.pipes())
        return []

    def get_pipe_outputs(self, pipe: Any) -> list[Any]:
        """Get outputs from a specific pipe.

        Args:
            pipe: The pipe to get outputs for

        Returns:
            List of outputs from the pipe
        """
        return self._pipe_outputs.get(pipe, [])

    def clear_metrics(self) -> None:
        """Clear collected metrics and pipe outputs."""
        for pipe in self._pipe_outputs:
            self._pipe_outputs[pipe].clear()

    @classmethod
    def _collect_pipe_metrics(cls, pipes: list[Any]) -> dict[str, Any]:
        """Collect metrics from all pipes that have metrics capability.

        Args:
            pipes: List of pipes to collect metrics from

        Returns:
            Dictionary mapping pipe names to their metrics
        """
        metrics: dict[str, Any] = {}
        for pipe in pipes:
            if hasattr(pipe, "name") and hasattr(pipe, "metrics") and pipe.name is not None:
                metrics[pipe.name] = pipe.metrics.get_metrics()
        return metrics

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics from all pipes in the pipeline.

        Returns
            Dictionary mapping pipe names to their metrics
        """
        return self._collect_pipe_metrics(self.get_pipes())
