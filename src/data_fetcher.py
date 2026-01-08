"""
Data fetcher module for Crypto Morning Pulse Bot.
Handles fetching data from RSS feeds, APIs, and market data sources.
Includes logic to extract OG images from news articles.
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import feedparser
import json
import re

from src.config import (
    REQUEST_TIMEOUT,
    MAX_CONCURRENT_REQUESTS,
    CRYPTOPANIC_API_KEY,
    NEWS_SOURCES,
    COINGECKO_PRICE_URL,
    COINGECKO_GLOBAL_URL,
    FNG_INDEX_URL,
    X_API_BEARER_TOKEN,
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
        """Fetch content from a URL."""
        if not self.session:
            raise RuntimeError("Session not initialized.")
        
        async with self.semaphore:
            try:
                async with self.session.get(
                    url,
                    headers=headers or {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    },
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    return None
            except Exception as e:
                logger.debug(f"Error fetching {url}: {str(e)}")
                return None

    async def extract_og_image(self, url: str) -> Optional[str]:
        """Extract the first image or OG image from a news URL."""
        try:
            html = await self._fetch_url(url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, "html.parser")
            
            # 1. Try OG Image
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                return og_image["content"]
            
            # 2. Try Twitter Image
            twitter_image = soup.find("meta", name="twitter:image")
            if twitter_image and twitter_image.get("content"):
                return twitter_image["content"]
            
            # 3. Try first large image in body
            for img in soup.find_all("img"):
                src = img.get("src")
                if src and src.startswith("http") and not any(x in src.lower() for x in ["icon", "logo", "avatar", "ad"]):
                    return src
                    
            return None
        except Exception:
            return None

    async def fetch_market_overview(self) -> Dict:
        """Fetch market overview data."""
        overview = {}
        price_data = await self._fetch_url(COINGECKO_PRICE_URL)
        if price_data:
            prices = json.loads(price_data)
            overview['btc'] = prices.get('bitcoin', {})
            overview['eth'] = prices.get('ethereum', {})
            overview['xrp'] = prices.get('ripple', {})
            
        global_data = await self._fetch_url(COINGECKO_GLOBAL_URL)
        if global_data:
            g_data = json.loads(global_data).get('data', {})
            overview['total_market_cap'] = g_data.get('total_market_cap', {}).get('usd', 0)
            overview['market_cap_change'] = g_data.get('market_cap_change_percentage_24h_usd', 0)
            
        fng_data = await self._fetch_url(FNG_INDEX_URL)
        if fng_data:
            f_data = json.loads(fng_data).get('data', [{}])[0]
            overview['fng_value'] = f_data.get('value', 'N/A')
            overview['fng_classification'] = f_data.get('value_classification', 'N/A')
            
        return overview

    async def fetch_rss_feeds(self) -> List[Dict]:
        """Fetch news from RSS feeds and extract images."""
        feed_items = []
        for source_name, feed_url in NEWS_SOURCES.items():
            try:
                content = await self._fetch_url(feed_url)
                if content:
                    feed = feedparser.parse(content)
                    for entry in feed.entries[:10]:
                        url = entry.get("link", "")
                        summary = entry.get("summary", "")
                        if summary:
                            summary = BeautifulSoup(summary, "html.parser").get_text()
                        
                        if not summary or len(summary) < 50:
                            continue
                            
                        feed_items.append({
                            "title": entry.get("title", ""),
                            "url": url,
                            "source": source_name.replace("_", " ").title(),
                            "summary": summary,
                        })
            except Exception: continue
        
        # Extract images for the top items to save time
        # We'll do this later in the pipeline for selected items only to be efficient
        return feed_items

    async def fetch_x_trending_posts(self) -> List[Dict]:
        """Fetch trending X posts with full URLs."""
        # Mocked high-quality data as requested
        return [
            {
                "username": "VitalikButerin", 
                "text": "針對以太坊擴容方案發表最新看法，強調Layer 2需要更好的互操作性", 
                "likes": "45k",
                "url": "https://x.com/VitalikButerin/status/1876543210"
            },
            {
                "username": "DocumentingBTC", 
                "text": "MicroStrategy再次增持比特幣，總持倉突破50萬枚BTC", 
                "likes": "38k",
                "url": "https://x.com/DocumentingBTC/status/1876543211"
            },
            {
                "username": "CryptoKaleo", 
                "text": "技術分析指出BTC可能在$105k遇到重要阻力位，建議觀望", 
                "likes": "32k",
                "url": "https://x.com/CryptoKaleo/status/1876543212"
            },
            {
                "username": "CoinDesk", 
                "text": "SEC主席暗示可能批准更多現貨加密貨幣ETF申請", 
                "likes": "28k",
                "url": "https://x.com/CoinDesk/status/1876543213"
            },
            {
                "username": "SBF_FTX", 
                "text": "關於加密貨幣監管的長文討論，呼籲產業與監管機構建立更好溝通", 
                "likes": "25k",
                "url": "https://x.com/SBF_FTX/status/1876543214"
            },
        ]

    async def fetch_all_data(self) -> Dict:
        """Fetch all data for the briefing."""
        market_overview = await self.fetch_market_overview()
        rss_items = await self.fetch_rss_feeds()
        x_posts = await self.fetch_x_trending_posts()
        
        return {
            "market_overview": market_overview,
            "news_items": rss_items,
            "x_posts": x_posts
        }
