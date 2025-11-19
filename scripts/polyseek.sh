#!/bin/bash
# Polyseek CLI wrapper script

cd "$(dirname "$0")/.."
export PYTHONPATH="src:$PYTHONPATH"

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults only if not already set
export LITELLM_MODEL_ID="${LITELLM_MODEL_ID:-gemini/gemini-2.0-flash-001}"

# Check for offline mode
if [ "$1" = "--offline" ]; then
    export POLYSEEK_OFFLINE=1
    shift
fi

# Check for market URL
if [ -z "$1" ]; then
    echo "Usage: $0 [--offline] <market_url> [--depth quick|deep] [--perspective neutral|devils_advocate]"
    echo ""
    echo "Examples:"
    echo "  $0 'https://polymarket.com/event/your-market-slug'"
    echo "  $0 'https://polymarket.com/event/your-market-slug' --depth deep"
    echo "  $0 'https://polymarket.com/event/your-market-slug' --perspective devils_advocate"
    echo "  $0 --offline 'https://polymarket.com/event/test'"
    exit 1
fi

python3 -m polyseek_sentient.main "$@"
