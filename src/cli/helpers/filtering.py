"""Filtering helper functions for CLI commands."""

from src.filtering import FilterOrchestrator
from src.utils.logging import get_logger

logger = get_logger(__name__)


def filter_tickers(
    tickers: list[str],
    strategy: str,
    config_obj,
    typer_instance,
    force_full_analysis: bool = False,
    historical_date=None,
    test_mode_config=None,
) -> tuple[list[str], dict]:
    """Filter tickers using specified strategy before analysis.

    Unified filtering path for both LLM and rule-based analysis modes.
    Implements DRY principle by having a single filtering logic.

    Args:
        tickers: List of tickers to filter
        strategy: Filtering strategy name ('anomaly', 'volume', 'all')
        config_obj: Configuration object
        typer_instance: Typer instance for output
        force_full_analysis: If True, use 'all' strategy regardless of specified strategy
        historical_date: Optional date for historical analysis
        test_mode_config: Optional test mode configuration

    Returns:
        Tuple of (filtered_tickers, filter_result)
        - filtered_tickers: List of tickers that passed the filter
        - filter_result: Full filter result dictionary with details

    Raises:
        RuntimeError: If filtering fails or no tickers pass filter (unless force_full_analysis)
    """
    try:
        # Override strategy if force_full_analysis is enabled
        if force_full_analysis:
            strategy = "all"
            typer_instance.echo(
                "  ⚠️  --force-full-analysis enabled: using 'all' strategy (no filtering)"
            )

        typer_instance.echo(f"🔍 Filtering tickers using '{strategy}' strategy...")

        # Get lookback days from config
        lookback_days = 730
        if hasattr(config_obj, "analysis") and hasattr(
            config_obj.analysis, "historical_data_lookback_days"
        ):
            lookback_days = config_obj.analysis.historical_data_lookback_days

        # Get strategy config if available (convert Pydantic model to dict)
        strategy_config = None
        if hasattr(config_obj, "filtering") and hasattr(config_obj.filtering, "strategies"):
            strategy_cfg = getattr(config_obj.filtering.strategies, strategy, None)
            if strategy_cfg:
                # Convert Pydantic model to dict for strategy initialization
                strategy_config = (
                    strategy_cfg.model_dump()
                    if hasattr(strategy_cfg, "model_dump")
                    else dict(strategy_cfg)
                )

        # Setup provider for price fetching
        provider_name = None
        fixture_path = None
        if test_mode_config and test_mode_config.enabled:
            provider_name = "fixture"
            fixture_path = test_mode_config.fixture_path
        else:
            provider_name = config_obj.data.primary_provider

        # Create orchestrator
        orchestrator = FilterOrchestrator(
            strategy=strategy,
            provider_name=provider_name,
            fixture_path=fixture_path,
            config=config_obj,
            strategy_config=strategy_config,
        )

        # Execute filtering
        filter_result = orchestrator.filter_tickers(
            tickers=tickers,
            historical_date=historical_date,
            lookback_days=lookback_days,
            show_progress=True,
        )

        if filter_result.get("status") != "success":
            error_msg = filter_result.get("message", "Unknown error")
            logger.error(f"Filtering failed: {error_msg}")
            raise RuntimeError(
                f"Filtering failed: {error_msg}\n"
                "Unable to proceed with analysis.\n"
                "Check logs for details."
            )

        filtered_tickers = filter_result.get("filtered_tickers", [])

        if not filtered_tickers and strategy != "all":
            logger.warning(f"No tickers passed '{strategy}' filter")
            if not force_full_analysis:
                raise RuntimeError(
                    f"No tickers passed the '{strategy}' filter.\n"
                    "To analyze all tickers anyway (higher cost), "
                    "use --force-full-analysis flag or --strategy all.\n"
                    f"Example: analyze --group us_mega_cap --strategy {strategy} --force-full-analysis"
                )

        total_scanned = filter_result.get("total_scanned", len(tickers))
        total_filtered = filter_result.get("total_filtered", len(filtered_tickers))

        if total_filtered < total_scanned:
            reduction_pct = 100 * (1 - total_filtered / total_scanned)
            typer_instance.echo(
                f"  ✓ Filtering complete: {total_filtered}/{total_scanned} tickers selected "
                f"({reduction_pct:.0f}% reduction)"
            )
        else:
            typer_instance.echo(f"  ✓ All {total_filtered} tickers selected")

        return filtered_tickers, filter_result

    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Error during filtering: {e}", exc_info=True)
        raise RuntimeError(
            f"Filtering error: {str(e)}\nUnable to proceed with analysis.\nCheck logs for details."
        ) from e
