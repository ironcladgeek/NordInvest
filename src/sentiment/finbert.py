"""Local FinBERT sentiment scoring for financial text.

Provides zero-cost sentiment analysis using the ProsusAI/finbert model,
with optional LLM fallback for theme extraction.
"""

from dataclasses import dataclass
from typing import Any, Optional

from src.data.models import NewsArticle
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import transformers and torch
try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.info("transformers/torch not installed, FinBERT scoring not available")


@dataclass
class SentimentScore:
    """Sentiment score for a single article."""

    sentiment: str  # 'positive', 'negative', 'neutral'
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    raw_probs: Optional[dict[str, float]] = None  # Optional raw probabilities


class FinBERTSentimentScorer:
    """Local FinBERT-based sentiment scorer for financial text.

    Uses the ProsusAI/finbert model specifically trained on financial text,
    providing more accurate sentiment analysis than general-purpose models.
    """

    # Default model for financial sentiment
    DEFAULT_MODEL = "ProsusAI/finbert"

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        batch_size: int = 32,
        max_length: int = 512,
    ):
        """Initialize FinBERT sentiment scorer.

        Args:
            model_name: Hugging Face model name. Defaults to ProsusAI/finbert.
            device: Device to use ('cpu', 'cuda', 'mps'). Auto-detected if None.
            batch_size: Batch size for processing multiple texts.
            max_length: Maximum token length for texts.
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers and torch are required for FinBERT. "
                "Install with: pip install transformers torch"
            )

        self.model_name = model_name or self.DEFAULT_MODEL
        self.batch_size = batch_size
        self.max_length = max_length

        # Auto-detect device
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = device

        logger.info(
            f"Initializing FinBERT scorer with model={self.model_name}, device={self.device}"
        )

        # Load model and tokenizer
        self._tokenizer = None
        self._model = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Lazy-load the model and tokenizer."""
        if self._loaded:
            return

        logger.info(f"Loading FinBERT model: {self.model_name}")
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self._model = self._model.to(self.device)
        self._model.eval()
        self._loaded = True
        logger.info(f"FinBERT model loaded successfully on {self.device}")

    def score_text(self, text: str) -> SentimentScore:
        """Score sentiment for a single text.

        Args:
            text: Text to analyze

        Returns:
            SentimentScore with sentiment label, score, and confidence
        """
        self._ensure_loaded()

        # Tokenize
        inputs = self._tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        ).to(self.device)

        # Get predictions
        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)[0]

        # FinBERT outputs: [positive, negative, neutral]
        # Note: Some models have different orderings, we handle this
        labels = ["positive", "negative", "neutral"]
        if hasattr(self._model.config, "id2label"):
            labels = [self._model.config.id2label[i] for i in range(len(probs))]

        # Create probability dict
        raw_probs = {labels[i]: float(probs[i]) for i in range(len(probs))}

        # Find the label indices
        pos_idx = labels.index("positive") if "positive" in labels else 0
        neg_idx = labels.index("negative") if "negative" in labels else 1
        neut_idx = labels.index("neutral") if "neutral" in labels else 2

        # Calculate score (-1 to 1)
        score = float(probs[pos_idx] - probs[neg_idx])

        # Get predicted sentiment
        pred_idx = int(probs.argmax())
        sentiment = labels[pred_idx]

        # Confidence is the max probability
        confidence = float(probs.max())

        return SentimentScore(
            sentiment=sentiment,
            score=score,
            confidence=confidence,
            raw_probs=raw_probs,
        )

    def score_articles(
        self,
        articles: list[NewsArticle],
        include_summary: bool = True,
    ) -> list[SentimentScore]:
        """Score sentiment for multiple articles.

        Args:
            articles: List of news articles to analyze
            include_summary: If True, combine title and summary for analysis

        Returns:
            List of SentimentScore objects (same order as input)
        """
        if not articles:
            return []

        self._ensure_loaded()

        # Prepare texts
        texts = []
        for article in articles:
            if include_summary and article.summary:
                text = f"{article.title}. {article.summary}"
            else:
                text = article.title
            texts.append(text)

        # Process in batches
        results = []
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i : i + self.batch_size]
            batch_results = self._score_batch(batch_texts)
            results.extend(batch_results)

        return results

    def _score_batch(self, texts: list[str]) -> list[SentimentScore]:
        """Score a batch of texts.

        Args:
            texts: List of texts to analyze

        Returns:
            List of SentimentScore objects
        """
        # Tokenize batch
        inputs = self._tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        ).to(self.device)

        # Get predictions
        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)

        # Get labels
        labels = ["positive", "negative", "neutral"]
        if hasattr(self._model.config, "id2label"):
            labels = [self._model.config.id2label[i] for i in range(probs.shape[1])]

        # Find label indices
        pos_idx = labels.index("positive") if "positive" in labels else 0
        neg_idx = labels.index("negative") if "negative" in labels else 1

        # Convert to SentimentScore objects
        results = []
        for i in range(len(texts)):
            prob = probs[i]

            # Calculate score and confidence
            score = float(prob[pos_idx] - prob[neg_idx])
            pred_idx = int(prob.argmax())
            sentiment = labels[pred_idx]
            confidence = float(prob.max())

            raw_probs = {labels[j]: float(prob[j]) for j in range(len(labels))}

            results.append(
                SentimentScore(
                    sentiment=sentiment,
                    score=score,
                    confidence=confidence,
                    raw_probs=raw_probs,
                )
            )

        return results

    def update_articles_with_scores(
        self,
        articles: list[NewsArticle],
    ) -> list[NewsArticle]:
        """Update articles with local sentiment scores.

        Modifies articles in-place with sentiment and sentiment_score fields.

        Args:
            articles: List of news articles

        Returns:
            Same articles with updated sentiment fields
        """
        if not articles:
            return articles

        scores = self.score_articles(articles)

        for article, score in zip(articles, scores):
            article.sentiment = score.sentiment
            article.sentiment_score = score.score

        logger.info(f"Updated {len(articles)} articles with FinBERT sentiment scores")
        return articles

    def get_aggregate_sentiment(
        self,
        articles: list[NewsArticle],
    ) -> dict[str, Any]:
        """Get aggregate sentiment statistics for articles.

        Args:
            articles: List of news articles (with or without existing sentiment)

        Returns:
            Dictionary with aggregate sentiment metrics
        """
        # Score articles if they don't have sentiment
        needs_scoring = any(a.sentiment is None for a in articles)
        if needs_scoring:
            scores = self.score_articles(articles)
        else:
            # Use existing sentiment
            scores = [
                SentimentScore(
                    sentiment=a.sentiment or "neutral",
                    score=a.sentiment_score or 0.0,
                    confidence=0.8,  # Assume moderate confidence for pre-scored
                )
                for a in articles
            ]

        if not scores:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "avg_score": 0.0,
                "avg_confidence": 0.0,
                "overall_sentiment": "neutral",
            }

        # Calculate statistics
        positive = sum(1 for s in scores if s.sentiment == "positive")
        negative = sum(1 for s in scores if s.sentiment == "negative")
        neutral = sum(1 for s in scores if s.sentiment == "neutral")
        total = len(scores)

        avg_score = sum(s.score for s in scores) / total
        avg_confidence = sum(s.confidence for s in scores) / total

        # Determine overall sentiment
        if avg_score > 0.1:
            overall = "positive"
        elif avg_score < -0.1:
            overall = "negative"
        else:
            overall = "neutral"

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_pct": round(100 * positive / total, 1) if total > 0 else 0,
            "negative_pct": round(100 * negative / total, 1) if total > 0 else 0,
            "neutral_pct": round(100 * neutral / total, 1) if total > 0 else 0,
            "avg_score": round(avg_score, 3),
            "avg_confidence": round(avg_confidence, 3),
            "overall_sentiment": overall,
            "scoring_method": "finbert_local",
        }

    @classmethod
    def is_available(cls) -> bool:
        """Check if FinBERT scoring is available.

        Returns:
            True if transformers and torch are installed
        """
        return TRANSFORMERS_AVAILABLE
