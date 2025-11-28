"""Fundamental analysis calculations and scoring using free tier data.

NOTE: This implementation uses ONLY free tier API data:
- Company info from Finnhub (free tier)
- News sentiment from Finnhub (free tier)
- Analyst recommendations from Finnhub (free tier)
- Price data from Yahoo Finance (free tier)

Premium endpoints like /stock/metric and /stock/financials are NOT used
to maintain cost efficiency and free tier compatibility.
"""

from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class FundamentalAnalyzer:
    """Calculates fundamental scores from free tier API data only.

    Scores based on:
    - Analyst recommendations (from /stock/recommendation-trend - FREE TIER)
    - News sentiment (from /news-sentiment - FREE TIER)
    - Price momentum (from price data - FREE TIER)
    - Company information (from /stock/profile2 - FREE TIER)
    """

    @staticmethod
    def calculate_score(
        analyst_data: dict[str, Any] = None,
        sentiment: dict[str, Any] = None,
        price_context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Calculate fundamental score from free tier data sources.

        Args:
            analyst_data: Analyst recommendation trends from Finnhub
                         Expected keys: strong_buy, buy, hold, sell, strong_sell, total_analysts
            sentiment: News sentiment from Finnhub
                      Expected keys: positive, negative, neutral
            price_context: Price momentum context
                          Expected keys: change_percent, trend (bullish/bearish)

        Returns:
            Dictionary with component scores and overall fundamental score
        """
        analyst_score = FundamentalAnalyzer._score_analyst_consensus(analyst_data)
        sentiment_score = FundamentalAnalyzer._score_sentiment(sentiment)
        momentum_score = FundamentalAnalyzer._score_momentum(price_context)

        # Weight the components
        # Analyst: 40%, Sentiment: 35%, Momentum: 25%
        overall_score = analyst_score * 0.40 + sentiment_score * 0.35 + momentum_score * 0.25

        return {
            "overall_score": max(0, min(100, overall_score)),
            "analyst_score": analyst_score,
            "sentiment_score": sentiment_score,
            "momentum_score": momentum_score,
            "components": {
                "analyst_consensus": {
                    "score": analyst_score,
                    "data": analyst_data or {},
                },
                "sentiment": {
                    "score": sentiment_score,
                    "data": sentiment or {},
                },
                "momentum": {
                    "score": momentum_score,
                    "data": price_context or {},
                },
            },
        }

    @staticmethod
    def _score_analyst_consensus(analyst_data: dict[str, Any]) -> float:
        """Score based on analyst recommendation distribution.

        Args:
            analyst_data: Analyst recommendations with buy/hold/sell counts

        Returns:
            Score 0-100
        """
        if not analyst_data:
            return 50  # Neutral if no data

        strong_buy = analyst_data.get("strong_buy", 0)
        buy = analyst_data.get("buy", 0)
        hold = analyst_data.get("hold", 0)
        sell = analyst_data.get("sell", 0)
        strong_sell = analyst_data.get("strong_sell", 0)
        total = analyst_data.get("total_analysts", 0)

        if total == 0:
            return 50

        # Calculate weighted average score
        bullish = strong_buy * 100 + buy * 75
        neutral = hold * 50
        bearish = sell * 25 + strong_sell * 0

        score = (bullish + neutral + bearish) / total

        return max(0, min(100, score))

    @staticmethod
    def _score_sentiment(sentiment: dict[str, Any]) -> float:
        """Score based on news sentiment distribution.

        Args:
            sentiment: Sentiment data with positive, negative, neutral ratios

        Returns:
            Score 0-100
        """
        if not sentiment:
            return 50  # Neutral if no data

        positive = sentiment.get("positive", 0)
        negative = sentiment.get("negative", 0)
        neutral = sentiment.get("neutral", 0)

        # Normalize to 0-1 range
        total = positive + negative + neutral
        if total == 0:
            return 50

        positive_pct = positive / total if total > 0 else 0
        negative_pct = negative / total if total > 0 else 0

        # Score: positive sentiment increases score, negative decreases
        # Baseline: 50 (neutral), can go 0-100
        score = 50 + (positive_pct * 50) - (negative_pct * 50)

        return max(0, min(100, score))

    @staticmethod
    def _score_momentum(price_context: dict[str, Any]) -> float:
        """Score based on price momentum and trend.

        Args:
            price_context: Price change percentage and trend direction

        Returns:
            Score 0-100
        """
        if not price_context:
            return 50  # Neutral if no data

        change_percent = price_context.get("change_percent", 0)
        trend = price_context.get("trend", "neutral")

        score = 50

        # Price change contribution (±30 points)
        if change_percent > 0.05:  # 5% gain
            score += 15
        elif change_percent > 0.02:  # 2% gain
            score += 8
        elif change_percent < -0.05:  # 5% loss
            score -= 15
        elif change_percent < -0.02:  # 2% loss
            score -= 8

        # Trend contribution (±15 points)
        if trend == "bullish":
            score += 15
        elif trend == "bearish":
            score -= 15

        return max(0, min(100, score))

    @staticmethod
    def get_recommendation(score: float) -> str:
        """Convert score to investment recommendation.

        Args:
            score: Fundamental score (0-100)

        Returns:
            Recommendation string
        """
        if score >= 75:
            return "strong_buy"
        elif score >= 60:
            return "buy"
        elif score >= 40:
            return "hold"
        elif score >= 25:
            return "sell"
        else:
            return "strong_sell"
