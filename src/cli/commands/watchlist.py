"""Watchlist management commands."""

from datetime import date, timedelta
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.app import app
from src.cli.helpers.downloads import download_price_data
from src.cli.helpers.watchlist import run_watchlist_scan
from src.config import load_config
from src.data.db import init_db
from src.data.repository import (
    RecommendationsRepository,
    WatchlistRepository,
    WatchlistSignalRepository,
)
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@app.command()
def watchlist(
    add_ticker: str = typer.Option(
        None,
        "--add-ticker",
        "-a",
        help="Add ticker to watchlist (e.g., AAPL)",
    ),
    add_recommendation: int = typer.Option(
        None,
        "--add-recommendation",
        "-r",
        help="Add ticker by recommendation ID",
    ),
    remove_ticker: str = typer.Option(
        None,
        "--remove-ticker",
        "-d",
        help="Remove ticker from watchlist",
    ),
    list_all: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List all tickers in watchlist",
    ),
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Manage watchlist of tickers to monitor.

    Add tickers to watchlist either by ticker symbol or recommendation ID.
    Each ticker can only appear once in the watchlist.

    Examples:
        # Add ticker to watchlist
        watchlist --add-ticker AAPL

        # Add ticker by recommendation ID (uses first recommendation for that ticker)
        watchlist --add-recommendation 123

        # Remove ticker from watchlist
        watchlist --remove-ticker AAPL

        # List all watchlist tickers
        watchlist --list
    """
    try:
        # Load config
        config_obj = load_config(config)

        # Initialize database
        db_path = (
            config_obj.database.db_path if config_obj.database.enabled else "data/falconsignals.db"
        )
        init_db(db_path)

        # Create repository
        watchlist_repo = WatchlistRepository(db_path)

        # Handle operations
        if add_ticker:
            success, message = watchlist_repo.add_to_watchlist(add_ticker)
            if success:
                typer.echo(f"✅ {message}")
            else:
                typer.echo(f"❌ {message}", err=True)
                raise typer.Exit(code=1)

        elif add_recommendation:
            # Get recommendation and extract ticker
            rec_repo = RecommendationsRepository(db_path)
            rec = rec_repo.get_recommendation_by_id(add_recommendation)

            if not rec:
                typer.echo(f"❌ Recommendation {add_recommendation} not found", err=True)
                raise typer.Exit(code=1)

            ticker_symbol = rec.get("ticker")
            if not ticker_symbol:
                typer.echo("❌ No ticker symbol found for recommendation", err=True)
                raise typer.Exit(code=1)

            success, message = watchlist_repo.add_to_watchlist(
                ticker_symbol, recommendation_id=add_recommendation
            )

            if success:
                typer.echo(f"✅ {message}")
            else:
                typer.echo(f"❌ {message}", err=True)
                raise typer.Exit(code=1)

        elif remove_ticker:
            success, message = watchlist_repo.remove_from_watchlist(remove_ticker)
            if success:
                typer.echo(f"✅ {message}")
            else:
                typer.echo(f"❌ {message}", err=True)
                raise typer.Exit(code=1)

        elif list_all:
            watchlist_items = watchlist_repo.get_watchlist()

            if not watchlist_items:
                typer.echo("📝 Watchlist is empty")
                return

            # Create rich table
            table = Table(title="📝 Watchlist", show_header=True, header_style="bold cyan")
            table.add_column("Ticker", style="green", width=8)
            table.add_column("Company Name", style="white", width=40)
            table.add_column("Rec ID", justify="right", style="yellow", width=8)
            table.add_column("Added", style="blue", width=16)

            # Add rows
            for item in watchlist_items:
                ticker = item["ticker"]
                name = item["name"]
                rec_id = str(item["recommendation_id"]) if item["recommendation_id"] else "-"
                created = item["created_at"].strftime("%Y-%m-%d %H:%M")

                table.add_row(ticker, name, rec_id, created)

            # Print table
            console = Console()
            console.print(table)
            console.print(f"\nTotal: {len(watchlist_items)} ticker(s)\n", style="bold")

        else:
            typer.echo(
                "❌ Please specify an action: --add-ticker, --add-recommendation, --remove-ticker, or --list"
            )
            raise typer.Exit(code=1)

    except Exception as e:
        logger.error(f"Watchlist command error: {e}", exc_info=True)
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def watchlist_scan(
    ticker: str = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Comma-separated list of specific tickers to scan (e.g., AAPL,NVDA)",
    ),
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Run technical analysis on watchlist tickers.

    Performs technical analysis on all tickers in the watchlist (or specific tickers)
    and stores the results including technical score, confidence, rationale, and
    suggested action (Buy, Wait, Remove) in the watchlist_signals table.

    Examples:
        # Scan all watchlist tickers
        watchlist-scan

        # Scan specific tickers
        watchlist-scan --ticker AAPL,NVDA
    """
    try:
        # Load config
        config_obj = load_config(config)
        setup_logging(config_obj.logging)

        # Initialize database
        db_path = (
            config_obj.database.db_path if config_obj.database.enabled else "data/falconsignals.db"
        )
        init_db(db_path)

        # Create repositories
        watchlist_repo = WatchlistRepository(db_path)
        signal_repo = WatchlistSignalRepository(db_path)

        # Get tickers to scan
        if ticker:
            # Specific tickers provided
            ticker_list = [t.strip().upper() for t in ticker.split(",")]
            typer.echo(f"🔍 Scanning {len(ticker_list)} specified ticker(s)...")

            # Verify all tickers are in watchlist
            watchlist_items = watchlist_repo.get_watchlist()
            watchlist_symbols = {item["ticker"] for item in watchlist_items}

            for t in ticker_list:
                if t not in watchlist_symbols:
                    typer.echo(f"⚠️  Warning: {t} is not in watchlist, skipping", err=True)

            ticker_list = [t for t in ticker_list if t in watchlist_symbols]

            if not ticker_list:
                typer.echo("❌ No valid watchlist tickers to scan", err=True)
                raise typer.Exit(code=1)
        else:
            # Scan all watchlist tickers
            watchlist_items = watchlist_repo.get_watchlist()

            if not watchlist_items:
                typer.echo(
                    "📝 Watchlist is empty. Add tickers with 'watchlist --add-ticker <TICKER>'"
                )
                raise typer.Exit(code=0)

            ticker_list = [item["ticker"] for item in watchlist_items]
            typer.echo(f"🔍 Scanning {len(ticker_list)} watchlist ticker(s)...")

        # Download fresh price data before analysis (DRY - reuse helper)
        typer.echo("\n📥 Refreshing price data...")
        download_success, download_skipped, download_errors, _ = download_price_data(
            tickers=ticker_list,
            config_obj=config_obj,
            force_refresh=True,
            show_progress=True,
        )

        typer.echo(f"  ✓ Downloaded: {download_success}/{len(ticker_list)} tickers")
        if download_skipped > 0:
            typer.echo(f"  ⏭️  Skipped: {download_skipped} ticker(s)")
        if download_errors > 0:
            typer.echo(f"  ⚠️  Errors: {download_errors} ticker(s)")

        # Run AI-powered watchlist scan
        typer.echo("\n🤖 Running AI technical analysis...")
        success_count, error_count = run_watchlist_scan(
            ticker_list=ticker_list,
            config_obj=config_obj,
            watchlist_repo=watchlist_repo,
            signal_repo=signal_repo,
            typer_instance=typer,
        )

    except Exception as e:
        logger.error(f"Watchlist scan error: {e}", exc_info=True)
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def watchlist_report(
    ticker: str = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Filter by specific ticker(s), comma-separated (e.g., AAPL or AAPL,NVDA). Shows all tickers if not specified.",
    ),
    days: int = typer.Option(
        30,
        "--days",
        "-d",
        help="Number of days of history to show (default: 30)",
    ),
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Display historical watchlist signals report.

    Shows all signals from the watchlist_signals table with full details including
    complete rationale, trading levels, and analysis history. Results can be filtered
    by ticker and time period.

    Examples:
        # Show all recent signals
        watchlist-report

        # Show signals for specific ticker
        watchlist-report --ticker AAPL

        # Show signals for multiple tickers
        watchlist-report --ticker AAPL,NVDA,MSFT

        # Show last 90 days
        watchlist-report --days 90

        # Show specific tickers with extended history
        watchlist-report --ticker ADBE,CFLT --days 60
    """
    try:
        # Load config
        config_obj = load_config(config)
        setup_logging(config_obj.logging)

        # Initialize database
        db_path = (
            config_obj.database.db_path if config_obj.database.enabled else "data/falconsignals.db"
        )
        init_db(db_path)

        # Create repository
        signal_repo = WatchlistSignalRepository(db_path)

        # Fetch signals
        if ticker:
            # Parse comma-separated tickers
            ticker_list = [t.strip().upper() for t in ticker.split(",")]

            if len(ticker_list) == 1:
                typer.echo(f"📊 Watchlist Signals Report - {ticker_list[0]} (Last {days} days)\n")
            else:
                typer.echo(
                    f"📊 Watchlist Signals Report - {', '.join(ticker_list)} (Last {days} days)\n"
                )

            # Fetch signals for all specified tickers
            signals = []
            for ticker_symbol in ticker_list:
                ticker_signals = signal_repo.get_signal_history(ticker_symbol, days_back=days)
                signals.extend(ticker_signals)

            # Sort by date descending
            signals = sorted(signals, key=lambda x: x["analysis_date"], reverse=True)

            if not signals:
                if len(ticker_list) == 1:
                    typer.echo(f"📝 No signals found for {ticker_list[0]} in the last {days} days")
                else:
                    typer.echo(
                        f"📝 No signals found for any of the specified tickers in the last {days} days"
                    )
                raise typer.Exit(code=0)
        else:
            typer.echo(f"📊 Watchlist Signals Report - All Tickers (Last {days} days)\n")
            # Get all watchlist signals for all tickers
            signals = signal_repo.get_watchlist_with_latest_signals()

            if not signals:
                typer.echo("📝 No signals found in watchlist")
                raise typer.Exit(code=0)

            # For "all tickers" view, flatten and get recent signals
            all_signals = []
            cutoff_date = date.today() - timedelta(days=days)

            for entry in signals:
                if entry.get("latest_signal"):
                    sig = entry["latest_signal"]
                    if sig.get("analysis_date") >= cutoff_date:
                        sig["ticker"] = entry["ticker"]
                        sig["name"] = entry["name"]
                        all_signals.append(sig)

            signals = sorted(all_signals, key=lambda x: x["analysis_date"], reverse=True)

            if not signals:
                typer.echo(f"📝 No signals found in the last {days} days")
                raise typer.Exit(code=0)

        # Display results in detailed format
        console = Console()

        for i, signal in enumerate(signals, 1):
            # Create a panel for each signal
            ticker_symbol = signal.get("ticker", "N/A")
            signal_date = signal.get("analysis_date", "N/A")
            score = signal.get("score", 0)
            confidence = signal.get("confidence", 0)
            action = signal.get("action", "N/A")
            current_price = signal.get("current_price", 0)
            currency = signal.get("currency", "USD")
            rationale = signal.get("rationale", "No rationale provided")

            # Trading levels
            entry_price = signal.get("entry_price")
            stop_loss = signal.get("stop_loss")
            take_profit = signal.get("take_profit")
            wait_for_price = signal.get("wait_for_price")

            # Build content with full details
            content_lines = []
            content_lines.append(f"[bold cyan]Date:[/bold cyan] {signal_date}")
            content_lines.append(f"[bold yellow]Score:[/bold yellow] {score:.0f}/100")
            content_lines.append(f"[bold cyan]Confidence:[/bold cyan] {confidence:.0f}%")
            content_lines.append(f"[bold magenta]Action:[/bold magenta] {action}")
            content_lines.append(f"[bold white]Price:[/bold white] {currency} {current_price:.2f}")

            # Add trading levels if available
            if entry_price:
                content_lines.append(
                    f"[bold green]Entry Price:[/bold green] {currency} {entry_price:.2f}"
                )
            if stop_loss:
                content_lines.append(f"[bold red]Stop Loss:[/bold red] {currency} {stop_loss:.2f}")
            if take_profit:
                content_lines.append(
                    f"[bold green]Take Profit:[/bold green] {currency} {take_profit:.2f}"
                )
            if wait_for_price:
                content_lines.append(
                    f"[bold yellow]Wait For:[/bold yellow] {currency} {wait_for_price:.2f}"
                )

            content_lines.append("")
            content_lines.append("[bold]Rationale:[/bold]")
            content_lines.append(rationale)

            content = "\n".join(content_lines)

            # Color-code panel border by action
            border_style = "green" if action == "Buy" else "yellow" if action == "Wait" else "red"

            console.print(f"\n[bold]{i}. {ticker_symbol}[/bold]")
            console.print(Panel(content, border_style=border_style, expand=False))

        # Summary
        console.print(f"\n[bold green]Total signals:[/bold green] {len(signals)}")

        # Count by action
        action_counts = {}
        for sig in signals:
            action = sig.get("action", "Unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        if action_counts:
            console.print("\n[bold]By Action:[/bold]")
            for action, count in sorted(action_counts.items()):
                console.print(f"  {action}: {count}")

    except Exception as e:
        logger.error(f"Watchlist report error: {e}", exc_info=True)
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e
