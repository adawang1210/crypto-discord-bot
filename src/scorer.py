"""
Scoring and content filtering module for Crypto Morning Pulse Bot.
Implements impact scoring, deduplication, and content quality assessment.
"""

import re
import json
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from src.config import (
    MIN_IMPACT_SCORE,
    MIN_KOL_SCORE,
    CONTENT_KEYWORD_MULTIPLIERS,
    RECENCY_BONUS,
    CACHE_DIR,
    CACHE_RETENTION_DAYS,
    DEDUP_KEYWORD_THRESHOLD,
)
from src.logger import logger


class ContentScorer:
    """Scores and filters content based on impact and quality criteria."""
    
    # Valid categories
    VALID_CATEGORIES = {
        "macro_policy": "Macro/Policy",
        "capital_flow": "Capital Flow",
        "major_coins": "Major Coins",
        "altcoins_trending": "Altcoins/Trending",
        "tech_narratives": "Tech/Narratives",
        "kol_insights": "KOL Insights",
    }
    
    def __init__(self):
        """Initialize scorer with cache."""
        self.cache_file = os.path.join(CACHE_DIR, "content_cache.json")
        self.published_cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """
        Load published content cache from file.
        
        Returns:
            Dict: Cache of published content items.
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                    # Clean up old entries (older than CACHE_RETENTION_DAYS)
                    cutoff_time = (
                        datetime.now() - timedelta(days=CACHE_RETENTION_DAYS)
                    ).isoformat()
                    cache = {
                        k: v for k, v in cache.items()
                        if v.get("timestamp", "") > cutoff_time
                    }
                    return cache
            except Exception as e:
                logger.error(f"Error loading cache: {str(e)}")
        
        return {}
    
    def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.published_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving cache: {str(e)}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for deduplication.
        
        Args:
            text: Text to extract keywords from.
        
        Returns:
            List[str]: List of keywords.
        """
        # Remove URLs and special characters
        text = re.sub(r"http\S+|@\w+|#\w+", "", text)
        # Extract words (3+ characters)
        words = re.findall(r"\b\w{3,}\b", text.lower())
        return words
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using keyword overlap.
        
        Args:
            text1: First text.
            text2: Second text.
        
        Returns:
            float: Similarity score (0-1).
        """
        keywords1 = set(self._extract_keywords(text1))
        keywords2 = set(self._extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1 & keywords2)
        # Use max length for better similarity detection
        max_len = max(len(keywords1), len(keywords2))
        
        return intersection / max_len if max_len > 0 else 0.0
    
    def is_duplicate(self, text: str) -> bool:
        """
        Check if content is duplicate of recently published item.
        
        Args:
            text: Content text to check.
        
        Returns:
            bool: True if duplicate found, False otherwise.
        """
        for cached_item in self.published_cache.values():
            similarity = self._calculate_similarity(
                text,
                cached_item.get("text", "")
            )
            if similarity >= DEDUP_KEYWORD_THRESHOLD:
                logger.debug(f"Duplicate detected with similarity {similarity:.2f}")
                return True
        
        return False
    
    def _calculate_kol_score(self, post: Dict) -> int:
        """
        Calculate impact score for a KOL post.
        
        Args:
            post: KOL post dictionary.
        
        Returns:
            int: Total impact score.
        """
        score = post.get("base_score", 0)
        text = post.get("text", "").lower()
        
        # Apply content keyword multipliers
        for keywords, multiplier in CONTENT_KEYWORD_MULTIPLIERS.items():
            if re.search(keywords, text, re.IGNORECASE):
                score += multiplier
        
        # Apply recency bonus
        timestamp = post.get("timestamp", "")
        if timestamp:
            try:
                # Estimate time from timestamp (simplified)
                now = datetime.now()
                # This is a placeholder - actual implementation would parse timestamp
                score += RECENCY_BONUS.get("2_hours", 15)
            except Exception as e:
                logger.debug(f"Error calculating recency bonus: {str(e)}")
        
        return score
    
    def _calculate_news_quality_score(self, item: Dict) -> int:
        """
        Calculate quality score for a news item.
        
        Args:
            item: News item dictionary.
        
        Returns:
            int: Quality score (0-10).
        """
        score = 0
        
        # Multi-source verification (placeholder - would need actual implementation)
        score += 2
        
        # Financial significance (check for large amounts)
        text = (item.get("title", "") + item.get("summary", "")).lower()
        if re.search(r"\$\d{2,}[mb]|billion|million", text, re.IGNORECASE):
            score += 2
        
        # Official sources
        source = item.get("source", "").lower()
        official_sources = ["sec", "coinbase", "binance", "ethereum", "bitcoin"]
        if any(s in source for s in official_sources):
            score += 3
        
        # Network effect (trending indicators)
        if item.get("kind") == "news":
            score += 2
        
        return min(score, 10)
    
    def score_kol_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Score and filter KOL posts.
        
        Args:
            posts: List of KOL posts.
        
        Returns:
            List[Dict]: Scored and filtered posts.
        """
        scored_posts = []
        
        for post in posts:
            score = self._calculate_kol_score(post)
            
            if score >= MIN_KOL_SCORE and not self.is_duplicate(post.get("text", "")):
                post["impact_score"] = score
                scored_posts.append(post)
        
        # Sort by score descending
        scored_posts.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
        
        logger.info(f"Scored {len(scored_posts)} KOL posts (threshold: {MIN_KOL_SCORE})")
        return scored_posts
    
    def score_news_items(self, items: List[Dict]) -> List[Dict]:
        """
        Score and filter news items.
        
        Args:
            items: List of news items.
        
        Returns:
            List[Dict]: Scored and filtered items.
        """
        scored_items = []
        
        for item in items:
            score = self._calculate_news_quality_score(item)
            
            if score >= MIN_IMPACT_SCORE and not self.is_duplicate(item.get("title", "")):
                item["impact_score"] = score
                scored_items.append(item)
        
        # Sort by score descending
        scored_items.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
        
        logger.info(f"Scored {len(scored_items)} news items (threshold: {MIN_IMPACT_SCORE})")
        return scored_items
    
    def _categorize_news(self, item: Dict) -> str:
        """
        Categorize a news item into one of the predefined categories.
        
        Args:
            item: News item to categorize.
        
        Returns:
            str: Category name.
        """
        text = (item.get("title", "") + item.get("summary", "")).lower()
        
        # Simple keyword-based categorization
        if re.search(r"sec|regulation|law|policy|etf", text):
            return "macro_policy"
        elif re.search(r"inflow|outflow|whale|transfer|drain", text):
            return "capital_flow"
        elif re.search(r"\bbitcoin\b|\bbtc\b|\bethereum\b|\beth\b|\bsolana\b|\bsol\b", text):
            return "major_coins"
        elif re.search(r"altcoin|token|memecoin|trending|surge|pump", text):
            return "altcoins_trending"
        elif re.search(r"layer|l2|defi|rwa|ai|zk|protocol", text):
            return "tech_narratives"
        else:
            return "macro_policy"  # Default category
    
    def select_top_items_with_diversity(
        self,
        kol_posts: List[Dict],
        news_items: List[Dict],
        total_items: int = 5
    ) -> List[Dict]:
        """
        Select top items ensuring category diversity.
        Prioritize: 1 KOL Insights + 4 diverse news categories.
        
        Args:
            kol_posts: Scored KOL posts.
            news_items: Scored news items.
            total_items: Total items to select (default 5).
        
        Returns:
            List[Dict]: Selected items with category diversity.
        """
        selected = []
        category_count = {}
        
        # Step 1: Add 1 KOL Insights if available
        if kol_posts:
            kol_item = kol_posts[0]
            kol_item["category"] = "kol_insights"
            kol_item["source_name"] = kol_item.get("username", "Unknown")
            selected.append(kol_item)
            category_count["kol_insights"] = 1
        
        # Step 2: Categorize and sort news items
        categorized_news = {}
        for item in news_items:
            category = self._categorize_news(item)
            if category not in categorized_news:
                categorized_news[category] = []
            categorized_news[category].append(item)
        
        # Step 3: Select items ensuring category diversity
        remaining_slots = total_items - len(selected)
        
        # First pass: take 1 item from each category
        for category in sorted(categorized_news.keys()):
            if len(selected) >= total_items:
                break
            
            if category_count.get(category, 0) < 1 and categorized_news[category]:
                item = categorized_news[category][0]
                item["category"] = category
                item["source_name"] = item.get("source", "Unknown")
                selected.append(item)
                category_count[category] = 1
        
        # Second pass: fill remaining slots with highest scoring items
        for category in sorted(categorized_news.keys()):
            if len(selected) >= total_items:
                break
            
            # Allow max 2 items per category
            if category_count.get(category, 0) < 2:
                for item in categorized_news[category][1:]:
                    if len(selected) >= total_items:
                        break
                    if item not in selected:
                        item["category"] = category
                        item["source_name"] = item.get("source", "Unknown")
                        selected.append(item)
                        category_count[category] = category_count.get(category, 0) + 1
        
        logger.info(f"✅ Selected {len(selected)} items with category diversity: {category_count}")
        return selected[:total_items]
    
    def add_to_cache(self, item: Dict) -> None:
        """
        Add published item to cache.
        
        Args:
            item: Item to add to cache.
        """
        cache_key = f"{item.get('category', 'unknown')}_{datetime.now().isoformat()}"
        self.published_cache[cache_key] = {
            "text": item.get("text", item.get("title", "")),
            "timestamp": datetime.now().isoformat(),
            "category": item.get("category", ""),
        }
        self._save_cache()
