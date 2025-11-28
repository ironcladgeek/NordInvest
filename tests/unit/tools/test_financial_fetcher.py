"""Tests for FinancialDataFetcherTool using free tier endpoints."""

from unittest.mock import MagicMock

from src.tools.fetchers import FinancialDataFetcherTool


class TestFinancialDataFetcherTool:
    """Test FinancialDataFetcherTool class with free tier data sources."""

    def test_tool_initialization(self):
        """Test tool initialization."""
        tool = FinancialDataFetcherTool()

        assert tool.name == "FinancialDataFetcher"
        assert tool.description is not None
        assert "free tier" in tool.description.lower()

    def test_run_missing_ticker(self):
        """Test run without ticker."""
        tool = FinancialDataFetcherTool()

        result = tool.run(None)

        assert "error" in result
        assert result["analyst_data"] == {}
        assert result["sentiment"] == {}

    def test_run_provider_not_available(self):
        """Test run when provider is not available."""
        tool = FinancialDataFetcherTool()

        mock_provider = MagicMock()
        mock_provider.is_available = False
        tool.finnhub_provider = mock_provider

        result = tool.run("TEST_UNAVAIL")

        assert "error" in result
        assert "not available" in result["error"]

    def test_run_with_analyst_data(self):
        """Test successful fetch with analyst data."""
        tool = FinancialDataFetcherTool()

        mock_finnhub = MagicMock()
        mock_finnhub.is_available = True
        mock_finnhub.get_recommendation_trends.return_value = {
            "strong_buy": 5,
            "buy": 10,
            "hold": 3,
            "sell": 1,
            "strong_sell": 0,
            "total_analysts": 19,
        }
        mock_finnhub.get_news_sentiment.return_value = {
            "positive": 0.65,
            "negative": 0.20,
            "neutral": 0.15,
        }

        mock_price = MagicMock()
        mock_price_obj = MagicMock()
        mock_price_obj.close_price = 100.0
        mock_price.get_stock_prices.return_value = [
            MagicMock(close_price=95.0),
            MagicMock(close_price=100.0),
        ]

        tool.finnhub_provider = mock_finnhub
        tool.price_provider = mock_price

        result = tool.run("TEST_TICKER")

        assert result["ticker"] == "TEST_TICKER"
        assert "analyst_data" in result
        assert "sentiment" in result
        assert "price_context" in result
        assert "error" not in result

    def test_run_with_partial_data(self):
        """Test run with partial data (missing sentiment)."""
        tool = FinancialDataFetcherTool()

        mock_finnhub = MagicMock()
        mock_finnhub.is_available = True
        mock_finnhub.get_recommendation_trends.return_value = {
            "total_analysts": 10,
        }
        mock_finnhub.get_news_sentiment.return_value = None  # Missing sentiment

        mock_price = MagicMock()
        mock_price.get_stock_prices.return_value = []

        tool.finnhub_provider = mock_finnhub
        tool.price_provider = mock_price

        result = tool.run("PARTIAL_DATA")

        assert result["ticker"] == "PARTIAL_DATA"
        assert result["sentiment"] == {}  # Empty but present
        assert "error" not in result

    def test_run_with_error_handling(self):
        """Test error handling when API calls fail."""
        tool = FinancialDataFetcherTool()

        mock_finnhub = MagicMock()
        mock_finnhub.is_available = True
        mock_finnhub.get_recommendation_trends.side_effect = RuntimeError("API Error")

        tool.finnhub_provider = mock_finnhub

        result = tool.run("ERROR_TICKER")

        assert "error" in result
        assert result["analyst_data"] == {}

    def test_price_context_calculation(self):
        """Test price context calculation from price data."""
        tool = FinancialDataFetcherTool()

        # Create mock price objects
        old_price = MagicMock()
        old_price.close_price = 95.0
        new_price = MagicMock()
        new_price.close_price = 105.0

        tool.price_provider = MagicMock()
        tool.price_provider.get_stock_prices.return_value = [old_price, new_price]

        price_context = tool._get_price_context("PRICE_TEST")

        assert price_context["change_percent"] == pytest.approx(0.1053, abs=0.001)
        assert price_context["trend"] == "bullish"
        assert price_context["latest_price"] == 105.0

    def test_price_context_empty_prices(self):
        """Test price context when no price data available."""
        tool = FinancialDataFetcherTool()

        tool.price_provider = MagicMock()
        tool.price_provider.get_stock_prices.return_value = []

        price_context = tool._get_price_context("NO_PRICES")

        assert price_context["change_percent"] == 0
        assert price_context["trend"] == "neutral"


# Import pytest for approx
import pytest
