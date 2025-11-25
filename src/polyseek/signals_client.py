"""External signal aggregation (news / social)."""

from __future__ import annotations

import datetime as dt
import urllib.parse
from dataclasses import dataclass
from typing import Iterable, List, Optional, Protocol

import httpx

try:
    import feedparser
except ImportError:
    feedparser = None  # type: ignore

from .config import Settings, load_settings
from .fetch_market import MarketData


@dataclass
class SignalRecord:
    source: str
    source_type: str  # news | sns | comment
    title: str
    url: str
    snippet: str
    timestamp: Optional[dt.datetime]
    sentiment: str
    credibility_score: float
    engagement: Optional[int] = None
    language: str = "en"


class SignalProvider(Protocol):
    async def search(self, query: str) -> List[SignalRecord]: ...


class TwitterSignalProvider:
    """Twitter/X API v2 integration for real-time social signals."""

    def __init__(self, bearer_token: Optional[str], max_results: int = 10):
        self.bearer_token = bearer_token
        self.max_results = max_results
        self.api_base = "https://api.twitter.com/2"

    @property
    def available(self) -> bool:
        return bool(self.bearer_token)

    async def search(self, query: str) -> List[SignalRecord]:
        """Search recent tweets using Twitter API v2."""
        if not self.available:
            return []
        
        # Twitter API v2 search endpoint
        url = f"{self.api_base}/tweets/search/recent"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
        
        # Build query - remove common words and focus on keywords
        # Twitter search syntax: https://developer.twitter.com/en/docs/twitter-api/v1/rules-and-filtering/search-operators
        query_clean = query.replace("?", "").replace("Will", "").strip()
        # Limit query length for Twitter API
        if len(query_clean) > 500:
            query_clean = query_clean[:500]
        
        params = {
            "query": query_clean,
            "max_results": min(self.max_results, 10),  # Twitter API limit
            "tweet.fields": "created_at,public_metrics,lang",
            "expansions": "author_id",
            "user.fields": "username,verified",
        }
        
        records: List[SignalRecord] = []
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
            
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            
            for tweet in tweets:
                author_id = tweet.get("author_id")
                author = users.get(author_id, {})
                username = author.get("username", "unknown")
                text = tweet.get("text", "")
                created_at = tweet.get("created_at")
                metrics = tweet.get("public_metrics", {})
                engagement = (
                    metrics.get("like_count", 0)
                    + metrics.get("retweet_count", 0)
                    + metrics.get("reply_count", 0)
                )
                
                # Parse timestamp
                timestamp = None
                if created_at:
                    try:
                        timestamp = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    except ValueError:
                        timestamp = None
                
                # Create tweet URL
                tweet_id = tweet.get("id", "")
                tweet_url = f"https://twitter.com/{username}/status/{tweet_id}" if tweet_id else ""
                
                # Calculate credibility score based on engagement and verification
                credibility = 0.5
                if author.get("verified"):
                    credibility += 0.2
                if engagement > 100:
                    credibility += 0.2
                elif engagement > 10:
                    credibility += 0.1
                
                records.append(
                    SignalRecord(
                        source=f"@{username}",
                        source_type="sns",
                        title=f"Tweet by @{username}",
                        url=tweet_url,
                        snippet=text[:280],
                        timestamp=timestamp,
                        sentiment=_heuristic_sentiment(text),
                        credibility_score=min(credibility, 1.0),
                        engagement=engagement,
                        language=tweet.get("lang", "en"),
                    )
                )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print(f"[signals] Twitter API authentication failed - check bearer token")
            elif e.response.status_code == 429:
                print(f"[signals] Twitter API rate limit exceeded")
            else:
                print(f"[signals] Twitter API error: {e}")
        except Exception as exc:
            print(f"[signals] Twitter search failed: {exc}")
        
        return records


