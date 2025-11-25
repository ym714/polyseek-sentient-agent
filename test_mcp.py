#!/usr/bin/env python3
"""Test script for Polyseek MCP server."""

import asyncio
import sys

try:
    from src.polyseek.main import PolyseekAgent
except ImportError as e:
    print(f"Error: {e}")
    print("Make sure sentient-agent-framework is installed:")
    print("  pip install sentient-agent-framework")
    sys.exit(1)


class TestResponseHandler:
    """Simple response handler for testing."""
    
    async def emit_text_block(self, event_name: str, content: str):
        print(f"📝 [{event_name}] {content}")
    
    async def emit_json(self, event_name: str, data: dict):
        print(f"📊 [{event_name}]")
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
    
    def create_text_stream(self, event_name: str):
        return TestStream(event_name)
    
    async def complete(self):
        print("✅ [COMPLETE] Response finished")


class TestStream:
    def __init__(self, name: str):
        self.name = name
        print(f"📡 [{self.name}] Stream started")
    
    async def emit_chunk(self, chunk: str):
        print(chunk, end='', flush=True)
    
    async def complete(self):
        print(f"\n✅ [{self.name}] Stream complete")


async def test_mcp_agent():
    """Test the Polyseek MCP agent."""
    
    print("🚀 Starting Polyseek MCP Agent Test\n")
    
    # Create agent
    agent = PolyseekAgent()
    print(f"✅ Agent created: {agent.name}\n")
    
    # Create test session and query using simple classes
    class TestSession:
        def __init__(self, session_id: str):
            self.id = session_id
    
    class TestQuery:
        def __init__(self, prompt: str):
            self.prompt = prompt
    
    session = TestSession("test-session-123")
    query = TestQuery('{"market_url": "https://polymarket.com/event/russia-x-ukraine-ceasefire-in-2025?tid=1764099903364", "depth": "quick"}')
    
    print(f"📨 Query: {query.prompt}\n")
    print("=" * 60)
    
    # Create response handler
    handler = TestResponseHandler()
    
    # Run the agent
    try:
        await agent.assist(session, query, handler)
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("Polyseek MCP Agent Test")
    print("=" * 60 + "\n")
    
    success = asyncio.run(test_mcp_agent())
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed")
        sys.exit(1)
