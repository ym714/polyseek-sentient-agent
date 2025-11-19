# Polyseek Sentient Agent - Quick Start Guide

## Installation

```bash
pip install -r requirements.txt
pip install sentient-agent-framework
```

## Environment Setup

Set required environment variables:

```bash
# LLM API Key (required)
export GOOGLE_API_KEY="your-key"
# or
export POLYSEEK_LLM_API_KEY="your-key"
# or
export OPENROUTER_API_KEY="your-key"

# News API (optional, but recommended)
export NEWS_API_KEY="your-key"

# Kalshi API (optional, for Kalshi markets)
export KALSHI_API_KEY="your-key"
export KALSHI_API_SECRET="your-secret"

# X/Twitter API (optional)
export X_BEARER_TOKEN="your-token"

# Reddit API (optional)
export REDDIT_CLIENT_ID="your-id"
export REDDIT_CLIENT_SECRET="your-secret"
```

## Basic Usage

### Method 1: Using Scripts (Recommended)

```bash
cd /Users/motoki/projects/polyseek_sentient

# Quick mode (default, ~30 seconds)
./scripts/run_simple.sh "https://polymarket.com/event/your-market-slug"

# Deep mode (~120 seconds)
./scripts/run_simple.sh "https://polymarket.com/event/your-market-slug" deep neutral

# Devil's Advocate perspective
./scripts/run_simple.sh "https://polymarket.com/event/your-market-slug" quick devils_advocate
```

### Method 2: Python CLI

```bash
export PYTHONPATH="src:$PYTHONPATH"
python -m polyseek_sentient.main "https://polymarket.com/event/your-market-slug" --depth quick --perspective neutral
```

### Method 3: Programmatic Usage

```python
from polyseek_sentient import PolyseekSentientAgent
from sentient_agent_framework import Session, Query, ResponseHandler
import json
import asyncio

agent = PolyseekSentientAgent()

async def analyze_market(market_url: str):
    session = Session(id="user-session")
    query = Query(prompt=json.dumps({
        "market_url": market_url,
        "depth": "quick",  # or "deep"
        "perspective": "neutral"  # or "devils_advocate"
    }))
    
    class MyHandler(ResponseHandler):
        async def emit_json(self, event_name, data):
            print(f"[{event_name}]", json.dumps(data, indent=2))
        async def emit_text_block(self, event_name, content):
            print(f"[{event_name}] {content}")
        def create_text_stream(self, event_name):
            return self
        async def emit_chunk(self, chunk):
            print(chunk, end='')
        async def complete(self):
            print()
    
    await agent.assist(session, query, MyHandler())

# Run
asyncio.run(analyze_market("https://polymarket.com/event/your-market-slug"))
```

## Modes

### Quick Mode (~30 seconds)
- Single-pass LLM analysis
- Fast response time
- Good for rapid decision-making

### Deep Mode (~120 seconds)
- 4-step analysis: Planner → Critic → Follow-up → Final
- More comprehensive analysis
- Better for important decisions

### Perspectives

- **neutral**: Standard analysis
- **devils_advocate**: Forces consideration of counter-arguments

## Output Format

The agent returns structured JSON + Markdown:

```json
{
  "verdict": "YES|NO|UNCERTAIN",
  "confidence_pct": 0-100,
  "summary": "...",
  "key_drivers": [
    {
      "text": "...",
      "source_ids": ["SRC1", "SRC2"]
    }
  ],
  "uncertainty_factors": ["..."],
  "sources": [
    {
      "id": "SRC1",
      "title": "...",
      "url": "...",
      "type": "market|comment|sns|news",
      "sentiment": "pro|con|neutral"
    }
  ]
}
```

## Examples

### Example 1: NVIDIA Earnings Market
```bash
./scripts/run_simple.sh "https://polymarket.com/event/nvda-quarterly-earnings-nongaap-eps-11-19-2025-1pt25"
```

### Example 2: Deep Analysis with Devil's Advocate
```bash
./scripts/run_simple.sh "https://polymarket.com/event/your-market-slug" deep devils_advocate
```

## Troubleshooting

### Market Not Found
```
MarketFetchError: No market found for slug 'xxx'
```
→ Verify the URL is correct and points to an actual Polymarket/Kalshi market.

### LLM API Error
```
LLM API call failed
```
→ Check that your API key is correctly set in environment variables.

### Timeout
→ Deep mode takes ~120 seconds. Try quick mode (~30 seconds) for faster results.

## Offline Mode

For testing without network access:

```bash
export POLYSEEK_OFFLINE=1
python -m polyseek_sentient.main "https://polymarket.com/event/test"
```

## Next Steps

- See `DEEP_MODE_GUIDE.md` for detailed deep mode usage
- See `HOW_IT_WORKS.md` for architecture details
- See `API_SETUP.md` for API configuration details
- See `UPGRADE_PLAN.md` for enhancement options
