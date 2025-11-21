# Polyseek Sentient Agent (MVP)

**Automated prediction market analysis that transforms 30+ minutes of manual research into 30-120 seconds of structured insights.**

Polyseek is an AI agent that analyzes Polymarket and Kalshi markets by aggregating data from APIs, scraping market context, and synthesizing external signals (news, social media) into actionable verdicts with confidence scores and bias mitigation

## Key Features
- URL-based market detection (Polymarket/Kalshi)
- Resolution rules + comment scraping with BeautifulSoup
- Pluggable signal providers (News API example included)
- Prompt-engineered LLM analysis with Bayesian-style reasoning
- Markdown + JSON output via a strict schema

## Project Layout
```
polyseek_sentient/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── src/
│   └── polyseek_sentient/
│       ├── main.py               # Sentient agent entry point
│       ├── config.py             # settings + env loading
│       ├── fetch_market.py       # official API integration helpers
│       ├── scrape_context.py     # comment/rules extraction utilities
│       ├── signals_client.py     # external signal aggregation
│       ├── analysis_agent.py     # LLM orchestration
│       ├── report_formatter.py   # schema validation + Markdown builder
│       └── tests/
│           └── test_report_formatter.py
├── docs/               # Documentation
└── scripts/            # Utility scripts
```

## Quickstart
1. Install deps: `pip install -r requirements.txt`
2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```
   At minimum you need one LLM key (Google/OpenRouter/OpenAI via LiteLLM). Polymarket access is public, Kalshi requires credentials.
3. Run the demo CLI:
   ```bash
   python -m polyseek_sentient.main "https://polymarket.com/event/..."
   ```
   Or use the convenience script:
   ```bash
   ./scripts/run_simple.sh "https://polymarket.com/event/..."
   ```
4. When embedding inside Sentient Agent Framework, instantiate `PolyseekSentientAgent` and wire it into your server/orchestrator.

## Documentation

See `docs/` directory for detailed documentation:

- **QUICKSTART.md** - Installation and basic usage guide
- **HOW_IT_WORKS.md** - Architecture and implementation details
- **DEEP_MODE_GUIDE.md** - Deep mode usage guide
- **API_SETUP.md** - External API configuration guide
- **UPGRADE_PLAN.md** - Enhancement and upgrade options
- **PRACTICAL_EXPANSIONS.md** - Practical expansion ideas
- **PROBLEM_STATEMENT.md** - Problem statement and solution overview

## Tests
```
pytest src/polyseek_sentient/tests/test_report_formatter.py
```

The test only covers the formatter; extend as you plug real signal providers.
