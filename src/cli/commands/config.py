"""Configuration management commands."""

from pathlib import Path

import typer

from src.cli.app import app
from src.config import load_config
from src.utils.logging import get_logger

logger = get_logger(__name__)


@app.command()
def config_init(
    output: Path = typer.Option(  # noqa: B008
        Path("config/local.yaml"),
        "--output",
        "-o",
        help="Output path for local configuration file",
    ),
) -> None:
    """Initialize local configuration from template.

    Creates a local.yaml file based on the default.yaml template
    that you can customize for your preferences.
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        default_config = project_root / "config" / "default.yaml"

        if not default_config.exists():
            typer.echo(f"❌ Default config not found: {default_config}", err=True)
            raise typer.Exit(code=1)

        # Read default config
        with open(default_config, "r") as f:
            default_content = f.read()

        # Create output directory
        output.parent.mkdir(parents=True, exist_ok=True)

        # Write local config
        with open(output, "w") as f:
            f.write(default_content)

        logger.debug(f"Local configuration initialized: {output}")
        typer.echo(f"✓ Configuration template created: {output}")
        typer.echo("  Please edit this file with your preferences")

    except Exception as e:
        logger.exception(f"Error initializing configuration: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def validate_config(
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Validate configuration file.

    Loads and validates the configuration without running analysis,
    useful for checking configuration before deployment.
    """
    try:
        config_obj = load_config(config)

        typer.echo("✓ Configuration is valid")
        typer.echo(f"  Risk tolerance: {config_obj.risk.tolerance}")
        typer.echo(f"  Capital: €{config_obj.capital.starting_capital_eur:,.2f}")
        typer.echo(f"  Markets: {', '.join(config_obj.markets.included)}")
        typer.echo(f"  Instruments: {', '.join(config_obj.markets.included_instruments)}")
        typer.echo(f"  Buy threshold: {config_obj.analysis.buy_threshold}")
        typer.echo(f"  Cost limit: €{config_obj.deployment.cost_limit_eur_per_month:.2f}/month")

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        typer.echo(f"❌ Configuration error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        logger.exception(f"Unexpected error validating configuration: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e
