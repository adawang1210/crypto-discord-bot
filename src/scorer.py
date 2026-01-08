"""
Scoring and content filtering module for Crypto Morning Pulse Bot.
Implements impact scoring, deduplication, and content quality assessment.
Optimized to retain critical price action and market trend news.
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
    
    # Keywords to exclude (soft news, interviews, irrelevant topics)
    EXCLUDE_KEYWORDS = [
        r"exclusive interview", r"personal story", r"growing up", r"childhood",
        r"lifestyle", r"career", r"how to", r"guide for", r"beginner",
        r"meet the", r"story of"
    ]
    
    def __init__(self):
        """Initialize scorer with cache."""
        self.cache_file = os.path.join(CACHE_DIR, "content_cache.json")
        self.published_cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load published content cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                    cutoff_time = (datetime.now() - timedelta(days=CACHE_RETENTION_DAYS)).isoformat()
                    cache = {k: v for k, v in cache.items() if v.get("timestamp", "") > cutoff_time}
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
    
    def is_relevant(self, item: Dict) -> bool:
        """Check if the item is relevant to crypto market movements."""
        title = item.get("title", "").lower()
        summary = (item.get("summary", "") or "").lower()
        full_text = title + " " + summary
        
        # 1. Check for soft news exclusion
        for pattern in self.EXCLUDE_KEYWORDS:
            if re.search(pattern, full_text):
                logger.info(f"🚫 Excluding (Soft News): {title[:50]}... (Reason: {pattern})")
                return False
        
        # 2. Critical market keywords (Price action, etc.) - These should always be relevant
        critical_keywords = [
            r"bitcoin", r"btc", r"ethereum", r"eth", r"xrp", r"ripple", r"solana", r"sol",
            r"price", r"slips", r"rally", r"crash", r"surge", r"dip", r"bull", r"bear", 
            r"market", r"liquidation", r"ath", r"all-time high", r"below \$\d+", r"above \$\d+"
        ]
        if any(re.search(p, full_text) for p in critical_keywords):
            return True

        # 3. General crypto relevance
        crypto_keywords = [
            r"zcash", r"zec", r"ada", r"dot", r"avax",
            r"crypto", r"blockchain", r"token", r"etf", r"ipo", r"sec", r"fed", r"regulation",
            r"trading", r"defi", r"nft", r"dao", r"layer", r"wallet",
            r"exchange", r"binance", r"coinbase", r"funding", r"investment", r"hack", r"exploit",
            r"web3", r"digital asset", r"stablecoin", r"mining", r"staking", r"developer", r"devs",
            r"split", r"launch", r"announcement", r"partnership", r"cz", r"vitalik", r"buterin",
            r"saylor", r"musk", r"grayscale", r"microstrategy", r"blackrock", r"fidelity",
            r"rtfkt", r"collectibles", r"metaverse", r"airdrop", r"whitelist"
        ]
        
        if any(re.search(p, full_text) for p in crypto_keywords):
            return True
            
        logger.info(f"🚫 Excluding (Irrelevant): {title[:50]}...")
        return False
    
    def score_news_items(self, items: List[Dict], total_items: int = 8) -> List[Dict]:
        """Score and filter news items, then select top items with diversity."""
        scored_items = []
        for item in items:
            if not self.is_relevant(item):
                continue
                
            score = self._calculate_news_quality_score(item)
            # Lowered threshold slightly to ensure more items pass
            if score >= 1.5 and not self.is_duplicate(item.get("title", "")):
                item["impact_score"] = score
                scored_items.append(item)
        
        scored_items.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
        logger.info(f"✅ Filtered and scored {len(scored_items)} relevant news items")
        
        # Use diversity selection logic
        return self.select_top_items_with_diversity([], scored_items, total_items)

    def _calculate_news_quality_score(self, item: Dict) -> int:
        """Calculate quality score for a news item."""
        score = 2.0 # Base score
        text = (item.get("title", "") + (item.get("summary", "") or "")).lower()
        
        if re.search(r"\$\d{2,}[mb]|billion|million", text):
            score += 3.0
        if re.search(r"surge|plummet|crash|rally|breakout|ath|all-time high|slips|below|above", text):
            score += 2.0
        for keyword, multiplier in CONTENT_KEYWORD_MULTIPLIERS.items():
            if re.search(rf"\b{keyword}\b", text):
                score *= multiplier
        source = item.get("source", "").lower()
        if any(s in source for s in ["coindesk", "cointelegraph", "the block", "decrypt", "bloomberg", "reuters"]):
            score += 2.0
            
        return int(min(score, 10))

    def _categorize_news(self, item: Dict) -> str:
        """Categorize a news item."""
        text = (item.get("title", "") + (item.get("summary", "") or "")).lower()
        if re.search(r"inflow|outflow|whale|transfer|drain|hack|exploit|funding|raised|investment|venture|capital|seed round", text):
            return "capital_flow"
        if re.search(r"sec|regulation|law|policy|etf|fed|central bank|government|court|lawsuit|legal", text):
            return "macro_policy"
        if re.search(r"\bbitcoin\b|\bbtc\b|\bethereum\b|\beth\b|\bsolana\b|\bsol\b", text):
            return "major_coins"
        if re.search(r"altcoin|token|memecoin|trending|surge|pump|listing", text):
            return "altcoins_trending"
        if re.search(r"layer|l2|defi|rwa|ai|zk|protocol|infrastructure|mainnet|testnet|upgrade", text):
            return "tech_narratives"
        return "macro_policy"

    def select_top_items_with_diversity(self, kol_posts: List[Dict], news_items: List[Dict], total_items: int = 5) -> List[Dict]:
        """Select top items ensuring category diversity."""
        selected = []
        category_count = {cat: 0 for cat in self.VALID_CATEGORIES.keys()}
        
        if kol_posts:
            kol_item = kol_posts[0]
            kol_item["category"] = "kol_insights"
            kol_item["source_name"] = kol_item.get("username", "Unknown")
            if "summary" not in kol_item and "text" in kol_item:
                kol_item["summary"] = kol_item["text"]
            selected.append(kol_item)
            category_count["kol_insights"] = 1
        
        categorized_news = {cat: [] for cat in self.VALID_CATEGORIES.keys() if cat != "kol_insights"}
        for item in news_items:
            category = self._categorize_news(item)
            if category in categorized_news:
                categorized_news[category].append(item)
        
        news_categories = [cat for cat in self.VALID_CATEGORIES.keys() if cat != "kol_insights"]
        for category in news_categories:
            if len(selected) >= total_items: break
            if category_count[category] < 1 and categorized_news[category]:
                item = categorized_news[category].pop(0)
                item["category"] = category
                item["source_name"] = item.get("source", "Unknown")
                selected.append(item)
                category_count[category] = 1
        
        all_remaining = []
        for cat, items in categorized_news.items():
            for item in items:
                item["category"] = cat
                all_remaining.append(item)
        all_remaining.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
        
        for item in all_remaining:
            if len(selected) >= total_items: break
            category = item["category"]
            if category_count[category] < 2:
                item["source_name"] = item.get("source", "Unknown")
                selected.append(item)
                category_count[category] += 1
                
        return selected[:total_items]

    def is_duplicate(self, text: str) -> bool:
        """Check if content is duplicate."""
        for cached_item in self.published_cache.values():
            similarity = SequenceMatcher(None, text.lower(), cached_item.get("text", "").lower()).ratio()
            if similarity >= 0.7: return True
        return False

    def add_to_cache(self, item: Dict) -> None:
        """Add published item to cache."""
        cache_key = f"{item.get('category', 'unknown')}_{datetime.now().isoformat()}"
        self.published_cache[cache_key] = {
            "text": item.get("title", ""),
            "timestamp": datetime.now().isoformat(),
            "category": item.get("category", ""),
        }
        self._save_cache()
