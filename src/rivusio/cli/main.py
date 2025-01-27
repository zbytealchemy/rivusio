"""Command line interface for rivusio."""
import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Any, Optional, Union, cast

import click
from rich.console import Console

from rivusio import AsyncBasePipe, AsyncStream, StreamConfig, SyncBasePipe

console = Console()

PathType = Annotated[str, click.Path(exists=True)]
OptionalPathType = Annotated[str, click.Path()]

@click.group()
def cli() -> None:
    """Rivusio CLI."""


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option(
    "--input-file",
    "-i",
    type=click.Path(exists=True),
    required=True,
    help="Input file to process",
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(),
    required=True,
    help="Output file to write results to",
)
@click.option("--batch-size", "-b", type=int, default=None, help="Batch size for processing")
@click.option("--window-size", "-w", type=float, default=None, help="Window size in seconds")
def run(
    config_file: PathType,
    input_file: PathType,
    output_file: OptionalPathType,
    batch_size: Optional[int],
    window_size: Optional[float],
) -> None:
    """Run a pipeline from a configuration file."""
    try:
        config = json.loads(Path(config_file).read_text())

        batch_size = batch_size if batch_size else 1
        stream_config_args = {
            "batch_size": batch_size,
            **config.get("stream_config", {}),
        }

        if window_size is not None:
            stream_config_args["window_size"] = timedelta(seconds=window_size)

        stream_config = StreamConfig(**stream_config_args)

        pipe_class = _import_class(config["pipe_class"])

        # Type checks
        if not issubclass(pipe_class, AsyncBasePipe):
            raise click.BadParameter("Only async pipes are supported in the CLI")

        pipe = pipe_class()
        asyncio.run(_process_data(pipe, input_file, output_file, stream_config))

        console.print("[green]Pipeline completed successfully![/green]")

    except Exception as e:
        console.print(f"[red]Error running pipeline: {e!s}[/red]")
        raise click.Abort from e


@cli.command()
def list_pipes() -> None:
    """List available pipes."""
    try:
        click.echo("Available pipes:")
        click.echo("  Async pipes:")
        for pipe in AsyncBasePipe.__subclasses__():
            click.echo(f"    - {pipe.__name__}")
        click.echo("  Sync pipes:")
        for pipe in SyncBasePipe.__subclasses__():  # type: ignore[assignment]
            click.echo(f"    - {pipe.__name__}")

    except Exception as e:
        console.print(f"[red]Error listing pipes: {e!s}[/red]")
        raise click.Abort from e


@cli.command()
@click.argument("pipe_name", type=str)
def info(pipe_name: str) -> None:
    """Show detailed information about a pipe."""
    try:
        pipe_class = _find_pipe(pipe_name)
        if not pipe_class:
            raise click.BadParameter(f"Pipe '{pipe_name}' not found")

        info = _get_pipe_info(pipe_class)

        console.print(f"\n[cyan]Pipe: {info['name']}[/cyan]")
        console.print(f"[green]Module:[/green] {info['module']}")
        console.print(f"\n{info.get('description', '')}")

        if info.get("config_fields"):
            console.print("\n[yellow]Configuration Fields:[/yellow]")
            for field, details in info["config_fields"].items():
                console.print(f"  {field}: {details['type']}")
                if details.get("description"):
                    console.print(f"    {details['description']}")

    except Exception as e:
        console.print(f"[red]Error getting pipe info: {e!s}[/red]")
        raise click.Abort from e


async def _process_data(
    pipe: AsyncBasePipe, input_file: str, output_file: str, config: StreamConfig,
) -> None:
    """Process data through a pipe."""

    async def data_source() -> AsyncGenerator[dict[str, Any], None]:
        input_path = Path(input_file)
        with input_path.open("r") as f:
            for line in f:
                yield json.loads(line)

    stream = AsyncStream(data_source(), config=config)

    output_path = Path(output_file)
    with output_path.open("w") as f:
        async for result in stream.process(pipe):
            f.write(json.dumps(result) + "\n")


def _import_class(class_path: str) -> type[Union[AsyncBasePipe[Any, Any], SyncBasePipe[Any, Any]]]:
    """Import a class from a string path."""
    try:
        module_path, class_name = class_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        cls = cast(
            type[Union[AsyncBasePipe[Any, Any], SyncBasePipe[Any, Any]]],
            getattr(module, class_name),
        )
        if not issubclass(cls, AsyncBasePipe | SyncBasePipe):
            raise TypeError(f"Class {class_name} is not a valid pipe class") from None
        return cls
    except (TypeError, AttributeError) as e:
        raise click.BadParameter(f"Could not import pipe class: {e!s}") from e


def _find_pipe(name: str) -> Optional[type[Union[AsyncBasePipe[Any, Any], SyncBasePipe[Any, Any]]]]:
    """Find a pipe class by name."""
    # This is a placeholder. In a real implementation,
    # we would look up the pipe class by name.
    return None


def _get_pipe_info(
    pipe_class: type[Union[AsyncBasePipe[Any, Any], SyncBasePipe[Any, Any]]],
) -> dict[str, Any]:
    """Get information about a pipe class."""
    return {
        "name": pipe_class.__name__,
        "module": pipe_class.__module__,
        "description": pipe_class.__doc__,
        "config_fields": {},  # Would be populated from class inspection
    }


if __name__ == "__main__":
    cli()
