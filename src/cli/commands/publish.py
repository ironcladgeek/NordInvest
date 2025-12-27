"""Website publishing command."""

import subprocess
from datetime import datetime
from pathlib import Path

import typer

from src.cli.app import app
from src.config import load_config
from src.data.db import init_db
from src.data.repository import RecommendationsRepository
from src.utils.logging import get_logger, setup_logging
from src.website.generator import WebsiteGenerator

logger = get_logger(__name__)


@app.command()
def publish(
    session_id: int | None = typer.Option(
        None, "--session-id", help="Publish report from run session ID"
    ),
    date: str | None = typer.Option(
        None, "--date", help="Publish report for specific date (YYYY-MM-DD)"
    ),
    ticker: str | None = typer.Option(
        None, "--ticker", help="Publish only for specific ticker symbol"
    ),
    analysis_mode: str | None = typer.Option(
        None,
        "--analysis-mode",
        help="Filter by analysis mode: 'llm' or 'rule_based'",
    ),
    signal_type: str | None = typer.Option(
        None,
        "--signal-type",
        help=(
            "Filter by signal type: 'strong_buy', 'buy', 'hold_bullish', 'hold', 'hold_bearish', "
            "'sell', 'strong_sell'"
        ),
    ),
    confidence_threshold: float | None = typer.Option(
        None,
        "--confidence-threshold",
        help="Minimum confidence score (e.g., 70 means confidence > 70)",
    ),
    final_score_threshold: float | None = typer.Option(
        None,
        "--final-score-threshold",
        help="Minimum final score (e.g., 70 means final_score > 70)",
    ),
    build_only: bool = typer.Option(
        False, "--build-only", help="Only build site, don't deploy to GitHub Pages"
    ),
    no_build: bool = typer.Option(
        False, "--no-build", help="Skip MkDocs build step (for testing content generation)"
    ),
    config: str = typer.Option(
        "config/local.yaml",
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Publish analysis results to static website.

    Generate website content from database signals and optionally build/deploy
    to GitHub Pages. Similar to report command but outputs to website format.

    Examples:

        # Publish from specific session and deploy
        publish --session-id 123

        # Publish all signals from a date
        publish --date 2025-12-10

        # Publish only one ticker
        publish --ticker NVDA --date 2025-12-10

        # Filter by analysis mode
        publish --date 2025-12-10 --analysis-mode llm

        # Filter by signal type
        publish --date 2025-12-10 --signal-type strong_buy

        # Filter by confidence threshold
        publish --date 2025-12-10 --confidence-threshold 80

        # Combine multiple filters
        publish --date 2025-12-10 --analysis-mode llm --confidence-threshold 80 --signal-type buy

        # Generate content without building site
        publish --session-id 123 --no-build

        # Build site but don't deploy to GitHub Pages
        publish --session-id 123 --build-only
    """
    try:
        # Validate inputs
        if not session_id and not date and not ticker:
            typer.echo("❌ Error: Must specify --session-id, --date, or --ticker", err=True)
            typer.echo("Examples:", err=True)
            typer.echo("  publish --session-id 123", err=True)
            typer.echo("  publish --date 2025-12-10", err=True)
            typer.echo("  publish --ticker NVDA --date 2025-12-10", err=True)
            raise typer.Exit(code=1)

        # Validate date format if provided
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError as e:
                typer.echo(f"❌ Error: Invalid date format '{date}'. Use YYYY-MM-DD", err=True)
                raise typer.Exit(code=1) from e

        # Load configuration
        config_obj = load_config(config)
        setup_logging(config_obj.logging)

        # Check if database is enabled
        if not config_obj.database.enabled:
            typer.echo(
                "❌ Error: Database is not enabled in configuration.\n"
                "   Enable database in config file to use website publishing.",
                err=True,
            )
            raise typer.Exit(code=1)

        # Initialize database
        init_db(config_obj.database.db_path)
        logger.debug(f"Database initialized at {config_obj.database.db_path}")

        typer.echo("🌐 Publishing to website...")
        if session_id:
            typer.echo(f"  Session ID: {session_id}")
        if date:
            typer.echo(f"  Date: {date}")
        if ticker:
            typer.echo(f"  Ticker: {ticker}")

        # Display active filters
        filters_applied = []
        if analysis_mode:
            filters_applied.append(f"analysis_mode={analysis_mode}")
        if signal_type:
            filters_applied.append(f"signal_type={signal_type}")
        if confidence_threshold is not None:
            filters_applied.append(f"confidence>{confidence_threshold}")
        if final_score_threshold is not None:
            filters_applied.append(f"final_score>{final_score_threshold}")

        if filters_applied:
            typer.echo(f"  Filters: {', '.join(filters_applied)}")

        # Initialize generator
        website_dir = Path("website/docs")
        generator = WebsiteGenerator(
            config=config_obj,
            db_path=config_obj.database.db_path,
            output_dir=str(website_dir),
        )

        # Load signals from database
        repo = RecommendationsRepository(config_obj.database.db_path)

        if ticker:
            # Load signals for specific ticker
            signals_data = repo.get_recommendations_by_ticker(ticker)
            if not signals_data:
                typer.echo(f"❌ No signals found for ticker: {ticker}", err=True)
                raise typer.Exit(code=1)

            # Generate ticker page
            typer.echo(f"  Generating page for {ticker}...")
            ticker_path = generator.generate_ticker_page(ticker)
            typer.echo(f"  ✓ Created: {ticker_path}")

        elif session_id or date:
            # Load signals by session or date with filters
            if session_id:
                signals = repo.get_recommendations_by_session(
                    run_session_id=session_id,
                    analysis_mode=analysis_mode,
                    signal_type=signal_type,
                    confidence_threshold=confidence_threshold,
                    final_score_threshold=final_score_threshold,
                )
            elif date:  # Type guard for pyright
                signals = repo.get_recommendations_by_date(
                    report_date=date,
                    analysis_mode=analysis_mode,
                    signal_type=signal_type,
                    confidence_threshold=confidence_threshold,
                    final_score_threshold=final_score_threshold,
                )
            else:
                signals = []

            if not signals:
                filters_desc = "matching the specified filters" if filters_applied else ""
                session_or_date = (
                    f"session {session_id}" if session_id else f"date {date or 'unknown'}"
                )
                typer.echo(
                    f"❌ No signals found for {session_or_date} {filters_desc}",
                    err=True,
                )
                raise typer.Exit(code=1)

            typer.echo(f"  Loaded {len(signals)} signal(s) from database")

            # Signals are already InvestmentSignal objects from repository
            signal_objects = signals

            # Generate report page
            report_date_str = date if date else signal_objects[0].analysis_date
            typer.echo(f"  Generating report page for {report_date_str}...")

            metadata = {
                "session_id": session_id,
                "total_signals": len(signal_objects),
            }

            report_path = generator.generate_report_page(
                signals=signal_objects,
                report_date=report_date_str,
                metadata=metadata,
            )
            typer.echo(f"  ✓ Created: {report_path}")

            # Generate ticker pages for all tickers in the report
            typer.echo("  Generating ticker pages...")
            unique_tickers = list(set(s.ticker for s in signal_objects))
            for t in unique_tickers:
                try:
                    ticker_path = generator.generate_ticker_page(t)
                    typer.echo(f"    ✓ {t}: {ticker_path}")
                except Exception as e:
                    logger.warning(f"Failed to generate page for {t}: {e}")
                    typer.echo(f"    ⚠️  {t}: {e}")

        # Generate tag pages
        typer.echo("  Generating tag pages...")
        try:
            tag_pages = generator.generate_tag_pages()
            typer.echo(f"  ✓ Generated {len(tag_pages)} tag pages")
        except Exception as e:
            logger.warning(f"Failed to generate tag pages: {e}")
            typer.echo(f"  ⚠️  Tag generation failed: {e}")

        # Generate index page
        typer.echo("  Generating index page...")
        index_path = generator.generate_index_page()
        typer.echo(f"  ✓ Created: {index_path}")

        # Update navigation
        typer.echo("  Updating navigation...")
        generator.update_navigation()
        typer.echo("  ✓ Navigation updated")

        typer.echo(f"\n✓ Content generated successfully in {website_dir}")

        # Build site with MkDocs if requested
        if not no_build:
            typer.echo("\n🔨 Building site with MkDocs...")

            website_root = Path("website")
            result = subprocess.run(
                ["mkdocs", "build", "--clean"],
                cwd=str(website_root),
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                typer.echo(f"❌ MkDocs build failed:\n{result.stderr}", err=True)
                raise typer.Exit(code=1)

            typer.echo("✓ Site built successfully")

            # Deploy to GitHub Pages if not build-only
            if not build_only:
                typer.echo("\n🚀 Deploying to GitHub Pages...")
                result = subprocess.run(
                    ["mkdocs", "gh-deploy", "--force"],
                    cwd=str(website_root),
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    typer.echo(f"❌ Deployment failed:\n{result.stderr}", err=True)
                    raise typer.Exit(code=1)

                typer.echo("✓ Deployed to GitHub Pages")
                typer.echo("\n🌐 Your site should be available at:")
                typer.echo("   https://ironcladgeek.github.io/FalconSignals/")
            else:
                typer.echo("\n✓ Build complete (deployment skipped)")
        else:
            typer.echo("\n✓ Content generation complete (build skipped)")

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Error publishing website: {e}", exc_info=True)
        typer.echo(f"\n❌ Error publishing website: {e}", err=True)
        raise typer.Exit(code=1) from e
