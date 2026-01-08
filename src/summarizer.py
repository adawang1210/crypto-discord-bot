"""
Content summarizer module for Crypto Morning Pulse Bot.
Rewrites extracted content into concise, high-quality summaries in Traditional Chinese.
"""

import asyncio
import aiohttp
import re
from typing import Optional, Dict, List
from src.logger import logger


class ContentSummarizer:
    """Summarizes and rewrites content into concise Chinese summaries."""
    
    def __init__(self):
        """Initialize content summarizer."""
        self.session: Optional[aiohttp.ClientSession] = None
        # Using a free summarization API or local logic
        self.summarize_url = "https://api.cohere.com/v1/summarize"  # Fallback to local logic
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _extract_key_info(self, text: str, title: str) -> Dict[str, str]:
        """
        Extract key information from text: who, what, impact.
        
        Args:
            text: Article text to analyze.
            title: Article title.
        
        Returns:
            Dict with 'subject', 'action', 'impact' keys.
        """
        info = {
            "subject": "",
            "action": "",
            "impact": ""
        }
        
        try:
            # Clean text
            text = text.strip()
            sentences = re.split(r'[.!?]\s+', text)
            
            if not sentences:
                return info
            
            # First sentence usually contains the main subject and action
            if len(sentences) > 0:
                first_sent = sentences[0].strip()
                info["action"] = first_sent[:150]  # Main action
            
            # Look for impact in subsequent sentences
            for sent in sentences[1:3]:
                sent = sent.strip()
                if any(keyword in sent.lower() for keyword in ['rise', 'fall', 'surge', 'crash', 'impact', 'affect', 'lead', 'result', 'cause']):
                    info["impact"] = sent[:100]
                    break
            
            # Extract subject from title or first sentence
            # Common patterns: "Company/Person does something"
            title_words = title.split()
            if len(title_words) > 0:
                # Usually first 2-3 words contain the subject
                info["subject"] = " ".join(title_words[:3])
            
            return info
        
        except Exception as e:
            logger.debug(f"Error extracting key info: {str(e)}")
            return info
    
    def _rewrite_summary(
        self,
        title: str,
        text: str,
        category: str
    ) -> str:
        """
        Rewrite content into a concise 1-2 sentence summary in Traditional Chinese.
        
        Args:
            title: Article title.
            text: Article text.
            category: Content category.
        
        Returns:
            str: Rewritten summary in Traditional Chinese.
        """
        try:
            # Extract key information
            info = self._extract_key_info(text, title)
            
            # Build summary based on category
            summary = ""
            
            if category == "macro_policy":
                # Format: "政策/事件 + 影響"
                if info["action"]:
                    summary = info["action"]
                    if info["impact"]:
                        summary += f"，{info['impact']}"
            
            elif category == "capital_flow":
                # Format: "資金流向 + 數量/影響"
                if "drain" in text.lower() or "flow" in text.lower():
                    summary = info["action"]
                    if info["impact"]:
                        summary += f"，{info['impact']}"
            
            elif category == "major_coins":
                # Format: "代幣 + 價格/活動變化"
                if info["action"]:
                    summary = info["action"]
                    if info["impact"]:
                        summary += f"，{info['impact']}"
            
            elif category == "altcoins_trending":
                # Format: "代幣 + 趨勢/原因"
                if info["action"]:
                    summary = info["action"]
                    if info["impact"]:
                        summary += f"，{info['impact']}"
            
            elif category == "tech_narratives":
                # Format: "技術/敘事 + 進展"
                if info["action"]:
                    summary = info["action"]
                    if info["impact"]:
                        summary += f"，{info['impact']}"
            
            elif category == "kol_insights":
                # Format: "KOL + 觀點/行動"
                if info["action"]:
                    summary = info["action"]
                    if info["impact"]:
                        summary += f"，{info['impact']}"
            
            # Limit to 200-280 characters
            if len(summary) > 280:
                summary = summary[:277] + "..."
            
            return summary.strip()
        
        except Exception as e:
            logger.debug(f"Error rewriting summary: {str(e)}")
            return ""
    
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
            
            # Rewrite summary
            rewritten = self._rewrite_summary(title, summary, category)
            
            if rewritten and len(rewritten) > 20:
                item["summary_rewritten"] = rewritten
                logger.info(f"✅ Rewritten summary: {rewritten[:50]}...")
            
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
                asyncio.wait_for(
                    self.summarize_item(item, cat),
                    timeout=5
                )
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
