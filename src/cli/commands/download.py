"""Download historical price data command."""

from pathlib import Path

import typer

from src.cli.app import app
from src.cli.helpers.downloads import download_price_data
from src.config import load_config
from src.MARKET_TICKERS import get_tickers_for_analysis, get_tickers_for_markets
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@app.command()
def download_prices(
    market: str = typer.Option(
        None,
        "--market",
        "-m",
        help="Market to download: 'global', 'us', 'eu', 'nordic', or comma-separated (e.g., 'us,eu')",
    ),
    group: str = typer.Option(
        None,
        "--group",
        "-g",
        help="Ticker group: sector categories or portfolios. Comma-separated for multiple.",
    ),
    ticker: str = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Comma-separated list of tickers to download (e.g., 'AAPL,MSFT,GOOGL')",
    ),
    limit: int = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of instruments to download per market",
    ),
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file (default: config/local.yaml or config/default.yaml)",
        exists=True,
    ),
    force_refresh: bool = typer.Option(
        False,
        "--force-refresh",
        help="Force re-download of all data (ignores existing cache)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be downloaded without actually downloading",
    ),
) -> None:
    """Download historical price data for tickers and store as CSV files.

    Fetches historical price data from configured providers and stores it
    in the cache directory as CSV files (one per ticker). Uses the lookback
    period defined in config (historical_data_lookback_days).

    Examples:
        # Download prices for specific tickers
        download-prices --ticker AAPL,MSFT,GOOGL

        # Download prices for a market
        download-prices --market us --limit 50

        # Download prices for a group
        download-prices --group us_tech_software

        # Download all markets with force refresh
        download-prices --market global --force-refresh

        # Dry run to see what would be downloaded
        download-prices --market nordic --dry-run
    """
    # Validate inputs
    if not market and not group and not ticker:
        typer.echo(
            "❌ Error: Either --market, --group, or --ticker must be provided\n"
            "Examples:\n"
            "  download-prices --market us\n"
            "  download-prices --group us_tech_software\n"
            "  download-prices --ticker AAPL,MSFT,GOOGL",
            err=True,
        )
        raise typer.Exit(code=1)

    if (market or group) and ticker:
        typer.echo("❌ Error: Cannot specify --ticker with --market or --group", err=True)
        raise typer.Exit(code=1)

    try:
        # Load configuration
        config_obj = load_config(config)

        # Setup logging
        setup_logging(config_obj.logging)

        typer.echo("📥 Historical Price Data Downloader")
        typer.echo(f"  Provider: {config_obj.data.primary_provider}")
        typer.echo(f"  Lookback period: {config_obj.analysis.historical_data_lookback_days} days")

        # Determine tickers to download
        if ticker:
            tickers = [t.strip().upper() for t in ticker.split(",")]
            typer.echo(f"  Mode: Specific tickers ({len(tickers)} specified)")
        elif group:
            groups = [g.strip() for g in group.split(",")]
            typer.echo(f"  Mode: Group analysis ({', '.join(groups)})")
            tickers = get_tickers_for_analysis(
                markets=None, categories=groups, limit_per_category=limit
            )
        else:
            markets_list = [m.strip().lower() for m in market.split(",")]
            typer.echo(f"  Mode: Market analysis ({', '.join(markets_list)})")
            tickers = get_tickers_for_markets(markets_list, limit=limit)

        typer.echo(f"  Tickers to process: {len(tickers)}")

        if dry_run:
            typer.echo("\n🔍 DRY RUN MODE - No data will be downloaded")
            typer.echo(f"\nTickers that would be processed ({len(tickers)}):")
            for i, t in enumerate(tickers[:20], 1):
                typer.echo(f"  {i}. {t}")
            if len(tickers) > 20:
                typer.echo(f"  ... and {len(tickers) - 20} more")
            return

        # Use period parameter for display
        period = f"{config_obj.analysis.historical_data_lookback_days}d"
        typer.echo(f"  Period: {period}")
        if force_refresh:
            typer.echo("  Force refresh: enabled (will re-download all data)")
        typer.echo()

        # Download prices using DRY helper
        success_count, skipped_count, error_count, prices_dir = download_price_data(
            tickers=tickers,
            config_obj=config_obj,
            force_refresh=force_refresh,
            show_progress=True,
        )

        # Summary
        typer.echo("\n✅ Download Summary:")
        typer.echo(f"  Successfully downloaded: {success_count}")
        typer.echo(f"  Skipped (already current): {skipped_count}")
        typer.echo(f"  Errors: {error_count}")
        typer.echo(f"  Total processed: {success_count + skipped_count + error_count}")

        # Show storage location
        typer.echo(f"\n💾 Data stored in: {prices_dir}")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        typer.echo(f"❌ Configuration error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        logger.exception(f"Unexpected error during download: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e
