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
        """
        Translate text to Traditional Chinese using free MyMemory API.
        """
        if not text:
            return ""
        
        try:
            # Limit text length for free API
            text_to_translate = text[:500]
            params = {
                "q": text_to_translate,
                "langpair": "en|zh-TW"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.translate_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("responseStatus") == 200:
                            return data.get("responseData", {}).get("translatedText", "")
        except Exception as e:
            logger.warning(f"Translation error in summarizer: {str(e)}")
        
        return text

    def _extract_key_sentences(self, text: str) -> str:
        """
        Extract 1-2 key sentences from the text.
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if not sentences:
            return text
        
        # Take the first sentence as it usually contains the main point
        summary = sentences[0]
        
        # If the first sentence is too short, try to add the second one
        if len(summary) < 100 and len(sentences) > 1:
            summary += " " + sentences[1]
            
        return summary

    async def summarize_item(
        self,
        item: Dict,
        category: str
    ) -> Dict:
        """
        Summarize a content item using local logic and translation.
        
        Args:
            item: Content item to summarize.
            category: Content category.
        
        Returns:
            Dict: Item with 'summary_rewritten' field.
        """
        try:
            title = item.get("title", "")
            content = item.get("summary", "") or item.get("text", "")
            
            if not title:
                return item
            
            # 1. Extract key sentences from English content
            english_summary = self._extract_key_sentences(content if len(content) > 50 else title)
            
            # 2. Translate title and summary to Traditional Chinese
            title_zh = await self._translate_text(title)
            summary_zh = await self._translate_text(english_summary)
            
            # 3. Combine and format
            # We want: "誰做了什麼 + 影響"
            # Local logic: use translated title as the main action, and summary as detail
            rewritten = f"{title_zh}。{summary_zh}"
            
            # Clean up: remove extra spaces and ensure it's not too long
            rewritten = re.sub(r'\s+', ' ', rewritten).strip()
            if len(rewritten) > 280:
                rewritten = rewritten[:277] + "..."
            
            item["summary_rewritten"] = rewritten
            logger.info(f"✅ Locally rewritten summary for: {title[:30]}...")
            
            return item
        
        except Exception as e:
            logger.error(f"Error in local summarization: {str(e)}")
            return item
    
    async def summarize_items(
        self,
        items: List[Dict],
        categories: List[str]
    ) -> List[Dict]:
        """
        Summarize multiple items.
        """
        tasks = [
            self.summarize_item(item, cat)
            for item, cat in zip(items, categories)
        ]
        return await asyncio.gather(*tasks)
