# API Setup Guide

This guide covers setting up external APIs for Polyseek Sentient Agent.

## Required APIs

### LLM API (Required)

At minimum, you need one LLM API key. Supported providers:

```bash
# Option 1: Google (via LiteLLM)
export GOOGLE_API_KEY="your-key"
export LITELLM_MODEL_ID="gemini/gemini-2.0-flash-001"

# Option 2: OpenRouter
export OPENROUTER_API_KEY="your-key"
export LITELLM_MODEL_ID="openrouter/google/gemini-2.0-flash-001"

# Option 3: OpenAI
export OPENAI_API_KEY="your-key"
export LITELLM_MODEL_ID="gpt-4o"

# Option 4: Generic (via POLYSEEK_LLM_API_KEY)
export POLYSEEK_LLM_API_KEY="your-key"
```

**Get API Keys:**
- Google: https://makersuite.google.com/app/apikey
- OpenRouter: https://openrouter.ai/keys
- OpenAI: https://platform.openai.com/api-keys

## Optional APIs

### News API (Recommended)

**Free Plan:** 100 requests/day

```bash
export NEWS_API_KEY="your-key"
```

**Get API Key:** https://newsapi.org/register

**Benefits:**
- Real-time news articles
- Multiple sources
- Free tier available

### X/Twitter API

**⚠️ Note:** X API free plan is very limited (2024-2025)

**Free Plan Limitations:**
- Very few requests per 15 minutes
- Strict monthly tweet limits
- No commercial use

**Paid Plans:**
- Basic: $100/month
- Pro: $5,000/month

**Setup:**
```bash
export X_BEARER_TOKEN="your-bearer-token"
```

**Get API Key:** https://developer.twitter.com/en/portal/dashboard

**Alternative:** Consider using Reddit API instead (completely free, commercial use allowed)

### Reddit API (Recommended Alternative)

**✅ Completely Free** - Commercial use allowed

**Setup:**
```bash
export REDDIT_CLIENT_ID="your-client-id"
export REDDIT_CLIENT_SECRET="your-client-secret"
export REDDIT_USER_AGENT="polyseek/1.0"
```

**Get API Credentials:**
1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Choose "script" type
4. Copy client_id (under the app name) and client_secret

**Benefits:**
- Completely free
- Commercial use allowed
- Good for community sentiment
- No strict rate limits

### Kalshi API (For Kalshi Markets)

**Required for:** Analyzing Kalshi prediction markets

**Setup:**
```bash
export KALSHI_API_KEY="your-api-key"
export KALSHI_API_SECRET="your-api-secret"
```

**Get API Credentials:** https://trading-api.kalshi.com/trade-api-docs/

**Note:** Kalshi requires authentication. Without credentials, only Polymarket markets can be analyzed.

## RSS Feeds (Fallback)

RSS feeds are used as a fallback when APIs are unavailable. No setup required.

**Note:** Some RSS feeds may have SSL certificate issues. The agent handles these gracefully.

## Configuration Priority

The agent uses APIs in this order:

1. **News API** (if configured)
2. **X/Twitter API** (if configured)
3. **Reddit API** (if configured)
4. **RSS Feeds** (fallback, always available)

## Testing Your Setup

### Test News API
```bash
export NEWS_API_KEY="your-key"
python -m polyseek_sentient.main "https://polymarket.com/event/test" --depth quick
```

### Test Reddit API
```bash
export REDDIT_CLIENT_ID="your-id"
export REDDIT_CLIENT_SECRET="your-secret"
export REDDIT_USER_AGENT="polyseek/1.0"
python -m polyseek_sentient.main "https://polymarket.com/event/test" --depth quick
```

### Test X/Twitter API
```bash
export X_BEARER_TOKEN="your-token"
python -m polyseek_sentient.main "https://polymarket.com/event/test" --depth quick
```

## Troubleshooting

### API Key Not Working
- Verify the key is correctly set: `echo $NEWS_API_KEY`
- Check API key permissions and limits
- Verify the API service is operational

### Rate Limits
- News API free plan: 100 requests/day
- X/Twitter free plan: Very limited
- Reddit API: Generous limits (no strict daily limit)

### SSL Certificate Errors (RSS)
- The agent handles SSL errors gracefully
- RSS feeds fall back automatically if SSL fails

## Recommended Setup

**Minimum (Free):**
- LLM API key (required)
- News API (free tier: 100 requests/day)

**Recommended:**
- LLM API key
- News API
- Reddit API (completely free, better than X/Twitter free tier)

**Full Setup:**
- LLM API key
- News API
- Reddit API
- X/Twitter API (if you have paid plan)
- Kalshi API (if analyzing Kalshi markets)

## Environment Variables Summary

```bash
# Required
export GOOGLE_API_KEY="your-key"  # or OPENROUTER_API_KEY, OPENAI_API_KEY

# Recommended
export NEWS_API_KEY="your-key"
export REDDIT_CLIENT_ID="your-id"
export REDDIT_CLIENT_SECRET="your-secret"
export REDDIT_USER_AGENT="polyseek/1.0"

# Optional
export X_BEARER_TOKEN="your-token"
export KALSHI_API_KEY="your-key"
export KALSHI_API_SECRET="your-secret"

# Model selection
export LITELLM_MODEL_ID="gemini/gemini-2.0-flash-001"
```

