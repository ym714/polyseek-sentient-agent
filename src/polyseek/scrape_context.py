"""Scrape resolution rules and comment context from market pages."""

from __future__ import annotations

import asyncio
import re
import uuid
from dataclasses import dataclass
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

from .config import Settings, ScrapeSettings, load_settings


@dataclass
class Comment:
    comment_id: str
    author: Optional[str]
    body: str
    language: str
    sentiment: str
    mentions_ratio: float


@dataclass
class MarketContext:
    resolution_rules: Optional[str]
    comments: List[Comment]


async def fetch_market_context(
    url: str,
    settings: Optional[Settings] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> MarketContext:
    """Scrape resolution criteria and comments."""
    settings = settings or load_settings()
    if settings.app.offline_mode:
        return _offline_context()
    html = await _download_html(url, settings, client)
    soup = BeautifulSoup(html, "html.parser")
    rules = _extract_rules(soup)
    comments = _extract_comments(soup, settings.scrape)
    return MarketContext(resolution_rules=rules, comments=comments)


async def _download_html(
    url: str,
    settings: Settings,
    client: Optional[httpx.AsyncClient],
) -> str:
    close_client = client is None
    client = client or httpx.AsyncClient(timeout=settings.scrape.timeout_seconds)
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPError as exc:
        if settings.app.offline_mode:
            return ""
        raise RuntimeError(f"Failed to download market page: {exc}") from exc
    finally:
        if close_client:
            await client.aclose()


def _extract_rules(soup: BeautifulSoup) -> Optional[str]:
    # Common Polymarket layout
    possible = soup.select_one('[data-testid="resolution-criteria"]')
    if possible:
        return possible.get_text(" ", strip=True)
    headers = soup.find_all(["h2", "h3"])
    for header in headers:
        if "resolution" in header.get_text("", strip=True).lower():
            sibling_text = header.find_next("p")
            if sibling_text:
                return sibling_text.get_text(" ", strip=True)
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"]
    return None


def _extract_comments(soup: BeautifulSoup, settings: ScrapeSettings) -> List[Comment]:
    raw_comments: List[Comment] = []
    candidates = soup.select('[data-testid*="comment"], [class*="Comment"]')
    for node in candidates:
        text = node.get_text(" ", strip=True)
        if not text or len(text) < 15:
            continue
        author = None
        author_node = node.find(attrs={"data-testid": re.compile("author", re.I)})
        if author_node:
            author = author_node.get_text(" ", strip=True)
        trimmed = text[:settings.max_comment_chars]
        sentiment = _heuristic_sentiment(trimmed)
        mentions_ratio = _mentions_ratio(trimmed)
        raw_comments.append(
            Comment(
                comment_id=str(uuid.uuid4()),
                author=_anonymize(author),
                body=trimmed,
                language="unknown",
                sentiment=sentiment,
                mentions_ratio=mentions_ratio,
            )
        )
        if len(raw_comments) >= settings.max_comments:
            break
    return raw_comments


def _offline_context() -> MarketContext:
    stub = Comment(
        comment_id="offline-1",
        author="user_offline",
        body="This is offline mode. Replace with real comments when online.",
        language="en",
        sentiment="neutral",
        mentions_ratio=0.0,
    )
    return MarketContext(
        resolution_rules="Offline mode: resolution text unavailable.",
        comments=[stub],
    )


def _heuristic_sentiment(text: str) -> str:
    text_lower = text.lower()
    pro_words = ("yes", "win", "likely", "bull")
    con_words = ("no", "lose", "unlikely", "bear")
    pro_score = sum(word in text_lower for word in pro_words)
    con_score = sum(word in text_lower for word in con_words)
    if pro_score > con_score:
        return "pro"
    if con_score > pro_score:
        return "con"
    return "neutral"


def _mentions_ratio(text: str) -> float:
    mentions = len(re.findall(r"@[\w:-]+", text))
    words = max(len(text.split()), 1)
    return min(1.0, mentions / words)


def _anonymize(author: Optional[str]) -> Optional[str]:
    if not author:
        return None
    return f"user_{abs(hash(author)) % 10000:04d}"
