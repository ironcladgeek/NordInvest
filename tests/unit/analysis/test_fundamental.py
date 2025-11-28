"""Tests for fundamental analysis module using free tier data."""

from src.analysis.fundamental import FundamentalAnalyzer


class TestFundamentalAnalyzer:
    """Test FundamentalAnalyzer class with free tier data sources."""

    def test_calculate_score_with_all_data(self):
        """Test scoring with complete data from all sources."""
        analyst_data = {
            "strong_buy": 5,
            "buy": 8,
            "hold": 3,
            "sell": 1,
            "strong_sell": 0,
            "total_analysts": 17,
        }
        sentiment = {"positive": 0.65, "negative": 0.15, "neutral": 0.20}
        price_context = {"change_percent": 0.08, "trend": "bullish"}

        result = FundamentalAnalyzer.calculate_score(analyst_data, sentiment, price_context)

        assert "overall_score" in result
        assert "analyst_score" in result
        assert "sentiment_score" in result
        assert "momentum_score" in result
        assert 0 <= result["overall_score"] <= 100

    def test_calculate_score_no_data(self):
        """Test scoring with no data (all neutral)."""
        result = FundamentalAnalyzer.calculate_score(None, None, None)

        assert result["overall_score"] == 50  # Neutral score
        assert result["analyst_score"] == 50
        assert result["sentiment_score"] == 50
        assert result["momentum_score"] == 50

    def test_score_analyst_consensus_bullish(self):
        """Test analyst consensus scoring with strong buy consensus."""
        analyst_data = {
            "strong_buy": 10,
            "buy": 5,
            "hold": 2,
            "sell": 1,
            "strong_sell": 0,
            "total_analysts": 18,
        }

        score = FundamentalAnalyzer._score_analyst_consensus(analyst_data)

        assert score > 70  # Strong bullish consensus

    def test_score_analyst_consensus_bearish(self):
        """Test analyst consensus scoring with bearish consensus."""
        analyst_data = {
            "strong_buy": 0,
            "buy": 2,
            "hold": 3,
            "sell": 8,
            "strong_sell": 5,
            "total_analysts": 18,
        }

        score = FundamentalAnalyzer._score_analyst_consensus(analyst_data)

        assert score < 30  # Bearish consensus

    def test_score_analyst_consensus_no_data(self):
        """Test analyst scoring with no data."""
        score = FundamentalAnalyzer._score_analyst_consensus(None)
        assert score == 50

    def test_score_sentiment_positive(self):
        """Test sentiment scoring with positive news."""
        sentiment = {"positive": 0.75, "negative": 0.10, "neutral": 0.15}

        score = FundamentalAnalyzer._score_sentiment(sentiment)

        assert score > 70  # Positive sentiment

    def test_score_sentiment_negative(self):
        """Test sentiment scoring with negative news."""
        sentiment = {"positive": 0.10, "negative": 0.75, "neutral": 0.15}

        score = FundamentalAnalyzer._score_sentiment(sentiment)

        assert score < 30  # Negative sentiment

    def test_score_sentiment_neutral(self):
        """Test sentiment scoring with neutral news."""
        sentiment = {"positive": 0.33, "negative": 0.33, "neutral": 0.34}

        score = FundamentalAnalyzer._score_sentiment(sentiment)

        assert 45 < score < 55  # Close to neutral

    def test_score_sentiment_no_data(self):
        """Test sentiment scoring with no data."""
        score = FundamentalAnalyzer._score_sentiment(None)
        assert score == 50

    def test_score_momentum_bullish(self):
        """Test momentum scoring with bullish trend."""
        price_context = {"change_percent": 0.10, "trend": "bullish"}

        score = FundamentalAnalyzer._score_momentum(price_context)

        assert score > 60  # Bullish momentum

    def test_score_momentum_bearish(self):
        """Test momentum scoring with bearish trend."""
        price_context = {"change_percent": -0.10, "trend": "bearish"}

        score = FundamentalAnalyzer._score_momentum(price_context)

        assert score < 40  # Bearish momentum

    def test_score_momentum_neutral(self):
        """Test momentum scoring with neutral trend."""
        price_context = {"change_percent": 0.01, "trend": "neutral"}

        score = FundamentalAnalyzer._score_momentum(price_context)

        assert 45 < score < 55  # Close to neutral

    def test_score_momentum_no_data(self):
        """Test momentum scoring with no data."""
        score = FundamentalAnalyzer._score_momentum(None)
        assert score == 50

    def test_get_recommendation_strong_buy(self):
        """Test recommendation for high score."""
        recommendation = FundamentalAnalyzer.get_recommendation(80)
        assert recommendation == "strong_buy"

    def test_get_recommendation_buy(self):
        """Test recommendation for good score."""
        recommendation = FundamentalAnalyzer.get_recommendation(65)
        assert recommendation == "buy"

    def test_get_recommendation_hold(self):
        """Test recommendation for neutral score."""
        recommendation = FundamentalAnalyzer.get_recommendation(50)
        assert recommendation == "hold"

    def test_get_recommendation_sell(self):
        """Test recommendation for poor score."""
        recommendation = FundamentalAnalyzer.get_recommendation(30)
        assert recommendation == "sell"

    def test_get_recommendation_strong_sell(self):
        """Test recommendation for very poor score."""
        recommendation = FundamentalAnalyzer.get_recommendation(10)
        assert recommendation == "strong_sell"

    def test_score_bounds(self):
        """Test that all scores stay within 0-100 bounds."""
        # Extreme bullish
        bullish_analyst = {
            "strong_buy": 100,
            "buy": 0,
            "hold": 0,
            "sell": 0,
            "strong_sell": 0,
            "total_analysts": 100,
        }
        bullish_sentiment = {"positive": 1.0, "negative": 0.0, "neutral": 0.0}
        bullish_momentum = {"change_percent": 1.0, "trend": "bullish"}

        result = FundamentalAnalyzer.calculate_score(
            bullish_analyst, bullish_sentiment, bullish_momentum
        )
        assert result["overall_score"] <= 100
        assert result["analyst_score"] <= 100
        assert result["sentiment_score"] <= 100
        assert result["momentum_score"] <= 100

        # Extreme bearish
        bearish_analyst = {
            "strong_buy": 0,
            "buy": 0,
            "hold": 0,
            "sell": 0,
            "strong_sell": 100,
            "total_analysts": 100,
        }
        bearish_sentiment = {"positive": 0.0, "negative": 1.0, "neutral": 0.0}
        bearish_momentum = {"change_percent": -1.0, "trend": "bearish"}

        result = FundamentalAnalyzer.calculate_score(
            bearish_analyst, bearish_sentiment, bearish_momentum
        )
        assert result["overall_score"] >= 0
        assert result["analyst_score"] >= 0
        assert result["sentiment_score"] >= 0
        assert result["momentum_score"] >= 0

    def test_component_weighting(self):
        """Test that component weighting is applied (40%, 35%, 25%)."""
        # High analyst, neutral sentiment, neutral momentum
        analyst_data = {
            "strong_buy": 15,
            "buy": 0,
            "hold": 0,
            "sell": 0,
            "strong_sell": 0,
            "total_analysts": 15,
        }
        sentiment = {"positive": 0.5, "negative": 0.5, "neutral": 0.0}
        momentum = {"change_percent": 0.0, "trend": "neutral"}

        result = FundamentalAnalyzer.calculate_score(analyst_data, sentiment, momentum)

        # With high analyst (100), neutral sentiment (50), neutral momentum (50)
        # Overall = 100*0.40 + 50*0.35 + 50*0.25 = 40 + 17.5 + 12.5 = 70
        analyst_score = result["analyst_score"]
        overall_score = result["overall_score"]

        # Overall should be significantly influenced by analyst score (40% weight)
        assert analyst_score > 80  # Strong buy consensus
        assert overall_score > 65 and overall_score < 75  # Weighted average
