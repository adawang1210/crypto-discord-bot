"""
Data fetcher module for Crypto Morning Pulse Bot.
Handles fetching data from RSS feeds, APIs, and other sources.
Nitter is used as fallback only.
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import feedparser
import json

from src.config import (
    NITTER_INSTANCES,
    NITTER_REQUEST_DELAY,
    REQUEST_TIMEOUT,
    MAX_CONCURRENT_REQUESTS,
    CRYPTOPANIC_API_KEY,
)
from src.logger import logger


class DataFetcher:
    """Main data fetcher class for crypto market data."""
    
    def __init__(self):
        """Initialize data fetcher."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _fetch_url(
        self,
        url: str,
        headers: Optional[Dict] = None,
        timeout: int = REQUEST_TIMEOUT
    ) -> Optional[str]:
        """
        Fetch content from a URL with timeout and error handling.
        
        Args:
            url: URL to fetch.
            headers: Optional HTTP headers.
            timeout: Request timeout in seconds.
        
        Returns:
            Optional[str]: Response text or None if failed.
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        async with self.semaphore:
            try:
                async with self.session.get(
                    url,
                    headers=headers or {},
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status in (403, 429):
                        logger.debug(f"Rate limited or forbidden: {url} (Status: {response.status})")
                        return None
                    else:
                        logger.debug(f"HTTP {response.status} from {url}")
                        return None
            except asyncio.TimeoutError:
                logger.debug(f"Timeout fetching {url}")
                return None
            except Exception as e:
                logger.debug(f"Error fetching {url}: {str(e)}")
                return None
    
    async def fetch_rss_feeds(self) -> List[Dict]:
        """
        Fetch news from RSS feeds.
        
        Returns:
            List[Dict]: List of feed items with metadata.
        """
        feed_items = []
        
        feeds = [
            ("CoinDesk", "https://feeds.coindesk.com/news"),
            ("Cointelegraph", "https://cointelegraph.com/feed"),
            ("Decrypt", "https://decrypt.co/feed"),
            ("The Block", "https://www.theblockresearch.com/feed"),
        ]
        
        for source_name, feed_url in feeds:
            try:
                content = await self._fetch_url(feed_url)
                if content:
                    feed = feedparser.parse(content)
                    
                    for entry in feed.entries[:3]:
                        try:
                            item = {
                                "title": entry.get("title", ""),
                                "url": entry.get("link", ""),
                                "published_at": entry.get("published", ""),
                                "source": source_name,
                                "summary": entry.get("summary", "")[:200],
                            }
                            feed_items.append(item)
                        except Exception as e:
                            logger.debug(f"Error parsing feed entry: {str(e)}")
                            continue
            except Exception as e:
                logger.debug(f"Error fetching RSS feed {feed_url}: {str(e)}")
        
        logger.info(f"Fetched {len(feed_items)} items from RSS feeds")
        return feed_items
    
    async def fetch_cryptopanic_news(self) -> List[Dict]:
        """
        Fetch trending news from CryptoPanic API.
        
        Returns:
            List[Dict]: List of news items with metadata.
        """
        news_items = []
        
        if not CRYPTOPANIC_API_KEY:
            logger.debug("CryptoPanic API key not configured, skipping news fetch")
            return news_items
        
        url = "https://cryptopanic.com/api/v1/posts/"
        params = {
            "auth_token": CRYPTOPANIC_API_KEY,
            "kind": "news",
            "public": "true",
            "limit": 20,
        }
        
        try:
            # Build URL with params
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{param_str}"
            
            content = await self._fetch_url(full_url)
            if content:
                data = json.loads(content)
                
                for item in data.get("results", []):
                    try:
                        news_item = {
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", {}).get("title", "CryptoPanic"),
                            "published_at": item.get("published_at", ""),
                            "kind": item.get("kind", ""),
                        }
                        news_items.append(news_item)
                    except Exception as e:
                        logger.debug(f"Error parsing CryptoPanic item: {str(e)}")
                        continue
                
                logger.info(f"Fetched {len(news_items)} items from CryptoPanic")
        except Exception as e:
            logger.warning(f"Error fetching CryptoPanic news: {str(e)}")
        
        return news_items
    
    async def fetch_coingecko_trending(self) -> List[Dict]:
        """
        Fetch trending coins from CoinGecko API.
        
        Returns:
            List[Dict]: List of trending coins with metadata.
        """
        trending_items = []
        
        url = "https://api.coingecko.com/api/v3/search/trending"
        
        try:
            content = await self._fetch_url(url)
            if content:
                data = json.loads(content)
                
                for coin in data.get("coins", [])[:5]:
                    try:
                        item = coin.get("item", {})
                        trending_item = {
                            "title": f"🔥 {item.get('name', '')} ({item.get('symbol', '').upper()}) trending",
                            "url": item.get("coingecko_url", ""),
                            "source": "CoinGecko",
                            "market_cap_rank": item.get("market_cap_rank", "N/A"),
                        }
                        trending_items.append(trending_item)
                    except Exception as e:
                        logger.debug(f"Error parsing CoinGecko trending item: {str(e)}")
                        continue
                
                logger.info(f"Fetched {len(trending_items)} trending coins from CoinGecko")
        except Exception as e:
            logger.debug(f"Error fetching CoinGecko trending: {str(e)}")
        
        return trending_items
    
    async def fetch_nitter_kol_posts(
        self,
        username: str,
        max_posts: int = 5
    ) -> List[Dict]:
        """
        Fetch posts from a KOL account via Nitter (fallback only).
        
        Args:
            username: Twitter/X username (without @).
            max_posts: Maximum number of posts to fetch.
        
        Returns:
            List[Dict]: List of posts with metadata.
        """
        posts = []
        
        # Skip Nitter for now due to rate limiting
        logger.debug(f"Skipping Nitter fetch for {username} (rate limit protection)")
        return posts
    
    async def fetch_all_data(self) -> Dict[str, List[Dict]]:
        """
        Fetch data from all sources.
        
        Returns:
            Dict[str, List[Dict]]: Dictionary with data from all sources.
        """
        try:
            # Fetch from stable sources
            rss_items = await self.fetch_rss_feeds()
            news_items = await self.fetch_cryptopanic_news()
            trending_items = await self.fetch_coingecko_trending()
            
            # Combine all items
            all_items = []
            
            # Add RSS items
            for item in rss_items:
                all_items.append({
                    **item,
                    "type": "news",
                    "score_base": 5,
                })
            
            # Add CryptoPanic items
            for item in news_items:
                all_items.append({
                    **item,
                    "type": "news",
                    "score_base": 6,
                })
            
            # Add trending items
            for item in trending_items:
                all_items.append({
                    **item,
                    "type": "trending",
                    "score_base": 7,
                })
            
            logger.info(f"Total items fetched: {len(all_items)}")
            
            return {
                "items": all_items,
                "rss_items": rss_items,
                "news_items": news_items,
                "trending_items": trending_items,
                "kol_posts": {},  # Empty for now
            }
        
        except Exception as e:
            logger.error(f"Error in fetch_all_data: {str(e)}")
            return {
                "items": [],
                "rss_items": [],
                "news_items": [],
                "trending_items": [],
                "kol_posts": {},
            }
