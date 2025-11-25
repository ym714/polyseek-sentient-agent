# QuestFlow MCP Agent - Setup Summary

## ✅ What Was Created

QuestFlow is a complete copy of polyseek_sentient, rebranded and enhanced for MCP (Model Context Protocol) compatibility.

### Key Changes:

1. **Module Renamed**: `polyseek_sentient` → `questflow`
2. **Agent Class**: `PolyseekSentientAgent` → `QuestFlowAgent`
3. **MCP Support**: Added `DefaultServer` integration for SSE endpoint at `/assist`
4. **Branding**: Updated all references to "QuestFlow"

## 📁 Project Structure

```
questflow/
├── src/questflow/          # Main agent code
│   ├── main.py            # Entry point with MCP server support
│   ├── config.py          # Configuration
│   ├── analysis_agent.py  # LLM analysis
│   └── ...
├── api/index.py           # Vercel entry point
├── start_mcp_server.sh    # MCP server startup script
├── README.md              # Project overview
├── QUICKSTART.md          # Quick start guide
└── .env.example           # Environment template
```

## 🚀 How to Use

### 1. MCP Server Mode (Recommended)

```bash
cd /Users/motoki/projects/questflow
./start_mcp_server.sh
```

Server will be available at:
- **MCP/SSE**: `http://localhost:8000/assist`
- **REST API**: `http://localhost:8000/api/analyze`

### 2. MCP Client Configuration

```
Agent Name: questflow
Description: AI-powered workflow and task analysis agent
MCP Server URL: http://localhost:8000/assist
Type: SSE
Authentication: None
```

## 📝 Next Steps

1. Copy `.env` from polyseek_sentient or configure new API keys
2. Install dependencies: `pip install -r requirements.txt`
3. Install Sentient Agent Framework: `pip install sentient-agent-framework`
4. Start the MCP server: `./start_mcp_server.sh`
5. Connect from your MCP client

## 🔧 Customization

To customize QuestFlow for your specific use case:

1. **Modify Analysis Logic**: Edit `src/questflow/analysis_agent.py`
2. **Change Data Sources**: Update `src/questflow/signals_client.py`
3. **Adjust API**: Modify `src/questflow/main.py`

See `QUICKSTART.md` for detailed instructions.
