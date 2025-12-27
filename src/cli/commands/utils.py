"""Utility commands for listing categories, portfolios, and strategies."""

import typer

from src.cli.app import app
from src.filtering.strategies import list_strategies as get_strategies
from src.MARKET_TICKERS import get_us_categories


@app.command()
def list_categories() -> None:
    """List all available US ticker categories.

    Shows all category names with the number of tickers in each.
    Use these category names with the `analyze --group` option.
    """
    categories = get_us_categories()

    typer.echo("\n🇺🇸 Available US Ticker Categories:\n")

    # Group by type for better readability
    groups = {
        "Market Cap": ["us_mega_cap", "us_large_cap", "us_mid_cap", "us_small_cap"],
        "Technology": [
            "us_tech",
            "us_tech_software",
            "us_tech_semiconductors",
            "us_tech_hardware",
            "us_tech_internet",
        ],
        "Healthcare": ["us_healthcare", "us_healthcare_pharma", "us_healthcare_devices"],
        "Financials": [
            "us_financials",
            "us_financials_banks",
            "us_financials_fintech",
            "us_financials_asset_mgmt",
        ],
        "Consumer": [
            "us_consumer",
            "us_consumer_retail",
            "us_consumer_food_bev",
            "us_consumer_restaurants",
        ],
        "Other Sectors": [
            "us_industrials",
            "us_energy",
            "us_clean_energy",
            "us_utilities",
            "us_real_estate",
            "us_materials",
            "us_communication",
            "us_transportation",
        ],
        "Themes": [
            "us_ai_ml",
            "us_cybersecurity",
            "us_cloud_computing",
            "us_space_defense",
            "us_ev_autonomous",
            "us_biotech_genomics",
            "us_quantum_computing",
        ],
        "ETFs": [
            "us_etfs",
            "us_etfs_broad_market",
            "us_etfs_sector",
            "us_etfs_fixed_income",
            "us_etfs_international",
            "us_etfs_thematic",
            "us_etfs_dividend",
        ],
    }

    for group_name, cat_list in groups.items():
        typer.echo(f"📌 {group_name}:")
        for cat in cat_list:
            if cat in categories:
                count = categories[cat]
                typer.echo(f"  • {cat}: {count} tickers")
        typer.echo()

    # Usage examples
    typer.echo("💡 Usage Examples:")
    typer.echo("  analyze --group us_tech_software")
    typer.echo("  analyze --group us_ai_ml,us_cybersecurity --limit 30")
    typer.echo("  analyze --market nordic --group us_tech_software")
    typer.echo()


@app.command()
def list_portfolios() -> None:
    """List all available diversified portfolio categories.

    Shows all pre-built portfolio categories with the number of tickers in each.
    Use these portfolio names with the `analyze --group` option.
    """
    categories = get_us_categories()

    # Filter for portfolio categories only
    portfolio_categories = {k: v for k, v in categories.items() if k.startswith("us_portfolio_")}

    typer.echo("\n💼 Available Diversified Portfolio Categories:\n")

    # Group by portfolio type for better readability
    groups = {
        "Balanced Portfolios": [
            "us_portfolio_balanced_conservative",
            "us_portfolio_balanced_moderate",
            "us_portfolio_balanced_aggressive",
        ],
        "Income Portfolios": [
            "us_portfolio_dividend_aristocrats",
            "us_portfolio_high_yield",
            "us_portfolio_dividend_growth",
        ],
        "Growth Portfolios": [
            "us_portfolio_tech_growth",
            "us_portfolio_next_gen_tech",
            "us_portfolio_disruptive",
        ],
        "Value Portfolios": [
            "us_portfolio_deep_value",
            "us_portfolio_garp",
            "us_portfolio_quality_value",
        ],
        "Economic Cycle": [
            "us_portfolio_expansion",
            "us_portfolio_contraction",
            "us_portfolio_inflation_hedge",
        ],
        "Thematic": [
            "us_portfolio_aging_population",
            "us_portfolio_millennial",
            "us_portfolio_infrastructure",
            "us_portfolio_reshoring",
            "us_portfolio_water",
        ],
        "International": [
            "us_portfolio_global_leaders",
            "us_portfolio_emerging_markets",
        ],
        "Risk Parity": [
            "us_portfolio_all_weather",
            "us_portfolio_permanent",
            "us_portfolio_golden_butterfly",
        ],
    }

    for group_name, portfolio_list in groups.items():
        typer.echo(f"📌 {group_name}:")
        for portfolio in portfolio_list:
            if portfolio in portfolio_categories:
                count = portfolio_categories[portfolio]
                typer.echo(f"  • {portfolio}: {count} tickers")
        typer.echo()

    # Summary
    total_portfolios = len(portfolio_categories)
    total_tickers = sum(portfolio_categories.values())
    typer.echo("📊 Summary:")
    typer.echo(f"  Total portfolios: {total_portfolios}")
    typer.echo(f"  Total tickers across all portfolios: {total_tickers}")
    typer.echo()

    # Usage examples
    typer.echo("💡 Usage Examples:")
    typer.echo("  analyze --group us_portfolio_balanced_conservative")
    typer.echo("  analyze --group us_portfolio_dividend_growth")
    typer.echo("  analyze --group us_portfolio_tech_growth --llm")
    typer.echo("  analyze --group us_portfolio_all_weather")
    typer.echo()


@app.command()
def list_strategies() -> None:
    """List all available filtering strategies with descriptions.

    Shows:
    - Strategy name (to use with --strategy flag)
    - Description of what the strategy detects
    - Suitable use cases

    Example:
        falconsignals list-strategies
    """

    typer.echo("\n📊 Available Filtering Strategies\n")
    typer.echo("=" * 80)

    strategies = get_strategies()

    for name, description in strategies:
        typer.echo(f"\n🔹 {name.upper()}")
        typer.echo(f"   {description}")

    typer.echo(f"\n{'=' * 80}")
    typer.echo(f"\nTotal strategies: {len(strategies)}")
    typer.echo("\nUsage: falconsignals analyze --strategy <strategy_name>")
    typer.echo("Example: falconsignals analyze --group us_tech_software --strategy momentum\n")
