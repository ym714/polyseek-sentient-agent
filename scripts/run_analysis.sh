#!/bin/bash
# Polyseek execution script

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults only if not already set
export LITELLM_MODEL_ID="${LITELLM_MODEL_ID:-gemini/gemini-2.0-flash-001}"

# Path configuration
export PYTHONPATH="src:$PYTHONPATH"

# Argument check
if [ $# -eq 0 ]; then
    echo "Usage: $0 <Polymarket-market-URL> [depth] [perspective]"
    echo ""
    echo "Examples:"
    echo "  $0 'https://polymarket.com/event/nvda-quarterly-earnings-nongaap-eps-11-19-2025-1pt25'"
    echo "  $0 'https://polymarket.com/event/...' quick neutral"
    echo "  $0 'https://polymarket.com/event/...' deep devils_advocate"
    echo ""
    echo "depth: quick (~30s) or deep (~120s) - default: quick"
    echo "perspective: neutral or devils_advocate - default: neutral"
    exit 1
fi

URL="$1"
DEPTH="${2:-quick}"
PERSPPECTIVE="${3:-neutral}"

cd "$(dirname "$0")"

python3 -c "
import sys
sys.path.insert(0, 'src')
from polyseek_sentient.config import Settings, LLMSettings, APISettings
import os
from polyseek_sentient.main import PolyseekSentientAgent
from sentient_agent_framework import Session, Query, ResponseHandler
import asyncio
import json

# Create custom settings
settings = Settings(
    apis=APISettings(news_api_key=os.getenv('NEWS_API_KEY')),
    llm=LLMSettings(
        model=os.getenv('LITELLM_MODEL_ID', 'gemini/gemini-2.0-flash-001'),
        api_key=os.getenv('GOOGLE_API_KEY') or os.getenv('POLYSEEK_LLM_API_KEY')
    )
)

class CLIResponseHandler:
    async def emit_text_block(self, event_name, content):
        print(f'[{event_name}] {content}')
    async def emit_json(self, event_name, data):
        print(f'[{event_name}]', json.dumps(data, indent=2, ensure_ascii=False))
    def create_text_stream(self, event_name):
        return self
    async def emit_chunk(self, chunk):
        print(chunk, end='')
    async def complete(self):
        print()

class SimpleQuery:
    def __init__(self, prompt):
        self.prompt = prompt

class SimpleSession:
    id = 'cli-session'

agent = PolyseekSentientAgent(settings=settings)
query = SimpleQuery(prompt=json.dumps({
    'market_url': '$URL',
    'depth': '$DEPTH',
    'perspective': '$PERSPPECTIVE'
}))
session = SimpleSession()
handler = CLIResponseHandler()

asyncio.run(agent.assist(session, query, handler))
"

