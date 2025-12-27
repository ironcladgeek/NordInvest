"""Download helper functions for CLI commands."""

import time
from datetime import datetime
from pathlib import Path

import typer

from src.data.price_manager import PriceDataManager
from src.data.provider_manager import ProviderManager
from src.utils.logging import get_logger
from src.utils.resilience import RateLimiter

logger = get_logger(__name__)


def download_price_data(
    tickers: list[str],
    config_obj,
    force_refresh: bool = False,
    show_progress: bool = True,
) -> tuple[int, int, int, Path]:
    """Download historical price data for tickers.

    Args:
        tickers: List of ticker symbols to download
        config_obj: Configuration object
        force_refresh: Force re-download even if data exists
        show_progress: Show progress bar (set False for silent mode)

    Returns:
        Tuple of (success_count, skipped_count, error_count, prices_dir)
    """
    # Initialize components
    data_dir = Path("data")
    price_manager = PriceDataManager(prices_dir=data_dir / "cache" / "prices")
    provider_manager = ProviderManager(
        primary_provider=config_obj.data.primary_provider,
        backup_providers=config_obj.data.backup_providers,
        db_path=config_obj.database.db_path if config_obj.database.enabled else None,
        historical_data_lookback_days=config_obj.analysis.historical_data_lookback_days,
    )

    # Initialize rate limiter (conservative: 5 requests per second)
    rate_limiter = RateLimiter(rate=5, period=1.0)

    # Use period parameter for fetching
    period = f"{config_obj.analysis.historical_data_lookback_days}d"

    # Download prices
    success_count = 0
    skipped_count = 0
    error_count = 0

    if show_progress:
        with typer.progressbar(
            tickers, label="Downloading prices", show_pos=True, show_percent=True
        ) as progress:
            for ticker in progress:
                try:
                    # Check if we need to download
                    if not force_refresh and price_manager.has_data(ticker):
                        # Check if data is relatively current (within last 2 days)
                        _, existing_end = price_manager.get_data_range(ticker)
                        if existing_end and (datetime.now().date() - existing_end).days <= 2:
                            logger.debug(f"Skipping {ticker} - data is current")
                            skipped_count += 1
                            continue

                    # Wait for rate limiter
                    rate_limiter.wait_if_needed(tokens=1)

                    # Fetch prices using provider manager with period parameter
                    prices = provider_manager.get_stock_prices(ticker, period=period)

                    if prices:
                        # Store to CSV
                        stored = price_manager.store_prices(
                            ticker,
                            [p.model_dump() for p in prices],
                            append=not force_refresh,
                        )
                        if stored > 0:
                            success_count += 1
                            logger.debug(f"Downloaded {len(prices)} prices for {ticker}")
                    else:
                        logger.warning(f"No price data received for {ticker}")
                        error_count += 1

                except KeyboardInterrupt:
                    typer.echo("\n\n⚠️  Download interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"Error downloading {ticker}: {e}")
                    error_count += 1
                    # Small delay on error to avoid hammering the API
                    time.sleep(0.5)
    else:
        for ticker in tickers:
            try:
                # Check if we need to download
                if not force_refresh and price_manager.has_data(ticker):
                    # Check if data is relatively current (within last 2 days)
                    _, existing_end = price_manager.get_data_range(ticker)
                    if existing_end and (datetime.now().date() - existing_end).days <= 2:
                        logger.debug(f"Skipping {ticker} - data is current")
                        skipped_count += 1
                        continue

                # Wait for rate limiter
                rate_limiter.wait_if_needed(tokens=1)

                # Fetch prices using provider manager with period parameter
                prices = provider_manager.get_stock_prices(ticker, period=period)

                if prices:
                    # Store to CSV
                    stored = price_manager.store_prices(
                        ticker,
                        [p.model_dump() for p in prices],
                        append=not force_refresh,
                    )
                    if stored > 0:
                        success_count += 1
                        logger.debug(f"Downloaded {len(prices)} prices for {ticker}")
                else:
                    logger.warning(f"No price data received for {ticker}")
                    error_count += 1

            except KeyboardInterrupt:
                typer.echo("\n\n⚠️  Download interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error downloading {ticker}: {e}")
                error_count += 1
                # Small delay on error to avoid hammering the API
                time.sleep(0.5)

    return success_count, skipped_count, error_count, price_manager.prices_dir
