"""
Data fetcher module for Crypto Morning Pulse Bot.
Handles fetching data from Nitter, news APIs, and other sources.
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import feedparser
import time

from src.config import (
    NITTER_INSTANCES,
    NITTER_REQUEST_DELAY,
    REQUEST_TIMEOUT,
    MAX_CONCURRENT_REQUESTS,
    CRYPTOPANIC_API_KEY,
    KOL_TIER_1,
    KOL_TIER_2,
    KOL_TIER_3,
)
from src.logger import logger


class NitterRotator:
    """Manages Nitter instance rotation and health tracking."""
    
    def __init__(self):
        """Initialize Nitter rotator with instance list."""
        self.instances = NITTER_INSTANCES.copy()
        self.instance_status: Dict[str, Dict] = {
            instance: {"healthy": True, "last_failed": None}
            for instance in self.instances
        }
        self.current_index = 0
    
    def get_next_instance(self) -> Optional[str]:
        """
        Get the next healthy Nitter instance.
        
        Returns:
            Optional[str]: Next healthy instance URL, or None if all are down.
        """
        attempts = 0
        while attempts < len(self.instances):
            instance = self.instances[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.instances)
            
            status = self.instance_status[instance]
            
            # Check if instance is in cooldown (marked as unhealthy for 1 hour)
            if not status["healthy"]:
                if status["last_failed"] and \
                   datetime.now() - status["last_failed"] < timedelta(hours=1):
                    attempts += 1
                    continue
                else:
                    # Try to recover after cooldown
                    status["healthy"] = True
            
            return instance
        
        return None
    
    def mark_failed(self, instance: str) -> None:
        """
        Mark an instance as failed and start cooldown.
        
        Args:
            instance: The Nitter instance URL that failed.
        """
        if instance in self.instance_status:
            self.instance_status[instance]["healthy"] = False
            self.instance_status[instance]["last_failed"] = datetime.now()
            logger.warning(f"Marked Nitter instance as unhealthy: {instance}")
    
    def mark_healthy(self, instance: str) -> None:
        """
        Mark an instance as healthy.
        
        Args:
            instance: The Nitter instance URL that is healthy.
        """
        if instance in self.instance_status:
            self.instance_status[instance]["healthy"] = True
            logger.info(f"Marked Nitter instance as healthy: {instance}")
    
    def get_status_report(self) -> Dict[str, bool]:
        """
        Get status report of all instances.
        
        Returns:
            Dict[str, bool]: Mapping of instances to their health status.
        """
        return {
            instance: status["healthy"]
            for instance, status in self.instance_status.items()
        }


class DataFetcher:
    """Main data fetcher class for crypto market data."""
    
    def __init__(self):
        """Initialize data fetcher with Nitter rotator."""
        self.nitter_rotator = NitterRotator()
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
                        logger.warning(f"Rate limited or forbidden: {url} (Status: {response.status})")
                        return None
                    else:
                        logger.warning(f"HTTP {response.status} from {url}")
                        return None
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url}")
                return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                return None
    
    async def fetch_nitter_kol_posts(
        self,
        username: str,
        max_posts: int = 10
    ) -> List[Dict]:
        """
        Fetch posts from a KOL account via Nitter.
        
        Args:
            username: Twitter/X username (without @).
            max_posts: Maximum number of posts to fetch.
        
        Returns:
            List[Dict]: List of posts with metadata.
        """
        posts = []
        instance = self.nitter_rotator.get_next_instance()
        
        if not instance:
            logger.error("No healthy Nitter instances available")
            return posts
        
        url = f"https://{instance}/{username}"
        
        try:
            await asyncio.sleep(NITTER_REQUEST_DELAY)
            content = await self._fetch_url(url)
            
            if not content:
                self.nitter_rotator.mark_failed(instance)
                return posts
            
            self.nitter_rotator.mark_healthy(instance)
            
            soup = BeautifulSoup(content, "html.parser")
            tweet_elements = soup.find_all("div", class_="tweet")
            
            for tweet in tweet_elements[:max_posts]:
                try:
                    text_elem = tweet.find("p", class_="tweet-text")
                    link_elem = tweet.find("a", class_="tweet-link")
                    time_elem = tweet.find("span", class_="tweet-date")
                    
                    if text_elem and link_elem:
                        post = {
                            "username": username,
                            "text": text_elem.get_text(strip=True),
                            "url": f"https://{instance}{link_elem.get('href', '')}",
                            "timestamp": time_elem.get_text(strip=True) if time_elem else None,
                            "source": "nitter",
                        }
                        posts.append(post)
                except Exception as e:
                    logger.debug(f"Error parsing tweet from {username}: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error fetching Nitter posts for {username}: {str(e)}")
            self.nitter_rotator.mark_failed(instance)
        
        return posts
    
    async def fetch_cryptopanic_news(self) -> List[Dict]:
        """
        Fetch trending news from CryptoPanic API.
        
        Returns:
            List[Dict]: List of news items.
        """
        news_items = []
        
        if not CRYPTOPANIC_API_KEY:
            logger.debug("CryptoPanic API key not configured, skipping")
            return news_items
        
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&kind=news"
        
        try:
            content = await self._fetch_url(url)
            if content:
                import json
                data = json.loads(content)
                
                for item in data.get("results", [])[:10]:
                    news_items.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "source": item.get("source", {}).get("title", "Unknown"),
                        "published_at": item.get("published_at", ""),
                        "kind": item.get("kind", ""),
                        "source_type": "cryptopanic",
                    })
        except Exception as e:
            logger.error(f"Error fetching CryptoPanic news: {str(e)}")
        
        return news_items
    
    async def fetch_rss_feed(self, feed_url: str) -> List[Dict]:
        """
        Fetch items from an RSS feed.
        
        Args:
            feed_url: URL of the RSS feed.
        
        Returns:
            List[Dict]: List of feed items.
        """
        items = []
        
        try:
            content = await self._fetch_url(feed_url)
            if content:
                feed = feedparser.parse(content)
                
                for entry in feed.entries[:10]:
                    items.append({
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "summary": entry.get("summary", "")[:200],
                        "source_type": "rss",
                    })
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {str(e)}")
        
        return items
    
    async def fetch_all_kol_posts(self) -> List[Dict]:
        """
        Fetch posts from all KOLs in the watch list.
        
        Returns:
            List[Dict]: Combined list of KOL posts with tier information.
        """
        all_posts = []
        
        # Combine all KOL tiers
        kol_list = [
            (username, tier, 50) for username, tier in KOL_TIER_1.items()
        ] + [
            (username, tier, 30) for username, tier in KOL_TIER_2.items()
        ] + [
            (username, tier, 30) for username, tier in KOL_TIER_3.items()
        ]
        
        # Fetch posts concurrently
        tasks = [
            self.fetch_nitter_kol_posts(username)
            for username, _, _ in kol_list
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (username, tier, base_score), posts in zip(kol_list, results):
            if isinstance(posts, list):
                for post in posts:
                    post["kol_tier"] = tier
                    post["base_score"] = base_score
                    all_posts.append(post)
        
        return all_posts
    
    async def fetch_all_data(self) -> Dict[str, List]:
        """
        Fetch data from all sources.
        
        Returns:
            Dict[str, List]: Dictionary containing data from all sources.
        """
        logger.info("Starting data fetch from all sources")
        
        try:
            kol_posts, cryptopanic_news = await asyncio.gather(
                self.fetch_all_kol_posts(),
                self.fetch_cryptopanic_news(),
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(kol_posts, Exception):
                logger.error(f"Error fetching KOL posts: {kol_posts}")
                kol_posts = []
            
            if isinstance(cryptopanic_news, Exception):
                logger.error(f"Error fetching CryptoPanic news: {cryptopanic_news}")
                cryptopanic_news = []
            
            logger.info(
                f"Data fetch complete: {len(kol_posts)} KOL posts, "
                f"{len(cryptopanic_news)} news items"
            )
            
            return {
                "kol_posts": kol_posts,
                "news": cryptopanic_news,
                "nitter_status": self.nitter_rotator.get_status_report(),
            }
        
        except Exception as e:
            logger.error(f"Error in fetch_all_data: {str(e)}")
            return {
                "kol_posts": [],
                "news": [],
                "nitter_status": self.nitter_rotator.get_status_report(),
            }
