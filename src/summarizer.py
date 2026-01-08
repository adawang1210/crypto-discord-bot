"""
Content summarizer module for Crypto Morning Pulse Bot.
Rewrites extracted content into concise, high-quality summaries in Traditional Chinese.
Uses local logic and free translation APIs instead of OpenAI.
"""

import asyncio
import aiohttp
import re
from typing import Optional, Dict, List
from src.logger import logger


class ContentSummarizer:
    """Summarizes and rewrites content into concise Chinese summaries without OpenAI."""
    
    def __init__(self):
        """Initialize content summarizer."""
        self.translate_url = "https://api.mymemory.translated.net/get"
    
    async def _translate_text(self, text: str) -> str:
        """Translate text to Traditional Chinese using free MyMemory API."""
        if not text:
            return ""
        try:
            text_to_translate = text[:500]
            params = {"q": text_to_translate, "langpair": "en|zh-TW"}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.translate_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("responseStatus") == 200:
                            return data.get("responseData", {}).get("translatedText", "")
        except Exception: pass
        return text

    def _extract_keywords(self, text: str) -> str:
        """Extract the most important keyword (Subject/Coin/Entity) from text."""
        entities = [
            "Bitcoin", "BTC", "Ethereum", "ETH", "XRP", "Ripple", "Solana", "SOL",
            "SEC", "ETF", "Binance", "Coinbase", "MicroStrategy", "Vitalik", "CZ",
            "Fed", "Regulation", "Hack", "Exploit", "Zcash", "ZEC", "Nike", "RTFKT"
        ]
        for entity in entities:
            if re.search(rf"\b{entity}\b", text, re.IGNORECASE):
                return entity
        match = re.search(r"\b[A-Z][a-z]+\b", text)
        return match.group(0) if match else "加密貨幣"

    def _format_financials(self, text: str) -> str:
        """Format currency and percentages as requested."""
        # Format billions/millions
        text = re.sub(r"\$(\d+(?:\.\d+)?)\s*billion", lambda m: f"${float(m.group(1)):.2f}億", text, flags=re.IGNORECASE)
        text = re.sub(r"\$(\d+(?:\.\d+)?)\s*million", lambda m: f"${float(m.group(1)):.2f}萬", text, flags=re.IGNORECASE)
        # Format percentages
        text = re.sub(r"(\d+(?:\.\d+)?)\s*%", lambda m: f"{float(m.group(1)):.1f}%", text)
        return text

    async def summarize_item(self, item: Dict, category: str) -> Dict:
        """Summarize and format news item with keywords."""
        try:
            title = item.get("title", "")
            content = item.get("summary", "") or item.get("text", "")
            
            # 1. Extract Keyword
            keyword = self._extract_keywords(title + " " + content)
            
            # 2. Translate
            title_zh = await self._translate_text(title)
            
            # 3. Format Financials
            title_zh = self._format_financials(title_zh)
            
            # 4. Final Assembly: **[關鍵詞]** - [摘要]
            item["summary_rewritten"] = f"**{keyword}** - {title_zh}"
            return item
        except Exception as e:
            logger.error(f"Error in summarization: {str(e)}")
            return item
    
    async def summarize_items(self, items: List[Dict], categories: List[str]) -> List[Dict]:
        """Summarize multiple items."""
        tasks = [self.summarize_item(item, cat) for item, cat in zip(items, categories)]
        return await asyncio.gather(*tasks)
