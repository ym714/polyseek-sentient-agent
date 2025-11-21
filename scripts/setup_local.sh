#!/bin/bash
# Setup script for local development

cd "$(dirname "$0")/.."

echo "Setting up Polyseek Sentient for local development..."
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a .env file in the project root with your API keys:"
echo "   POLYSEEK_LLM_API_KEY=your-api-key"
echo "   LITELLM_MODEL_ID=openrouter/google/gemini-2.0-flash-001"
echo "   (Optional) NEWS_API_KEY=your-news-api-key"
echo ""
echo "2. Start the backend server:"
echo "   ./scripts/run_local.sh"
echo ""
echo "3. Open frontend/index.html in your browser, or use a local server:"
echo "   cd frontend && python3 -m http.server 3000"
echo "   Then open http://localhost:3000"
echo ""

