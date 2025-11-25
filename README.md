# Polyseek MCP Agent

**AI-powered prediction market analysis agent compatible with Model Context Protocol (MCP).**

Polyseek is an MCP-compatible AI agent that analyzes prediction markets on Polymarket and Kalshi by aggregating data from multiple sources and synthesizing insights through LLM-driven analysis.

## Key Features
- ✅ MCP (Model Context Protocol) compatible
- ✅ Sentient Agent Framework integration  
- ✅ Multi-source data aggregation (APIs, news, social media)
- ✅ LLM-powered analysis with structured outputs
- ✅ REST API and SSE endpoints
- ✅ Quick and Deep analysis modes

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install sentient-agent-framework
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Start MCP Server
```bash
./start_mcp_server.sh
```

Server endpoints:
- **MCP/SSE**: `http://localhost:8000/assist`
- **REST API**: `http://localhost:8000/api/analyze`
- **Health**: `http://localhost:8000/api/health`

## MCP Client Configuration

```
Agent Name: polyseek
Description: AI-powered prediction market analysis agent
MCP Server URL: http://localhost:8000/assist
Type: SSE
Authentication: None
```

## Usage

### CLI Mode
```bash
python -m src.polyseek.main "https://polymarket.com/event/..." --depth quick
```

### REST API
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "market_url": "https://polymarket.com/event/...",
    "depth": "quick",
    "perspective": "neutral"
  }'
```

## Documentation

See `QUICKSTART.md` for detailed setup instructions.

## Project Structure
```
polyseek/
├── src/polyseek/          # Main agent code
│   ├── main.py           # Entry point with MCP server
│   ├── analysis_agent.py # LLM analysis
│   └── ...
├── api/index.py          # Vercel entry point
└── start_mcp_server.sh   # MCP server startup
```
