"""Metrics collection functionality for pipelines."""
from typing import Any, cast


class PipelineMetricsMixin:
    """Mixin class providing metrics collection functionality for pipelines."""

    def get_pipes(self) -> list[Any]:
        """Get list of pipes to collect metrics from.

        This method should be overridden by classes using this mixin.
        """
        if hasattr(self, "_pipes"):
            return cast(list[Any], self._pipes)
        if hasattr(self, "pipes"):
            return cast(list[Any], self.pipes())
        return []

    def _collect_pipe_metrics(self, pipes: list[Any]) -> dict[str, Any]:
        """Collect metrics from all pipes that have metrics capability.

        Args:
        ----
            pipes: List of pipes to collect metrics from

        Returns:
        -------
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
        -------
            Dictionary mapping pipe names to their metrics

        """
        return self._collect_pipe_metrics(self.get_pipes())
