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

### Local Development (Web UI)

1. **Setup**:
   ```bash
   ./scripts/setup_local.sh
   ```

2. **Create `.env` file** in the project root:
   ```bash
   POLYSEEK_LLM_API_KEY=your-api-key
   LITELLM_MODEL_ID=openrouter/google/gemini-2.0-flash-001
   # Optional:
   NEWS_API_KEY=your-news-api-key
   ```

3. **Start the backend server**:
   ```bash
   ./scripts/run_local.sh
   ```
   The API will be available at `http://localhost:8000`

4. **Open the frontend**:
   - Option 1: Open `frontend/index.html` directly in your browser
   - Option 2: Use a local HTTP server:
     ```bash
     cd frontend && python3 -m http.server 3000
     ```
     Then open `http://localhost:3000`

### CLI Usage

1. Install deps: `pip install -r requirements.txt`
2. Set up environment variables (same as above)
3. Run the demo CLI:
   ```bash
   python -m polyseek_sentient.main "https://polymarket.com/event/..."
   ```
   Or use the convenience script:
   ```bash
   ./scripts/run_simple.sh "https://polymarket.com/event/..."
   ```

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
