# About NordInvest

NordInvest is an AI-powered financial analysis system that combines:

## 🤖 Hybrid Intelligence

- **Rule-Based Analysis**: Traditional technical indicators (RSI, MACD, Bollinger Bands, etc.)
- **LLM-Powered Insights**: Advanced reasoning using Claude/GPT for market interpretation
- **Multi-Factor Scoring**: Comprehensive evaluation across technical, fundamental, and sentiment dimensions

## 🎯 Analysis Methodology

### 1. Market Scanning
Pre-filter tickers using configurable strategies:
- Anomaly detection for unusual price/volume patterns
- Volume pattern analysis
- Momentum tracking
- Volatility screening

### 2. Deep Analysis
Comprehensive evaluation of selected instruments:
- **Technical Analysis**: 21+ indicators including RSI, MACD, Bollinger Bands, ADX, Stochastic, Ichimoku Cloud
- **Fundamental Analysis**: Financial metrics, earnings, analyst ratings
- **Sentiment Analysis**: News sentiment using FinBERT transformer model

### 3. Signal Generation
Multi-factor scoring produces investment signals:
- **STRONG_BUY**: High conviction opportunities (85%+ confidence)
- **BUY**: Good opportunities (70-85% confidence)
- **HOLD**: Neutral or mixed signals (50-70% confidence)
- **AVOID**: Weak or negative signals (<50% confidence)

## 🔒 Privacy

This public website does **NOT** contain:
- Portfolio allocations
- Watchlist recommendations
- Personal trading positions
- Suggested position sizes

Only analysis insights and signals are published.

## 📊 Performance Tracking

Recommendations are tracked over time to validate:
- Return accuracy
- Win rate
- Alpha vs benchmark
- Confidence calibration

## 🛠️ Technology Stack

- **Backend**: Python 3.12+
- **AI Framework**: CrewAI with Claude/GPT integration
- **Data Sources**: Yahoo Finance, Finnhub
- **Database**: SQLite
- **Website**: MkDocs + Material theme
- **Hosting**: GitHub Pages

## 📝 License & Disclaimers

### Investment Disclaimer

!!! danger "Important"
    This analysis is for informational purposes only and does not constitute investment advice. All investments carry risk, including potential loss of principal. Past performance does not guarantee future results. Market conditions can change rapidly; signals may become outdated.

    **Always:**
    - Consult with a qualified financial advisor
    - Do your own research
    - Understand the risks before investing
    - Never invest more than you can afford to lose

### Data Disclaimer

Data is provided by third-party sources (Yahoo Finance, Finnhub) and may contain errors or delays. The analysis represents the system's assessment at a specific point in time and should not be the sole basis for investment decisions.

## 🔗 Links

- [GitHub Repository](https://github.com/ironcladgeek/NordInvest)
- [View Latest Reports](reports/)
- [Browse Tickers](tickers/)

---

*Built with ❤️ using Python, CrewAI, and MkDocs Material*