class RSSSignalProvider:
    """RSS feed aggregator for news signals (completely free).
    
    Supports multiple RSS sources including Google News and major news sites.
    """

    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        # Multiple RSS sources for comprehensive coverage
        self.rss_sources = [
            # Google News RSS (query-based)
            "https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en",
            # Major news sites RSS feeds (general news)
            "https://feeds.reuters.com/reuters/topNews",
            "https://feeds.bbci.co.uk/news/rss.xml",
            "https://rss.cnn.com/rss/edition.rss",
            "https://feeds.npr.org/1001/rss.xml",
            "https://feeds.feedburner.com/oreilly/radar",
        ]
        
        # Query-based RSS sources (will be formatted with query)
        self.query_based_sources = [
            "https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en",
        ]

    @property
    def available(self) -> bool:
        return feedparser is not None

    async def search(self, query: str) -> List[SignalRecord]:
        """Search RSS feeds for news articles."""
        if not self.available:
            return []
        
        records: List[SignalRecord] = []
        query_encoded = urllib.parse.quote(query)
        
        # Search query-based RSS feeds
        for rss_url_template in self.query_based_sources:
            try:
                rss_url = rss_url_template.format(query=query_encoded)
                records.extend(await self._fetch_rss_feed(rss_url, "Google News RSS"))
            except Exception as exc:
                print(f"[signals] RSS feed error ({rss_url_template[:50]}...): {exc}")
                continue
        
        # Also check general news feeds for relevant articles
        # (This is optional and can be slow, so we limit it)
        for rss_url in self.rss_sources[:2]:  # Limit to first 2 general feeds
            if "{query}" not in rss_url:  # Skip query-based ones (already processed)
                try:
                    # For general feeds, we'll filter by checking if query terms appear
                    feed_records = await self._fetch_rss_feed(rss_url, "RSS Feed")
                    # Filter records that contain query keywords
                    query_words = set(query.lower().split())
                    filtered = [
                        r for r in feed_records
                        if any(word in r.title.lower() or word in r.snippet.lower() for word in query_words if len(word) > 3)
                    ]
                    records.extend(filtered[:3])  # Limit to 3 per general feed
                except Exception as exc:
                    print(f"[signals] RSS feed error: {exc}")
                    continue
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_records = []
        for record in records:
            if record.url and record.url not in seen_urls:
                seen_urls.add(record.url)
                unique_records.append(record)
        
        return unique_records[:self.max_results * 2]  # Allow more results from RSS

    async def _fetch_rss_feed(self, rss_url: str, source_name: str) -> List[SignalRecord]:
        """Fetch and parse a single RSS feed."""
        records: List[SignalRecord] = []
        
        try:
            # Use httpx to fetch RSS (with SSL verification disabled for compatibility)
            # Note: In production, you might want to handle SSL properly
            async with httpx.AsyncClient(timeout=15, verify=False, follow_redirects=True) as client:
                resp = await client.get(rss_url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                rss_content = resp.text
            
            # Parse RSS content with feedparser
            import asyncio
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, rss_content)
            
            # Check if parsing was successful
            if feed.bozo and feed.bozo_exception:
                # Log but continue - sometimes feedparser reports bozo but still has entries
                if "SSL" not in str(feed.bozo_exception) and "certificate" not in str(feed.bozo_exception).lower():
                    # Only skip if it's not an SSL error (we already handled that)
                    if not feed.entries:
                        return records  # Skip feeds with no entries
            
            feed_title = feed.feed.get("title", source_name) or source_name
            
            for entry in feed.entries[:self.max_results]:
                published = entry.get("published_parsed")
                timestamp = None
                if published:
                    try:
                        timestamp = dt.datetime(*published[:6], tzinfo=dt.timezone.utc)
                    except (ValueError, TypeError):
                        timestamp = None
                
                snippet = (entry.get("summary", "") or entry.get("description", "") or entry.get("title", ""))[:280]
                title = entry.get("title", "Untitled")
                link = entry.get("link", "")
                
                # Clean up Google News links (they're redirects)
                if "news.google.com" in link:
                    # Try to extract actual URL from Google News redirect
                    pass  # Keep as is for now
                
                records.append(
                    SignalRecord(
                        source=feed_title,
                        source_type="news",
                        title=title,
                        url=link,
                        snippet=snippet,
                        timestamp=timestamp,
                        sentiment=_heuristic_sentiment(snippet),
                        credibility_score=0.75,  # RSS feeds are generally reliable
                    )
                )
        except Exception as exc:
            # Silently fail individual feeds to allow others to succeed
            pass
        
        return records


