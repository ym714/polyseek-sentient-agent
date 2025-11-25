"""Helpers for retrieving official market data."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

import httpx

from .config import Settings, load_settings


class MarketSource(str, Enum):
    POLYMARKET = "polymarket"
    KALSHI = "kalshi"


@dataclass
class MarketPrices:
    yes: Optional[float]
    no: Optional[float]


@dataclass
class MarketData:
    market_id: str
    title: str
    category: Optional[str]
    rules: Optional[str]
    deadline: Optional[dt.datetime]
    liquidity: Optional[float]
    volume_24h: Optional[float]
    source: MarketSource
    url: str
    prices: MarketPrices


class MarketFetchError(RuntimeError):
    """Raised when market information cannot be retrieved."""


def detect_market_source(url: str) -> MarketSource:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "polymarket" in host:
        return MarketSource.POLYMARKET
    if "kalshi" in host:
        return MarketSource.KALSHI
    raise MarketFetchError(f"Unsupported market host: {host}")


async def fetch_market_data(
    url: str,
    settings: Optional[Settings] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> MarketData:
    """Fetch metadata for a market URL."""
    settings = settings or load_settings()
    source = detect_market_source(url)
    if source == MarketSource.POLYMARKET:
        return await _fetch_polymarket_data(url, settings, client)
    return await _fetch_kalshi_data(url, settings, client)


async def _fetch_polymarket_data(
    url: str,
    settings: Settings,
    client: Optional[httpx.AsyncClient] = None,
) -> MarketData:
    if settings.app.offline_mode:
        return _offline_market(url, MarketSource.POLYMARKET)
    slug = _extract_polymarket_slug(url)
    # Try /events endpoint first (for event-based markets)
    endpoint = f"{settings.apis.polymarket_base}/events?slug={slug}"
    close_client = client is None
    client = client or httpx.AsyncClient(timeout=10)
    try:
        resp = await client.get(endpoint)
        resp.raise_for_status()
        payload = resp.json()
        
        # Handle /events response (returns event with nested markets)
        if isinstance(payload, list) and len(payload) > 0:
            event = payload[0]
            markets = event.get("markets", [])
            if markets:
                # Use the first active market or the first one
                market = next((m for m in markets if m.get("active")), markets[0])
                # Parse outcomes and prices
                outcomes = json.loads(market.get("outcomes", "[]")) if isinstance(market.get("outcomes"), str) else market.get("outcomes", [])
                outcome_prices = json.loads(market.get("outcomePrices", "[]")) if isinstance(market.get("outcomePrices"), str) else market.get("outcomePrices", [])
                
                yes_price = None
                no_price = None
                if outcomes and outcome_prices:
                    for outcome, price in zip(outcomes, outcome_prices):
                        if outcome.lower() == "yes":
                            yes_price = float(price) if price else None
                        elif outcome.lower() == "no":
                            no_price = float(price) if price else None
                
                return MarketData(
                    market_id=str(market.get("id") or event.get("id")),
                    title=event.get("title") or market.get("question") or slug,
                    category=event.get("category"),
                    rules=event.get("description") or market.get("description") or market.get("resolutionSource"),
                    deadline=_parse_datetime(event.get("endDate") or market.get("endDate")),
                    liquidity=_to_float(event.get("liquidity") or market.get("liquidity")),
                    volume_24h=_to_float(event.get("volume24hr") or market.get("volume24hr")),
                    source=MarketSource.POLYMARKET,
                    url=url,
                    prices=MarketPrices(yes=yes_price, no=no_price),
                )
        
        # Fallback to /markets endpoint
        endpoint = f"{settings.apis.polymarket_base}/markets?slug={slug}"
        resp = await client.get(endpoint)
        resp.raise_for_status()
        payload = resp.json()
        
        if isinstance(payload, list):
            if not payload:
                raise MarketFetchError(f"No market found for slug '{slug}'")
            market = payload[0]
        else:
            markets = payload.get("markets") or []
            if not markets:
                raise MarketFetchError(f"No market found for slug '{slug}'")
            market = markets[0]

        return MarketData(
            market_id=str(market.get("market_id") or market.get("id")),
            title=market.get("question") or market.get("title") or slug,
            category=market.get("category"),
            rules=market.get("resolution_source") or market.get("resolution_criteria"),
            deadline=_parse_datetime(market.get("end_date") or market.get("close_time")),
            liquidity=_to_float(market.get("liquidity_in_usd") or market.get("liquidity")),
            volume_24h=_to_float(market.get("volume24hr")),
            source=MarketSource.POLYMARKET,
            url=url,
            prices=MarketPrices(
                yes=_to_float(market.get("yesPrice") or market.get("price")),
                no=_to_float(market.get("noPrice")),
            ),
        )
    except httpx.HTTPError as exc:
        raise MarketFetchError(f"Failed to fetch Polymarket data: {exc}") from exc
    finally:
        if close_client:
            await client.aclose()


async def _fetch_kalshi_data(
    url: str,
    settings: Settings,
    client: Optional[httpx.AsyncClient] = None,
) -> MarketData:
    if settings.app.offline_mode:
        return _offline_market(url, MarketSource.KALSHI)
    ticker = _extract_kalshi_ticker(url)
    endpoint = f"{settings.apis.kalshi_base}/trade-api/v2/markets/{ticker}"
    headers = {"accept": "application/json"}
    if settings.apis.kalshi_api_key and settings.apis.kalshi_api_secret:
        headers.update(
            {
                "kalshi-access-key": settings.apis.kalshi_api_key,
                "kalshi-secret-key": settings.apis.kalshi_api_secret,
            }
        )

    close_client = client is None
    client = client or httpx.AsyncClient(timeout=10)
    try:
        resp = await client.get(endpoint, headers=headers)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise MarketFetchError(f"Failed to fetch Kalshi data: {exc}") from exc
    finally:
        if close_client:
            await client.aclose()

    market = resp.json().get("market", {})
    return MarketData(
        market_id=market.get("id") or ticker,
        title=market.get("title") or ticker,
        category=market.get("event_ticker"),
        rules=market.get("rules"),
        deadline=_parse_datetime(market.get("close_time")),
        liquidity=_to_float(market.get("liquidity")),
        volume_24h=_to_float(market.get("day_volume")),
        source=MarketSource.KALSHI,
        url=url,
        prices=MarketPrices(
            yes=_to_float(market.get("yes_price")),
            no=_to_float(market.get("no_price")),
        ),
    )


def _extract_polymarket_slug(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        raise MarketFetchError("Could not extract Polymarket slug")
    return path.split("/")[-1]


def _extract_kalshi_ticker(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        raise MarketFetchError("Could not extract Kalshi ticker")
    return path.split("/")[-1].upper()


def _parse_datetime(raw: Optional[str]) -> Optional[dt.datetime]:
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except ValueError:
        return None


def _to_float(value: Optional[object]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _offline_market(url: str, source: MarketSource) -> MarketData:
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    return MarketData(
        market_id=f"offline-{source.value}",
        title=f"Offline {source.value.capitalize()} market",
        category="offline",
        rules="Offline mode is enabled; this is stubbed data.",
        deadline=now + dt.timedelta(days=7),
        liquidity=10000.0,
        volume_24h=5000.0,
        source=source,
        url=url,
        prices=MarketPrices(yes=0.5, no=0.5),
    )
