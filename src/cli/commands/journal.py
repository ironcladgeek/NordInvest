"""Trading journal management command."""

from datetime import date, datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.cli.app import app
from src.config import load_config
from src.data.db import init_db
from src.data.provider_manager import ProviderManager
from src.data.repository import TradingJournalRepository
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@app.command()
def journal(
    action: str = typer.Option(
        None,
        "--action",
        "-a",
        help="Action to perform: add, update, close, list, view, performance",
    ),
    config: Path = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Manage trading journal entries interactively.

    Add, update, close, list, or view trades with interactive prompts.

    Examples:
        # Add a new trade (interactive)
        journal --action add

        # Update an open trade
        journal --action update

        # Close a trade
        journal --action close

        # List open trades
        journal --action list

        # View trade details
        journal --action view

        # View performance statistics
        journal --action performance
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
        journal_repo = TradingJournalRepository(db_path)

        # If no action specified, prompt for it
        if not action:
            typer.echo("\n📒 Trading Journal\n")
            typer.echo("Available actions:")
            typer.echo("  add         - Add a new trade")
            typer.echo("  update      - Update an open trade")
            typer.echo("  close       - Close an open trade")
            typer.echo("  list        - List trades")
            typer.echo("  view        - View trade details")
            typer.echo("  performance - View performance statistics")
            typer.echo()
            action = typer.prompt("Select action")

        action = action.lower()

        if action == "add":
            typer.echo("\n➕ Add New Trade\n")

            # Get ticker
            ticker = typer.prompt("Ticker symbol").strip().upper()

            # Get entry date
            entry_date_str = typer.prompt(
                "Entry date (YYYY-MM-DD, or press Enter for today)",
                default=date.today().strftime("%Y-%m-%d"),
            )
            try:
                entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
            except ValueError:
                typer.echo("❌ Invalid date format", err=True)
                raise typer.Exit(code=1) from None

            # Get position type
            while True:
                position_type = typer.prompt("Position type (long/short)").strip().lower()
                if position_type in ["long", "short"]:
                    break
                typer.echo("❌ Invalid position type. Please enter 'long' or 'short'.")

            # Get entry price
            entry_price = typer.prompt("Entry price", type=float)

            # Get currency (optional)
            currency = typer.prompt("Currency (optional)", default="USD").strip().upper()

            # Get position size
            position_size = typer.prompt("Position size (number of shares)", type=float)

            # Get fees (optional)
            fees_entry = typer.prompt("Entry fees", type=float, default=0.0)

            # Get stop loss (optional)
            stop_loss_str = typer.prompt("Stop loss (optional, press Enter to skip)", default="")
            stop_loss = float(stop_loss_str) if stop_loss_str else None

            # Get take profit (optional)
            take_profit_str = typer.prompt(
                "Take profit (optional, press Enter to skip)", default=""
            )
            take_profit = float(take_profit_str) if take_profit_str else None

            # Get description (optional)
            description = typer.prompt("Description (optional, press Enter to skip)", default="")
            description = description if description else None

            # Get recommendation ID (optional)
            recommendation_id_str = typer.prompt(
                "Recommendation ID (optional, press Enter to skip)", default=""
            )
            recommendation_id = int(recommendation_id_str) if recommendation_id_str else None

            # Create trade
            success, message, trade_id = journal_repo.create_trade(
                ticker_symbol=ticker,
                entry_date=entry_date,
                entry_price=entry_price,
                position_size=position_size,
                position_type=position_type,
                fees_entry=fees_entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                description=description,
                recommendation_id=recommendation_id,
                currency=currency,
            )

            if success:
                typer.echo(f"\n✅ {message}")
                typer.echo(f"   Trade ID: {trade_id}")
                total_amount = (entry_price * position_size) + fees_entry
                typer.echo(f"   Total amount: ${total_amount:,.2f}")
            else:
                typer.echo(f"\n❌ Error: {message}", err=True)
                raise typer.Exit(code=1)

        elif action == "update":
            typer.echo("\n✏️  Update Trade\n")

            # Get trade ID
            trade_id = typer.prompt("Trade ID to update", type=int)

            # Get current trade details
            trade = journal_repo.get_trade_by_id(trade_id)
            if not trade:
                typer.echo(f"❌ Trade {trade_id} not found", err=True)
                raise typer.Exit(code=1)

            if trade["status"] != "open":
                typer.echo(f"❌ Trade {trade_id} is closed and cannot be updated", err=True)
                raise typer.Exit(code=1)

            typer.echo(f"\nCurrent values for {trade['ticker_symbol']}:")
            typer.echo(f"  Stop loss: {trade['stop_loss']}")
            typer.echo(f"  Take profit: {trade['take_profit']}")
            typer.echo(f"  Description: {trade['description']}")
            typer.echo()

            # Get new values (optional)
            stop_loss_str = typer.prompt("New stop loss (press Enter to keep current)", default="")
            stop_loss = float(stop_loss_str) if stop_loss_str else None

            take_profit_str = typer.prompt(
                "New take profit (press Enter to keep current)", default=""
            )
            take_profit = float(take_profit_str) if take_profit_str else None

            description = typer.prompt("New description (press Enter to keep current)", default="")
            description = description if description else None

            # Update trade
            success, message = journal_repo.update_trade(
                trade_id=trade_id,
                stop_loss=stop_loss,
                take_profit=take_profit,
                description=description,
            )

            if success:
                typer.echo(f"\n✅ {message}")
            else:
                typer.echo(f"\n❌ Error: {message}", err=True)
                raise typer.Exit(code=1)

        elif action == "close":
            typer.echo("\n🔒 Close Trade\n")

            # Get trade ID
            trade_id = typer.prompt("Trade ID to close", type=int)

            # Get current trade details
            trade = journal_repo.get_trade_by_id(trade_id)
            if not trade:
                typer.echo(f"❌ Trade {trade_id} not found", err=True)
                raise typer.Exit(code=1)

            if trade["status"] == "closed":
                typer.echo(f"❌ Trade {trade_id} is already closed", err=True)
                raise typer.Exit(code=1)

            typer.echo(f"\nClosing {trade['position_type']} position for {trade['ticker_symbol']}")
            typer.echo(f"  Entry price: ${trade['entry_price']:.2f}")
            typer.echo(f"  Position size: {trade['position_size']}")
            typer.echo(f"  Entry amount: ${trade['total_entry_amount']:,.2f}")
            typer.echo()

            # Get exit date
            exit_date_str = typer.prompt(
                "Exit date (YYYY-MM-DD, or press Enter for today)",
                default=date.today().strftime("%Y-%m-%d"),
            )
            try:
                exit_date = datetime.strptime(exit_date_str, "%Y-%m-%d").date()
            except ValueError:
                typer.echo("❌ Invalid date format", err=True)
                raise typer.Exit(code=1) from None

            # Get exit price
            exit_price = typer.prompt("Exit price", type=float)

            # Get exit fees
            fees_exit = typer.prompt("Exit fees", type=float, default=0.0)

            # Close trade
            success, message, profit_loss = journal_repo.close_trade(
                trade_id=trade_id,
                exit_date=exit_date,
                exit_price=exit_price,
                fees_exit=fees_exit,
            )

            if success:
                typer.echo(f"\n✅ {message}")
                if profit_loss is not None:
                    if profit_loss > 0:
                        typer.echo(f"   💰 Profit: ${profit_loss:,.2f}", nl=False)
                        typer.secho(" 📈", fg="green")
                    else:
                        typer.echo(f"   📉 Loss: ${profit_loss:,.2f}", nl=False)
                        typer.secho(" 📉", fg="red")
            else:
                typer.echo(f"\n❌ Error: {message}", err=True)
                raise typer.Exit(code=1)

        elif action == "list":
            typer.echo("\n📋 List Trades\n")

            # Prompt for filter type
            while True:
                list_type = typer.prompt("List type (open/closed/ticker/all)").strip().lower()
                if list_type in ["open", "closed", "ticker", "all"]:
                    break
                typer.echo(
                    "❌ Invalid list type. Please enter 'open', 'closed', 'ticker', or 'all'."
                )

            if list_type == "open":
                trades = journal_repo.get_open_trades()
                typer.echo(f"\n📂 Open Trades ({len(trades)}):")
            elif list_type == "closed":
                trades = journal_repo.get_closed_trades()
                typer.echo(f"\n📂 Closed Trades ({len(trades)}):")
            elif list_type == "ticker":
                ticker = typer.prompt("Ticker symbol").strip().upper()
                trades = journal_repo.get_trade_history(ticker)
                typer.echo(f"\n📂 Trades for {ticker} ({len(trades)}):")
            else:  # all
                trades = journal_repo.get_all_trades()
                typer.echo(f"\n📂 All Trades ({len(trades)}):")

            if not trades:
                typer.echo("  No trades found")
            else:
                # Display trades in a table
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("ID", style="dim", width=6)
                table.add_column("Ticker", style="green", width=8)
                table.add_column("Type", width=6)
                table.add_column("Entry Date", width=12)
                table.add_column("Entry", justify="right", width=10)
                table.add_column("Currency", width=8)
                table.add_column("Size", justify="right", width=8)
                table.add_column("Exit Date", width=12)
                table.add_column("Exit", justify="right", width=10)
                table.add_column("Status", width=8)
                table.add_column("P&L", justify="right", width=12)
                table.add_column("P&L %", justify="right", width=8)

                for trade in trades:
                    currency = trade.get("currency", "USD")

                    # Format entry price without currency
                    entry_str = f"{trade['entry_price']:.2f}"

                    # Format exit price without currency (if closed)
                    exit_str = (
                        f"{trade['exit_price']:.2f}" if trade["exit_price"] is not None else "-"
                    )

                    # Format exit date (if closed)
                    exit_date_str = str(trade["exit_date"]) if trade["exit_date"] else "-"

                    # Format P&L with currency
                    pl_str = (
                        f"{currency} {trade['profit_loss']:,.2f}"
                        if trade["profit_loss"] is not None
                        else "-"
                    )
                    pl_pct_str = (
                        f"{trade['profit_loss_pct']:.2f}%"
                        if trade["profit_loss_pct"] is not None
                        else "-"
                    )

                    pl_style = "green" if (trade["profit_loss"] or 0) > 0 else "red"

                    table.add_row(
                        str(trade["id"]),
                        trade["ticker_symbol"],
                        trade["position_type"],
                        str(trade["entry_date"]),
                        entry_str,
                        currency,
                        f"{trade['position_size']:.2f}",
                        exit_date_str,
                        exit_str,
                        trade["status"],
                        f"[{pl_style}]{pl_str}[/{pl_style}]",
                        f"[{pl_style}]{pl_pct_str}[/{pl_style}]",
                    )

                console = Console()
                console.print(table)

        elif action == "view":
            typer.echo("\n🔍 View Trade Details\n")

            # Get trade ID
            trade_id = typer.prompt("Trade ID", type=int)

            # Get trade
            trade = journal_repo.get_trade_by_id(trade_id)
            if not trade:
                typer.echo(f"❌ Trade {trade_id} not found", err=True)
                raise typer.Exit(code=1)

            # Display trade details
            typer.echo(f"\n{'=' * 60}")
            typer.echo(f"Trade #{trade['id']} - {trade['ticker_symbol']} ({trade['ticker_name']})")
            typer.echo(f"{'=' * 60}\n")

            typer.echo("📊 Position Details:")
            typer.echo(f"  Type: {trade['position_type'].upper()}")
            typer.echo(f"  Status: {trade['status'].upper()}")
            typer.echo()

            typer.echo("📥 Entry:")
            typer.echo(f"  Date: {trade['entry_date']}")
            typer.echo(f"  Price: ${trade['entry_price']:.2f}")
            typer.echo(f"  Size: {trade['position_size']}")
            typer.echo(f"  Fees: ${trade['fees_entry']:.2f}")
            typer.echo(f"  Total: ${trade['total_entry_amount']:,.2f}")
            typer.echo()

            typer.echo("🎯 Risk Management:")
            typer.echo(
                f"  Stop Loss: ${trade['stop_loss']:.2f}"
                if trade["stop_loss"]
                else "  Stop Loss: Not set"
            )
            typer.echo(
                f"  Take Profit: ${trade['take_profit']:.2f}"
                if trade["take_profit"]
                else "  Take Profit: Not set"
            )
            typer.echo()

            if trade["status"] == "closed":
                typer.echo("📤 Exit:")
                typer.echo(f"  Date: {trade['exit_date']}")
                typer.echo(f"  Price: ${trade['exit_price']:.2f}")
                typer.echo(f"  Fees: ${trade['fees_exit']:.2f}")
                typer.echo(f"  Total: ${trade['total_exit_amount']:,.2f}")
                typer.echo()

                typer.echo("💰 Performance:")
                pl_color = "green" if trade["profit_loss"] > 0 else "red"
                typer.echo("  P&L: ", nl=False)
                typer.secho(f"${trade['profit_loss']:,.2f}", fg=pl_color)
                typer.echo("  P&L %: ", nl=False)
                typer.secho(f"{trade['profit_loss_pct']:.2f}%", fg=pl_color)
                typer.echo()

            if trade["description"]:
                typer.echo("📝 Notes:")
                typer.echo(f"  {trade['description']}")
                typer.echo()

            typer.echo("⏱️  Timestamps:")
            typer.echo(f"  Created: {trade['created_at']}")
            typer.echo(f"  Updated: {trade['updated_at']}")
            typer.echo(f"\n{'=' * 60}\n")

        elif action == "performance":
            typer.echo("\n📊 Performance Statistics\n")

            # Prompt for date range (optional)
            start_date_str = typer.prompt(
                "Start date (YYYY-MM-DD, press Enter for all)", default=""
            )
            end_date_str = typer.prompt("End date (YYYY-MM-DD, press Enter for all)", default="")

            start_date = None
            end_date = None

            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                except ValueError:
                    typer.echo("❌ Invalid start date format", err=True)
                    raise typer.Exit(code=1) from None

            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                except ValueError:
                    typer.echo("❌ Invalid end date format", err=True)
                    raise typer.Exit(code=1) from None

            # Get closed trades for realized P&L
            closed_trades = journal_repo.get_closed_trades(start_date=start_date, end_date=end_date)

            # Get open trades for unrealized P&L
            open_trades = journal_repo.get_open_trades()

            # Filter open trades by entry date if date range specified
            if start_date or end_date:
                filtered_open = []
                for trade in open_trades:
                    entry_date = trade["entry_date"]
                    if isinstance(entry_date, str):
                        entry_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
                    if start_date and entry_date < start_date:
                        continue
                    if end_date and entry_date > end_date:
                        continue
                    filtered_open.append(trade)
                open_trades = filtered_open

            # Initialize provider manager for fetching current prices
            provider_manager = ProviderManager(
                primary_provider=config_obj.data.primary_provider,
                backup_providers=config_obj.data.backup_providers,
                db_path=config_obj.database.db_path if config_obj.database.enabled else None,
                historical_data_lookback_days=config_obj.analysis.historical_data_lookback_days,
            )

            typer.echo("\n⏳ Fetching current prices for open positions...")

            # Calculate unrealized P&L for open trades
            unrealized_pl = 0.0
            unrealized_pl_pct_list = []
            open_positions_with_prices = []

            # Cache for exchange rates to avoid multiple API calls for same currency
            exchange_rates = {}

            def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> float:
                """Get exchange rate from one currency to another using Yahoo Finance.

                Args:
                    from_currency: Source currency code (e.g., 'SEK', 'EUR')
                    to_currency: Target currency code (default: 'USD')

                Returns:
                    Exchange rate (1 from_currency = X to_currency)
                """
                if from_currency == to_currency:
                    return 1.0

                cache_key = f"{from_currency}{to_currency}"
                if cache_key in exchange_rates:
                    return exchange_rates[cache_key]

                try:
                    # Yahoo Finance uses format like "SEKUSD=X" for SEK to USD
                    ticker_symbol = f"{from_currency}{to_currency}=X"
                    price_obj = provider_manager.get_latest_price(ticker_symbol)
                    if price_obj and price_obj.close_price:
                        rate = price_obj.close_price
                        exchange_rates[cache_key] = rate
                        return rate
                    else:
                        typer.echo(
                            f"  ⚠️  Could not fetch exchange rate for {from_currency} to {to_currency}, using 1.0"
                        )
                        return 1.0
                except Exception as e:
                    typer.echo(
                        f"  ⚠️  Error fetching exchange rate {from_currency}/{to_currency}: {e}"
                    )
                    return 1.0

            for trade in open_trades:
                ticker = trade["ticker_symbol"]
                trade_currency = trade.get("currency", "USD")
                try:
                    # Fetch latest price using get_latest_price method
                    price_obj = provider_manager.get_latest_price(ticker)
                    if price_obj and price_obj.close_price:
                        current_price = price_obj.close_price

                        # Calculate unrealized P&L in the trade's native currency
                        entry_amount = trade["total_entry_amount"]
                        position_size = trade["position_size"]
                        position_type = trade["position_type"]

                        if position_type == "long":
                            current_value = (current_price * position_size) - (
                                trade["fees_entry"] or 0
                            )
                            trade_pl = current_value - entry_amount
                        else:  # short
                            current_value = (
                                (trade["entry_price"] * position_size * 2)
                                - (current_price * position_size)
                                - (trade["fees_entry"] or 0)
                            )
                            trade_pl = current_value - entry_amount

                        trade_pl_pct = (trade_pl / entry_amount) * 100 if entry_amount > 0 else 0

                        # Convert to USD for totals
                        exchange_rate = get_exchange_rate(trade_currency, "USD")
                        trade_pl_usd = trade_pl * exchange_rate

                        unrealized_pl += trade_pl_usd
                        unrealized_pl_pct_list.append(trade_pl_pct)
                        open_positions_with_prices.append(
                            {
                                **trade,
                                "current_price": current_price,
                                "unrealized_pl": trade_pl,
                                "unrealized_pl_usd": trade_pl_usd,
                                "unrealized_pl_pct": trade_pl_pct,
                                "exchange_rate": exchange_rate,
                            }
                        )
                    else:
                        typer.echo(f"  ⚠️  Could not fetch price for {ticker}")
                except Exception as e:
                    typer.echo(f"  ❌ Error fetching price for {ticker}: {e}")

            # Calculate realized P&L from closed trades
            realized_pl = sum(trade["profit_loss"] or 0 for trade in closed_trades)
            realized_pl_pct_list = [
                trade["profit_loss_pct"] for trade in closed_trades if trade["profit_loss_pct"]
            ]

            # Calculate statistics
            total_trades = len(closed_trades)
            winning_trades = sum(1 for trade in closed_trades if (trade["profit_loss"] or 0) > 0)
            losing_trades = sum(1 for trade in closed_trades if (trade["profit_loss"] or 0) < 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            avg_win = (
                sum(
                    trade["profit_loss"]
                    for trade in closed_trades
                    if (trade["profit_loss"] or 0) > 0
                )
                / winning_trades
                if winning_trades > 0
                else 0
            )
            avg_loss = (
                sum(
                    trade["profit_loss"]
                    for trade in closed_trades
                    if (trade["profit_loss"] or 0) < 0
                )
                / losing_trades
                if losing_trades > 0
                else 0
            )

            avg_realized_pl_pct = (
                sum(realized_pl_pct_list) / len(realized_pl_pct_list) if realized_pl_pct_list else 0
            )
            avg_unrealized_pl_pct = (
                sum(unrealized_pl_pct_list) / len(unrealized_pl_pct_list)
                if unrealized_pl_pct_list
                else 0
            )

            # Display results
            typer.echo("\n" + "=" * 60)
            typer.echo("📈 TRADING PERFORMANCE SUMMARY")
            typer.echo("=" * 60)

            if start_date or end_date:
                date_range = f"{start_date or 'Beginning'} to {end_date or 'Present'}"
                typer.echo(f"\n📅 Date Range: {date_range}")

            # Realized Performance (Closed Trades)
            typer.echo("\n💰 Realized Performance (Closed Trades):")
            typer.echo(f"  Total closed trades: {total_trades}")
            if total_trades > 0:
                typer.echo(f"  Winning trades: {winning_trades} ({win_rate:.1f}%)")
                typer.echo(f"  Losing trades: {losing_trades}")
                pl_color = "green" if realized_pl > 0 else "red"
                typer.echo("  Total realized P&L: ", nl=False)
                typer.secho(f"${realized_pl:,.2f}", fg=pl_color)
                typer.echo(f"  Average P&L per trade: ${realized_pl / total_trades:,.2f}")
                typer.echo(f"  Average return: {avg_realized_pl_pct:.2f}%")
                if winning_trades > 0:
                    typer.echo(f"  Average win: ${avg_win:,.2f}")
                if losing_trades > 0:
                    typer.echo(f"  Average loss: ${avg_loss:,.2f}")
                if winning_trades > 0 and losing_trades > 0:
                    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
                    typer.echo(f"  Profit factor: {profit_factor:.2f}")

            # Unrealized Performance (Open Trades)
            typer.echo("\n📊 Unrealized Performance (Open Trades):")
            typer.echo(f"  Total open positions: {len(open_positions_with_prices)}")
            if open_positions_with_prices:
                unrealized_color = "green" if unrealized_pl > 0 else "red"
                typer.echo("  Total unrealized P&L (USD): ", nl=False)
                typer.secho(f"${unrealized_pl:,.2f}", fg=unrealized_color)
                avg_unrealized = unrealized_pl / len(open_positions_with_prices)
                typer.echo(f"  Average unrealized P&L per position (USD): ${avg_unrealized:,.2f}")
                typer.echo(f"  Average unrealized return: {avg_unrealized_pl_pct:.2f}%")

                # Show top 3 best and worst performing open positions
                sorted_open = sorted(
                    open_positions_with_prices, key=lambda x: x["unrealized_pl_usd"], reverse=True
                )

                typer.echo("\n  📈 Top performing open positions:")
                for i, pos in enumerate(sorted_open[:3], 1):
                    pl_color = "green" if pos["unrealized_pl"] > 0 else "red"
                    currency = pos.get("currency", "USD")
                    typer.echo(f"    {i}. {pos['ticker_symbol']}: ", nl=False)
                    # Show native currency first, then USD equivalent if different
                    if currency != "USD":
                        typer.secho(
                            f"{currency} {pos['unrealized_pl']:,.2f} "
                            f"(${pos['unrealized_pl_usd']:,.2f} USD) "
                            f"{pos['unrealized_pl_pct']:.2f}%",
                            fg=pl_color,
                        )
                    else:
                        typer.secho(
                            f"${pos['unrealized_pl']:,.2f} ({pos['unrealized_pl_pct']:.2f}%)",
                            fg=pl_color,
                        )

                if len(sorted_open) > 3:
                    typer.echo("\n  📉 Worst performing open positions:")
                    for i, pos in enumerate(sorted_open[-3:][::-1], 1):
                        pl_color = "green" if pos["unrealized_pl"] > 0 else "red"
                        currency = pos.get("currency", "USD")
                        typer.echo(f"    {i}. {pos['ticker_symbol']}: ", nl=False)
                        # Show native currency first, then USD equivalent if different
                        if currency != "USD":
                            typer.secho(
                                f"{currency} {pos['unrealized_pl']:,.2f} "
                                f"(${pos['unrealized_pl_usd']:,.2f} USD) "
                                f"{pos['unrealized_pl_pct']:.2f}%",
                                fg=pl_color,
                            )
                        else:
                            typer.secho(
                                f"${pos['unrealized_pl']:,.2f} ({pos['unrealized_pl_pct']:.2f}%)",
                                fg=pl_color,
                            )

            # Overall Performance
            total_pl = realized_pl + unrealized_pl
            typer.echo("\n🎯 Overall Performance:")
            overall_color = "green" if total_pl > 0 else "red"
            typer.echo("  Total P&L (realized + unrealized): ", nl=False)
            typer.secho(f"${total_pl:,.2f}", fg=overall_color)

            typer.echo("\n" + "=" * 60 + "\n")

        else:
            typer.echo(f"❌ Unknown action: {action}", err=True)
            typer.echo("Valid actions: add, update, close, list, view, performance")
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Trading journal error: {e}", exc_info=True)
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e
