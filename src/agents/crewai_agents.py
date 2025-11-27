"""CrewAI-based intelligent agents for analysis."""

from typing import Any, Optional

from crewai import Agent, Task

from src.config.llm import initialize_llm_client
from src.config.schemas import LLMConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CrewAIAgentFactory:
    """Factory for creating CrewAI-based agents."""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize the factory with LLM configuration.

        Args:
            llm_config: LLM configuration (uses default if not provided)
        """
        self.llm_config = llm_config or LLMConfig()
        self.llm_client = initialize_llm_client(self.llm_config)
        logger.info(f"Initialized CrewAI factory with {self.llm_config.provider} provider")

    def create_market_scanner_agent(self) -> Agent:
        """Create market scanner agent.

        Returns:
            Configured CrewAI Agent for market scanning
        """
        return Agent(
            role="Market Scanner Analyst",
            goal=(
                "Scan financial markets to identify instruments with significant price movements, "
                "unusual volume patterns, and anomalies that warrant deeper analysis"
            ),
            backstory=(
                "You are an expert market analyst with deep knowledge of technical patterns and "
                "market microstructure. You excel at detecting emerging trends, unusual volume "
                "patterns, and price movements that signal potential trading opportunities. "
                "Your keen eye for detail helps identify instruments that deserve deeper analysis. "
                "You consider both daily and weekly price movements, volume anomalies, and positions "
                "at technical extremes."
            ),
            tools=[],  # Tools will be added separately
            llm=self.llm_client,
            verbose=False,
            allow_delegation=False,
        )

    def create_technical_analysis_agent(self) -> Agent:
        """Create technical analysis agent.

        Returns:
            Configured CrewAI Agent for technical analysis
        """
        return Agent(
            role="Senior Technical Analyst",
            goal=(
                "Analyze price charts and technical indicators to identify trading opportunities, "
                "trend strength, support/resistance levels, and potential entry/exit points"
            ),
            backstory=(
                "You are a skilled technical analyst with expertise in chart patterns, "
                "moving averages, momentum indicators, and volume analysis. "
                "You use technical indicators to identify trend strength, reversals, and "
                "support/resistance levels. Your analysis incorporates multiple timeframes "
                "and helps traders make informed decisions based on price action. "
                "You understand how different indicators complement each other and provide "
                "holistic technical insights."
            ),
            tools=[],  # Tools will be added separately
            llm=self.llm_client,
            verbose=False,
            allow_delegation=False,
        )

    def create_fundamental_analysis_agent(self) -> Agent:
        """Create fundamental analysis agent.

        Returns:
            Configured CrewAI Agent for fundamental analysis
        """
        return Agent(
            role="Fundamental Analyst",
            goal=(
                "Analyze financial statements and metrics to assess company health, growth "
                "prospects, and valuation. Provide investment-grade fundamental scores."
            ),
            backstory=(
                "You are an experienced fundamental analyst with deep expertise in financial "
                "statement analysis, ratio interpretation, and company valuation. "
                "You evaluate earnings growth, profit margins, cash flow quality, debt levels, "
                "and valuation metrics (P/E, EV/EBITDA, P/B, PEG). "
                "You can identify high-quality companies at reasonable valuations and weak "
                "companies even if they appear cheap. You understand industry dynamics and "
                "competitive positioning."
            ),
            tools=[],  # Tools will be added separately
            llm=self.llm_client,
            verbose=False,
            allow_delegation=False,
        )

    def create_sentiment_analysis_agent(self) -> Agent:
        """Create sentiment analysis agent.

        Returns:
            Configured CrewAI Agent for sentiment analysis
        """
        return Agent(
            role="Sentiment Analyst",
            goal=(
                "Analyze news, events, and market sentiment to assess how external factors "
                "impact investment thesis. Identify key events and their implications."
            ),
            backstory=(
                "You are a skilled sentiment analyst with expertise in news analysis, event "
                "classification, and market sentiment assessment. "
                "You process recent news articles to filter by relevance, extract key events, "
                "and score sentiment (positive/negative/neutral). "
                "You understand how different types of events (earnings, regulatory, competitive) "
                "impact company valuations and stock prices. "
                "You weight event importance and assess market reaction likelihood."
            ),
            tools=[],  # Tools will be added separately
            llm=self.llm_client,
            verbose=False,
            allow_delegation=False,
        )

    def create_signal_synthesizer_agent(self) -> Agent:
        """Create signal synthesizer agent.

        Returns:
            Configured CrewAI Agent for signal synthesis
        """
        return Agent(
            role="Investment Signal Synthesizer",
            goal=(
                "Synthesize technical, fundamental, and sentiment analyses into comprehensive "
                "investment signals with clear reasoning and risk assessment"
            ),
            backstory=(
                "You are a senior investment strategist responsible for synthesizing insights "
                "from multiple analysis perspectives. "
                "You combine technical, fundamental, and sentiment signals into coherent "
                "investment theses. You weigh conflicting signals, identify consensus areas, "
                "and provide clear recommendation rationale. "
                "You assess confidence levels based on signal agreement and data quality. "
                "You generate human-readable investment narratives that explain the investment case."
            ),
            tools=[],  # Tools will be added separately
            llm=self.llm_client,
            verbose=False,
            allow_delegation=False,
        )


class CrewAITaskFactory:
    """Factory for creating structured CrewAI tasks."""

    @staticmethod
    def create_market_scan_task(
        agent: Agent,
        ticker: str,
        context: dict[str, Any],
    ) -> Task:
        """Create market scanning task.

        Args:
            agent: Market scanner agent
            ticker: Stock ticker symbol
            context: Additional context for the scan

        Returns:
            Configured Task object
        """
        return Task(
            description=(
                f"Scan {ticker} for market anomalies and trading signals.\n"
                f"Analyze the following data:\n"
                f"- Price movements (daily and weekly changes)\n"
                f"- Volume patterns and anomalies\n"
                f"- Technical extremes (30-day highs/lows)\n"
                f"\n"
                f"Identify:\n"
                f"1. Significant price movements (>5% daily, >15% weekly)\n"
                f"2. Unusual volume spikes (>1.5x average)\n"
                f"3. New 30-day highs or lows\n"
                f"4. Any other market anomalies\n"
                f"\n"
                f"Provide a clear assessment of whether {ticker} warrants deeper analysis."
            ),
            agent=agent,
            expected_output=(
                "List of anomalies found with explanations and recommendation to analyze further"
            ),
        )

    @staticmethod
    def create_technical_analysis_task(
        agent: Agent,
        ticker: str,
        context: dict[str, Any],
    ) -> Task:
        """Create technical analysis task.

        Args:
            agent: Technical analyst agent
            ticker: Stock ticker symbol
            context: Additional context including price data

        Returns:
            Configured Task object
        """
        return Task(
            description=(
                f"Perform comprehensive technical analysis of {ticker}.\n"
                f"\n"
                f"Analyze the following indicators:\n"
                f"- Moving averages (SMA 20, 50, 200)\n"
                f"- Momentum (RSI 14, MACD)\n"
                f"- Volatility (ATR)\n"
                f"- Volume trends\n"
                f"\n"
                f"Assess:\n"
                f"1. Current trend (uptrend, downtrend, range-bound)\n"
                f"2. Trend strength and momentum\n"
                f"3. Support and resistance levels\n"
                f"4. Chart patterns and formations\n"
                f"5. Entry and exit points\n"
                f"\n"
                f"Provide a technical score (0-100) and reasoning."
            ),
            agent=agent,
            expected_output=(
                "Structured technical analysis with trend assessment, indicator readings, "
                "and technical score (0-100)"
            ),
        )

    @staticmethod
    def create_fundamental_analysis_task(
        agent: Agent,
        ticker: str,
        context: dict[str, Any],
    ) -> Task:
        """Create fundamental analysis task.

        Args:
            agent: Fundamental analyst agent
            ticker: Stock ticker symbol
            context: Additional context including financial data

        Returns:
            Configured Task object
        """
        return Task(
            description=(
                f"Analyze fundamentals of {ticker}.\n"
                f"\n"
                f"Evaluate:\n"
                f"1. Revenue and earnings growth (YoY, QoQ)\n"
                f"2. Profit margins (gross, operating, net)\n"
                f"3. Cash flow quality and trends\n"
                f"4. Debt ratios and financial health\n"
                f"5. Valuation metrics (P/E, EV/EBITDA, P/B, PEG)\n"
                f"6. Return on equity and capital efficiency\n"
                f"\n"
                f"Assess:\n"
                f"1. Business quality and competitive position\n"
                f"2. Growth prospects\n"
                f"3. Valuation attractiveness\n"
                f"4. Financial risks\n"
                f"\n"
                f"Provide a fundamental score (0-100) and recommendation."
            ),
            agent=agent,
            expected_output=(
                "Detailed fundamental analysis with metrics assessment, growth prospects, "
                "valuation analysis, and fundamental score (0-100)"
            ),
        )

    @staticmethod
    def create_sentiment_analysis_task(
        agent: Agent,
        ticker: str,
        context: dict[str, Any],
    ) -> Task:
        """Create sentiment analysis task.

        Args:
            agent: Sentiment analyst agent
            ticker: Stock ticker symbol
            context: Additional context including news data

        Returns:
            Configured Task object
        """
        return Task(
            description=(
                f"Analyze sentiment and news for {ticker}.\n"
                f"\n"
                f"Process recent news (last 7 days):\n"
                f"1. Classify articles by category (earnings, regulatory, product, competitive, macro)\n"
                f"2. Assess sentiment (positive, negative, neutral)\n"
                f"3. Evaluate importance and potential market impact\n"
                f"4. Extract key themes and events\n"
                f"\n"
                f"Assess:\n"
                f"1. Overall sentiment trend\n"
                f"2. Key catalysts and their implications\n"
                f"3. Analyst sentiment (if available)\n"
                f"4. Analyst rating changes\n"
                f"\n"
                f"Provide sentiment score (0-100) and narrative."
            ),
            agent=agent,
            expected_output=(
                "Sentiment analysis with key news items, sentiment classification, "
                "impact assessment, and sentiment score (0-100)"
            ),
        )

    @staticmethod
    def create_signal_synthesis_task(
        agent: Agent,
        ticker: str,
        technical_analysis: dict[str, Any],
        fundamental_analysis: dict[str, Any],
        sentiment_analysis: dict[str, Any],
    ) -> Task:
        """Create signal synthesis task.

        Args:
            agent: Signal synthesizer agent
            ticker: Stock ticker symbol
            technical_analysis: Technical analysis results
            fundamental_analysis: Fundamental analysis results
            sentiment_analysis: Sentiment analysis results

        Returns:
            Configured Task object
        """
        return Task(
            description=(
                f"Synthesize all analyses for {ticker} into investment signal.\n"
                f"\n"
                f"Technical Analysis Results:\n"
                f"{technical_analysis}\n"
                f"\n"
                f"Fundamental Analysis Results:\n"
                f"{fundamental_analysis}\n"
                f"\n"
                f"Sentiment Analysis Results:\n"
                f"{sentiment_analysis}\n"
                f"\n"
                f"Synthesize into:\n"
                f"1. Combined investment score (apply weights: fundamental 35%, technical 35%, sentiment 30%)\n"
                f"2. Clear recommendation (Buy, Hold, Avoid)\n"
                f"3. Confidence assessment (0-100%)\n"
                f"4. Key investment thesis\n"
                f"5. Risk factors\n"
                f"6. Time horizon\n"
                f"7. Expected return range\n"
            ),
            agent=agent,
            expected_output=(
                "Investment signal with combined score, recommendation, confidence, thesis, risks, "
                "time horizon, and expected return"
            ),
        )
