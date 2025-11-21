#!/bin/bash
# Local development server script

cd "$(dirname "$0")/.."

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set PYTHONPATH
export PYTHONPATH="src:$PYTHONPATH"

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Starting Polyseek Sentient API server..."
echo "API will be available at: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the FastAPI server
uvicorn src.polyseek_sentient.main:app --host 0.0.0.0 --port 8000 --reload

