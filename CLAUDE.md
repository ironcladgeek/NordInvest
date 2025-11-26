# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**NordInvest** is an AI-powered financial analysis and investment recommendation system that generates daily investment signals and portfolio allocation suggestions. It uses a multi-agent CrewAI architecture to analyze Nordic and European financial markets across fundamental, technical, and sentiment dimensions.

**Key characteristics:**
- Cost-conscious design: Target €50-90/month operational cost
- Multi-agent AI orchestration using CrewAI
- Runs once daily, completing analysis in <15 minutes
- Outputs: Markdown reports, JSON signals, portfolio recommendations
- Early-stage project: Foundation infrastructure complete, source code implementation in progress

## Essential Commands

### Development Workflow

```bash
# Install dependencies
uv sync

# Format and lint code (run before committing)
uv run poe lint

# Run all pre-commit hooks manually
uv run poe pre-commit

# Run tests
pytest

# Run single test file
pytest tests/path/to/test_file.py

# Run tests with specific pattern
pytest -k "test_pattern_name"
```

### Project Configuration

```bash
# Environment variables required
export ANTHROPIC_API_KEY=your_key        # For Claude API
export FINNHUB_API_KEY=your_key          # For news/sentiment data
export OPENAI_API_KEY=your_key           # Alternative LLM (optional)

# Create local config from template
cp config/default.yaml config/local.yaml
# Edit config/local.yaml with your preferences
```

## Architecture Overview

### High-Level System Design

```
Configuration Layer (YAML/CLI)
    ↓
Data Fetching (Multiple APIs + Caching)
    ↓
CrewAI Multi-Agent System
    ├─ Market Scanner Agent (anomaly detection, screening)
    ├─ Fundamental Analysis Agent (earnings, valuations, growth)
    ├─ Technical Analysis Agent (indicators: SMA, RSI, MACD, ATR)
    ├─ News & Sentiment Agent (news processing, sentiment scoring)
    └─ Signal Synthesis Agent (weighted scoring + confidence)
    ↓
Report Generation (Markdown/JSON)
    ↓
Output (Files, Email, Terminal)
```

### Core Components

**1. Agent System (src/agents/)**
- Each agent has a specific role with defined goal, backstory, and tools
- Agents collaborate through CrewAI Crew orchestration
- Five agents: Market Scanner, Fundamental Analysis, Technical Analysis, News/Sentiment, Signal Synthesis, Report Generator

**2. Data Layer (src/data/)**
- Abstract `DataProvider` interface for pluggable API sources
- Implementations: Yahoo Finance (primary), Alpha Vantage (backup), Finnhub (news/sentiment)
- Normalization pipeline converts raw API data to standardized Pydantic models

**3. Caching System (src/cache/)**
- File-based cache with JSON (structured data) and Parquet (time-series)
- Configurable TTL per data type:
  - Price data: 1h (market hours), 24h (overnight)
  - News: 4h
  - Fundamentals: 24h
  - Financial statements: 7 days
- Minimizes API calls and costs

**4. Analysis Modules (src/analysis/)**
- Technical Analysis: Moving averages, RSI, MACD, ATR, volume analysis
- Fundamental Analysis: Earnings growth, margins, debt ratios, valuation metrics
- Signal Synthesis: Multi-factor scoring (35% fundamental, 35% technical, 30% sentiment)

**5. Configuration System (src/config/)**
- YAML-based configuration for market preferences, risk tolerance, capital settings
- Environment variable support for API credentials
- Validation through Pydantic schemas

### Signal Scoring Methodology

**Confidence-Scored Recommendations:**
- **Buy**: Combined score > 70, confidence > 60%
- **Hold**: Combined score 40-70
- **Avoid**: Combined score < 40 or high-risk flags

**Scoring weights:**
- Fundamental score: 35% (earnings, valuations, financial health)
- Technical score: 35% (trend indicators, momentum)
- Sentiment score: 30% (news tone, analyst ratings)

**Confidence calculation:**
- Based on agreement across factors
- Data quality assessment
- Historical accuracy tracking (Phase 5+)

## Code Organization

```
NordInvest/
├── src/
│   ├── agents/           # CrewAI agent definitions
│   ├── tools/            # Custom CrewAI tools for agents
│   ├── data/             # Data providers and fetching logic
│   ├── analysis/         # Technical & fundamental analysis modules
│   ├── cache/            # Caching layer (JSON, Parquet)
│   ├── config/           # Configuration system and schemas
│   ├── reports/          # Report generation and formatting
│   └── utils/            # Shared utilities
├── config/
│   ├── default.yaml      # Default configuration template
│   └── local.yaml        # User-specific config (git-ignored)
├── data/
│   ├── cache/            # API response cache (git-ignored)
│   ├── features/         # Preprocessed feature data
│   └── reports/          # Generated daily reports
├── tests/                # Test suite
├── pyproject.toml        # Project metadata, dependencies, tool configs
├── uv.lock               # Dependency lock file
├── .pre-commit-config.yaml  # Git hooks for code quality
└── docs/
    ├── architecture.mermaid  # System architecture diagram
    └── roadmap.md            # Implementation roadmap (5 phases)
```

