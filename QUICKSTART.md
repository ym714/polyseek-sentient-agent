# QuestFlow MCP Agent - Quick Start Guide

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Install Sentient Agent Framework:**
   ```bash
   pip install sentient-agent-framework
   ```

## Running QuestFlow

### Option 1: MCP Server Mode (Recommended)

Start QuestFlow as an MCP/SSE server:

```bash
./start_mcp_server.sh
```

Or manually:

```bash
python -m src.questflow.main --mcp-server
```

The server will be available at:
- **MCP/SSE Endpoint**: `http://localhost:8000/assist`
- **REST API**: `http://localhost:8000/api/analyze`
- **Health Check**: `http://localhost:8000/api/health`

### Option 2: CLI Mode

Run analysis directly from command line:

```bash
python -m src.questflow.main "https://polymarket.com/event/..." --depth quick
```

### Option 3: FastAPI Development Server

Run as a standard FastAPI application:

```bash
uvicorn src.questflow.main:app --reload --host 0.0.0.0 --port 8000
```

## MCP Client Configuration

To connect QuestFlow to an MCP client (like Sentient Chat):

```
Agent Name: questflow
Description: AI-powered workflow and task analysis agent
MCP Server URL: http://localhost:8000/assist
Type: SSE
Authentication: None
```

## API Usage

### REST API Example

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "market_url": "https://polymarket.com/event/...",
    "depth": "quick",
    "perspective": "neutral"
  }'
```

### Response Format

```json
{
  "markdown": "# Analysis Report\n...",
  "json": {
    "verdict": "YES",
    "confidence_pct": 75.0,
    "summary": "...",
    "key_drivers": [...],
    "uncertainty_factors": [...],
    "sources": [...]
  }
}
```

## Deployment

### Vercel

The project is configured for Vercel deployment:

```bash
vercel deploy
```

### Docker

Build and run with Docker:

```bash
docker build -t questflow .
docker run -p 8000:8000 --env-file .env questflow
```

## Troubleshooting

### MCP Server Not Starting

- Ensure `sentient-agent-framework` is installed
- Check that port 8000 is not in use
- Verify API keys in `.env` file

### Import Errors

If you see import errors, ensure you're running from the project root:

```bash
cd /Users/motoki/projects/questflow
python -m src.questflow.main --mcp-server
```

## Next Steps

- See `docs/` for detailed documentation
- Check `README.md` for project overview
- Review `src/questflow/main.py` for customization options
