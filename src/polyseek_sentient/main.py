"""Entry point for the Polyseek Sentient agent."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from dataclasses import dataclass
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:  # pragma: no cover - optional dependency
    from sentient_agent_framework import AbstractAgent, Query, ResponseHandler, Session
except ImportError:  # pragma: no cover
    class AbstractAgent:  # type: ignore
        async def assist(self, session, query, response_handler):
            raise RuntimeError("Sentient Agent Framework not installed")

    class Session:  # type: ignore
        ...

    class Query:  # type: ignore
        def __init__(self, prompt: str):
            self.prompt = prompt

    class ResponseHandler:  # type: ignore
        async def emit_text_block(self, event_name: str, content: str):
            print(f"[{event_name}] {content}")

        async def emit_json(self, event_name: str, data: dict):
            print(f"[{event_name}] {json.dumps(data, indent=2, ensure_ascii=False)}")

        def create_text_stream(self, event_name: str):
            return self

        async def emit_chunk(self, chunk: str):
            print(chunk)

        async def complete(self):
            print("[COMPLETE]")


class CLIResponseHandler:
    """Simple handler for local CLI runs without Sentient stack."""

    async def emit_text_block(self, event_name: str, content: str):
        print(f"[{event_name}] {content}")

    async def emit_json(self, event_name: str, data: dict):
        print(f"[{event_name}] {json.dumps(data, indent=2, ensure_ascii=False)}")

    def create_text_stream(self, event_name: str):
        return _CLIStream(event_name)

    async def complete(self):
        print("[COMPLETE]")


class _CLIStream:
    def __init__(self, name: str):
        self.name = name

    async def emit_chunk(self, chunk: str):
        print(f"[{self.name}] {chunk}")

    async def complete(self):
        print(f"[{self.name}] (end)")


from .analysis_agent import AnalysisRequest, run_analysis
from .config import Settings, load_settings
from .fetch_market import MarketData, fetch_market_data
from .report_formatter import format_response
from .scrape_context import fetch_market_context
from .signals_client import gather_signals


@dataclass
class AgentInput:
    market_url: str
    depth: str = "quick"
    perspective: str = "neutral"


class PolyseekSentientAgent(AbstractAgent):
    """Sentient-compatible agent implementation."""

    def __init__(self, settings: Optional[Settings] = None):
        super().__init__(name="Polyseek Sentient Agent")
        self.settings = settings or load_settings()

    async def assist(self, session: Session, query: Query, response_handler: ResponseHandler):
        payload = _parse_prompt(query.prompt)
        await response_handler.emit_text_block("RECEIVED", f"Analyzing {payload.market_url}")

        market = await fetch_market_data(payload.market_url, self.settings)
        await response_handler.emit_json(
            "MARKET_METADATA",
            {
                "title": market.title,
                "deadline": str(market.deadline),
                "prices": {"yes": market.prices.yes, "no": market.prices.no},
            },
        )

        context = await fetch_market_context(payload.market_url, self.settings)
        signals = await gather_signals(market, self.settings)
        
        if payload.depth == "deep":
            await response_handler.emit_text_block("DEEP_MODE", "Starting deep analysis (Planner → Critic → Follow-up → Final)")

        analysis_payload = await run_analysis(
            AnalysisRequest(
                market=market,
                context=context,
                signals=signals,
                depth=payload.depth,
                perspective=payload.perspective,
            ),
            self.settings,
        )

        model, markdown = format_response(analysis_payload)
        await response_handler.emit_json("ANALYSIS_JSON", model.model_dump())
        stream = response_handler.create_text_stream("ANALYSIS_MARKDOWN")
        await stream.emit_chunk(markdown)
        await stream.complete()
        await response_handler.complete()


def _parse_prompt(prompt: str) -> AgentInput:
    try:
        data = json.loads(prompt)
        return AgentInput(
            market_url=data["market_url"],
            depth=data.get("depth", "quick"),
            perspective=data.get("perspective", "neutral"),
        )
    except (json.JSONDecodeError, KeyError):
        return AgentInput(market_url=prompt.strip())


async def _run_cli(url: str, depth: str, perspective: str):
    agent = PolyseekSentientAgent()
    handler = CLIResponseHandler()
    payload = json.dumps({"market_url": url, "depth": depth, "perspective": perspective})

    class _SimpleQuery:
        def __init__(self, prompt: str):
            self.prompt = prompt

    class _SimpleSession:
        id = "cli-session"

    query = _SimpleQuery(prompt=payload)
    await agent.assist(_SimpleSession(), query, handler)


def main():
    parser = argparse.ArgumentParser(description="Polyseek Sentient agent demo CLI")
    parser.add_argument("market_url")
    parser.add_argument("--depth", default="quick", choices=("quick", "deep"))
    parser.add_argument("--perspective", default="neutral", choices=("neutral", "devils_advocate"))
    args = parser.parse_args()
    asyncio.run(_run_cli(args.market_url, args.depth, args.perspective))


# ==========================================
# FastAPI Application
# ==========================================

app = FastAPI(title="Polyseek Sentient API")

import os

# CORS configuration: Get from environment variable in production, allow all in development
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    market_url: str
    depth: str = "quick"
    perspective: str = "neutral"


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/trending")
async def get_trending():
    """Return mock trending markets for the frontend."""
    return [
        {
            "id": 1,
            "title": "Will Bitcoin hit $100k in 2024?",
            "price": "0.65",
            "volume": "$12M",
            "url": "https://polymarket.com/event/will-bitcoin-hit-100k-in-2024",
        },
        {
            "id": 2,
            "title": "Russia x Ukraine Ceasefire in 2025?",
            "price": "0.15",
            "volume": "$5M",
            "url": "https://polymarket.com/event/russia-x-ukraine-ceasefire-in-2025",
        },
        {
            "id": 3,
            "title": "Will AI surpass human performance in coding by 2026?",
            "price": "0.42",
            "volume": "$1.8M",
            "url": "https://polymarket.com/event/ai-coding-2026",
        },
    ]


@app.post("/api/analyze")
async def analyze_market(request: AnalyzeRequest):
    try:
        settings = load_settings()
        
        # Check for common configuration issues
        if not settings.llm.api_key:
            raise HTTPException(
                status_code=500,
                detail="LLM API key not configured. Please set POLYSEEK_LLM_API_KEY, OPENROUTER_API_KEY, or OPENAI_API_KEY environment variable."
            )
        
        # 1. Fetch Market Data
        try:
            market = await fetch_market_data(request.market_url, settings)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch market data: {str(e)}"
            )
        
        # 2. Fetch Context
        try:
            context = await fetch_market_context(request.market_url, settings)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch market context: {str(e)}"
            )
        
        # 3. Gather Signals
        try:
            signals = await gather_signals(market, settings)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to gather signals: {str(e)}"
            )
        
        # 4. Run Analysis
        try:
            analysis_payload = await run_analysis(
                AnalysisRequest(
                    market=market,
                    context=context,
                    signals=signals,
                    depth=request.depth,
                    perspective=request.perspective,
                ),
                settings,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {str(e)}"
            )
        
        # 5. Format Response
        try:
            model, markdown = format_response(analysis_payload)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to format response: {str(e)}"
            )
        
        # Construct response matching frontend expectation
        return {
            "markdown": markdown,
            "json": model.model_dump()
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_message = str(e)
        print(f"Unexpected error in /api/analyze: {error_message}")
        print(f"Traceback: {error_trace}")
        # Log to stderr for Vercel logs
        import sys
        print(f"Error: {error_message}", file=sys.stderr)
        print(f"Traceback: {error_trace}", file=sys.stderr)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {error_message}"
        )


if __name__ == "__main__":
    main()
