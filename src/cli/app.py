"""FalconSignals CLI application setup."""

import typer

app = typer.Typer(
    name="falconsignals",
    help="AI-powered financial analysis and investment recommendation system",
    no_args_is_help=True,
)


@app.callback()
def version_callback(
    version: bool = typer.Option(None, "--version", "-v", help="Show version and exit"),
) -> None:
    """Show version information."""
    if version:
        typer.echo("FalconSignals v0.1.0")
        raise typer.Exit()