class NewsAPISignalProvider:
    """Thin wrapper around newsapi.org/v2/everything."""

    def __init__(self, api_key: Optional[str], window_days: int = 30, max_results: int = 5):
        self.api_key = api_key
        self.window_days = window_days
        self.max_results = max_results

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str) -> List[SignalRecord]:
        if not self.available:
            return []
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "pageSize": self.max_results,
            "language": "en",
            "sortBy": "publishedAt",
        }
        if self.window_days:
            params["from"] = (dt.datetime.utcnow() - dt.timedelta(days=self.window_days)).strftime("%Y-%m-%d")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers={"X-Api-Key": self.api_key})
            resp.raise_for_status()
            data = resp.json()
        articles = data.get("articles") or []
        records: List[SignalRecord] = []
        for article in articles:
            published = article.get("publishedAt")
            timestamp = None
            if published:
                try:
                    timestamp = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
                except ValueError:
                    timestamp = None
            snippet = (article.get("description") or article.get("content") or "")[:280]
            records.append(
                SignalRecord(
                    source=article.get("source", {}).get("name") or "newsapi",
                    source_type="news",
                    title=article.get("title") or "Untitled",
                    url=article.get("url") or "",
                    snippet=snippet,
                    timestamp=timestamp,
                    sentiment=_heuristic_sentiment(snippet),
                    credibility_score=0.8,
                )
            )
        return records


async def gather_signals(
    market: MarketData,
    settings: Optional[Settings] = None,
    extra_providers: Optional[Iterable[SignalProvider]] = None,
) -> List[SignalRecord]:
    """Fetch external signals using the configured providers."""
    settings = settings or load_settings()
    query = _build_query(market)
    providers: List[SignalProvider] = []
    if settings.app.offline_mode:
        return _offline_signals(market)
    
    # News API provider
    news_provider = NewsAPISignalProvider(settings.apis.news_api_key)
    if news_provider.available:
        providers.append(news_provider)
    
    # Twitter/X API provider
    twitter_provider = TwitterSignalProvider(settings.apis.x_bearer_token)
    if twitter_provider.available:
        providers.append(twitter_provider)
    
    # RSS Feed provider (completely free, no API key needed)
    rss_provider = RSSSignalProvider()
    if rss_provider.available:
        providers.append(rss_provider)
    
    # Extra providers (for extensibility)
    if extra_providers:
        providers.extend(extra_providers)

    records: List[SignalRecord] = []
    for provider in providers:
        try:
            records.extend(await provider.search(query))
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[signals] provider {provider.__class__.__name__} failed: {exc}")
    return records


def _build_query(market: MarketData) -> str:
    # Extract key terms from title for better search results
    # Remove question marks and common words, keep important keywords
    title = market.title
    # Remove question marks and common stop words
    title_clean = title.replace("?", "").replace("When will", "").replace("will", "").strip()
    # Use just the title for cleaner search queries
    # Limit to first 100 characters to avoid overly long queries
    query = title_clean[:100] if len(title_clean) > 100 else title_clean
    return query.strip()


def _heuristic_sentiment(text: str) -> str:
    lowered = (text or "").lower()
    if any(word in lowered for word in ("rise", "win", "approve", "gain")):
        return "pro"
    if any(word in lowered for word in ("fall", "lose", "reject", "decline")):
        return "con"
    return "neutral"


def _offline_signals(market: MarketData) -> List[SignalRecord]:
    return [
        SignalRecord(
            source="offline-news",
            source_type="news",
            title=f"Offline insight for {market.title}",
            url=market.url,
            snippet="Offline mode stub signal.",
            timestamp=dt.datetime.utcnow(),
            sentiment="neutral",
            credibility_score=0.5,
        )
    ]
