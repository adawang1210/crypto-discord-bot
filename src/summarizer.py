"""
Content summarizer module for Crypto Morning Pulse Bot.
Rewrites extracted content into concise, high-quality summaries in Traditional Chinese.
"""

import asyncio
import aiohttp
import re
import os
from typing import Optional, Dict, List
from openai import OpenAI
from src.logger import logger


class ContentSummarizer:
    """Summarizes and rewrites content into concise Chinese summaries."""
    
    def __init__(self):
        """Initialize content summarizer."""
        self.client = OpenAI() # Uses environment variables for API key and base URL
    
    async def _rewrite_with_llm(self, title: str, text: str, category: str) -> str:
        """
        Use LLM to rewrite the summary in Traditional Chinese.
        """
        prompt = f"""
你是一個專業的加密貨幣新聞編輯。請將以下新聞內容改寫為一段簡潔的繁體中文摘要。

要求：
1. 長度：1-2 句話，總字數在 200-280 字元之間。
2. 重點：突出「誰做了什麼」以及「影響是什麼」。
3. 語言：使用繁體中文，但保留專有名詞（如公司名、代幣名、人名）為英文。
4. 風格：不要直接複製原文，要用自己的話重新表述。
5. 類別：{category}

新聞標題：{title}
新聞內容：{text}

請直接輸出改寫後的摘要，不要包含任何其他文字。
"""
        try:
            # Run in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": "你是一個專業的加密貨幣新聞編輯，擅長撰寫簡潔、專業的繁體中文摘要。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            logger.error(f"Error calling LLM for summarization: {str(e)}")
            return ""

    def _rewrite_summary_local(
        self,
        title: str,
        text: str,
        category: str
    ) -> str:
        """
        Fallback local logic for rewriting summary if LLM fails.
        """
        # Simple extraction logic as a fallback
        summary = f"{title}。{text[:100]}"
        if len(summary) > 280:
            summary = summary[:277] + "..."
        return summary

    async def summarize_item(
        self,
        item: Dict,
        category: str
    ) -> Dict:
        """
        Summarize a content item with rewritten summary.
        
        Args:
            item: Content item to summarize.
            category: Content category.
        
        Returns:
            Dict: Item with 'summary_rewritten' field.
        """
        try:
            title = item.get("title", "")
            summary = item.get("summary", "")
            
            if not title or not summary:
                return item
            
            # Rewrite summary using LLM
            rewritten = await self._rewrite_with_llm(title, summary, category)
            
            # Fallback if LLM fails
            if not rewritten:
                rewritten = self._rewrite_summary_local(title, summary, category)
            
            if rewritten:
                item["summary_rewritten"] = rewritten
                logger.info(f"✅ Rewritten summary for: {title[:30]}...")
            
            return item
        
        except Exception as e:
            logger.error(f"Error summarizing item: {str(e)}")
            return item
    
    async def summarize_items(
        self,
        items: List[Dict],
        categories: List[str]
    ) -> List[Dict]:
        """
        Summarize multiple items with their categories.
        
        Args:
            items: List of items to summarize.
            categories: List of categories corresponding to items.
        
        Returns:
            List[Dict]: List of summarized items.
        """
        try:
            tasks = [
                self.summarize_item(item, cat)
                for item, cat in zip(items, categories)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            final_items = []
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Error summarizing item {idx}: {str(result)}")
                    final_items.append(items[idx])
                else:
                    final_items.append(result)
            
            logger.info(f"✅ Summarized {len(final_items)} items")
            return final_items
        
        except Exception as e:
            logger.error(f"Error in summarize_items: {str(e)}")
            return items