## Key Development Patterns

### Creating New Agents

1. Create agent class in `src/agents/`
2. Define role, goal, backstory using clear job descriptions
3. Assign custom tools from `src/tools/`
4. Register in CrewAI Crew (`src/main.py`)

### Adding Data Providers

1. Extend `DataProvider` abstract base class
2. Implement `fetch()` and `validate()` methods
3. Return Pydantic data models
4. Register in provider factory for automatic selection

### Implementing Analysis Functions

1. Create module in `src/analysis/`
2. Accept standardized data models (Pydantic validated)
3. Return scoring dictionaries with confidence levels
4. Include explanations/reasoning for transparency

### Caching Strategy

- All API responses should go through cache layer
- Use appropriate TTL based on data freshness requirements
- Cache keys should be deterministic (symbol, date, etc.)
- Monitor cache hit rates for optimization

## Dependency and Tool Information

### Core Dependencies
- **CrewAI**: Multi-agent AI orchestration framework
- **Pydantic**: Data validation and schema definition
- **Typer**: CLI interface with type hints
- **PyYAML**: Configuration file parsing
- **Loguru**: Structured logging
- **python-dotenv**: Environment variable management

### Development Tools
- **pytest**: Testing framework
- **Black**: Code formatter (100-char line length)
- **Ruff**: Fast Python linter with import sorting
- **Pre-commit**: Git hooks framework (enforces conventional commits)
- **Poethepoet**: Task runner for development commands
- **UV**: Fast Python package manager (replaces pip/Poetry)

### Code Quality Standards
- **Black formatter**: Line length 100 characters
- **Ruff linter**: Configured with import sorting enabled
- **Conventional commits**: Semantic commit messages enforced (feat:, fix:, docs:, etc.)
- **Pre-commit hooks**: Run automatically on every commit
- No logging f-string interpolation warnings (G004 ignored)

## Development Workflow

### Before Committing

1. Run linting and formatting:
   ```bash
   uv run poe lint
   ```

2. Pre-commit hooks will automatically:
   - Fix trailing whitespace
   - Fix missing newlines
   - Validate YAML/TOML syntax
   - Sort imports with Ruff
   - Format code with Black
   - Validate conventional commit message

3. Commit with semantic message:
   ```bash
   git commit -m "feat: add new analysis agent"
   git commit -m "fix: cache expiration logic"
   git commit -m "docs: update architecture documentation"
   ```

### Running Tests

- Single test file: `pytest tests/unit/agents/test_scanner.py`
- With pattern matching: `pytest -k "test_fundamental_scoring"`
- Full test suite: `pytest` (from project root)

## Implementation Roadmap

The project follows a 5-phase implementation plan (see `docs/roadmap.md`):

| Phase | Timeline | Status | Focus |
|-------|----------|--------|-------|
| Phase 1 | Days 1-2 | ✅ Complete | Foundation, project setup, config system |
| Phase 2 | Days 3-5 | ⏳ Next | Data layer, caching, API integration |
| Phase 3 | Days 6-9 | Pending | CrewAI agents, custom tools |
| Phase 4 | Days 10-12 | Pending | Signal synthesis, reporting |
| Phase 5 | Days 13-14 | Pending | Integration, testing, deployment |

## Cost Control Strategy

The system is designed to maintain €50-90/month operational cost:

- **Aggressive caching**: Minimize repeated API calls (1-24h TTL per data type)
- **Free tier prioritization**: Yahoo Finance as primary data source
- **Batch processing**: Group requests for efficiency
- **Single daily run**: Not continuous execution
- **Token optimization**: Concise LLM prompts and responses

**Cost breakdown:**
- LLM API: €50-70/month
- Financial Data APIs: €0-20/month (free tiers)
- Compute: €0 (local execution)

## Common Troubleshooting

### API Rate Limiting
- Check cache TTL settings in config
- Verify cache is populated from previous runs
- Consider rotating between providers (Yahoo Finance → Alpha Vantage)

### Data Quality Issues
- Check data validation in Pydantic models
- Verify normalization in data processing pipeline
- Review cache for stale data (check TTL settings)

### Test Failures
- Ensure mock data matches expected Pydantic schemas
- Verify API provider mocking in fixtures
- Check cache cleanup between test runs

## Additional Resources

- Full roadmap: `docs/roadmap.md` (detailed 5-phase plan with cost analysis)
- Architecture diagram: `docs/architecture.mermaid` (system components and data flow)
- README: `README.md` (quick overview)
- Config template: `config/default.yaml` (configuration options)
