"""
Content enhancer module for Crypto Morning Pulse Bot.
Handles translation, summarization, and image extraction.
"""

import asyncio
import aiohttp
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
import re

from src.logger import logger


class ContentEnhancer:
    """Enhances content with translations, summaries, and images."""
    
    def __init__(self):
        """Initialize content enhancer."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.translate_url = "https://api.mymemory.translated.net/get"
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def translate_to_chinese(self, text: str) -> str:
        """
        Translate text to Traditional Chinese using free API.
        
        Args:
            text: Text to translate.
        
        Returns:
            str: Translated text or original if translation fails.
        """
        if not text or len(text) < 3:
            return text
        
        try:
            if not self.session:
                raise RuntimeError("Session not initialized. Use async context manager.")
            
            # Limit text to 500 characters for API
            text_to_translate = text[:500]
            
            params = {
                "q": text_to_translate,
                "langpair": "en|zh-TW"
            }
            
            async with self.session.get(
                self.translate_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("responseStatus") == 200:
                        translated = data.get("responseData", {}).get("translatedText", "")
                        if translated:
                            logger.debug(f"Translated: {text[:50]}... -> {translated[:50]}...")
                            return translated
        
        except Exception as e:
            logger.debug(f"Translation error: {str(e)}")
        
        return text
    
    async def extract_summary(
        self,
        html_content: str,
        max_length: int = 150
    ) -> str:
        """
        Extract summary from HTML content.
        
        Args:
            html_content: HTML content to extract from.
            max_length: Maximum length of summary in characters.
        
        Returns:
            str: Extracted summary.
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find article content
            article_text = ""
            
            # Try common article containers
            for selector in ["article", ".article-content", ".post-content", ".entry-content", "main"]:
                element = soup.select_one(selector)
                if element:
                    article_text = element.get_text()
                    break
            
            # Fallback to body if no article found
            if not article_text:
                body = soup.find("body")
                if body:
                    article_text = body.get_text()
            
            # Clean up text
            article_text = re.sub(r"\s+", " ", article_text).strip()
            
            # Extract first sentences to reach max_length
            sentences = re.split(r"(?<=[.!?])\s+", article_text)
            summary = ""
            
            for sentence in sentences:
                if len(summary) + len(sentence) <= max_length:
                    summary += sentence + " "
                else:
                    break
            
            summary = summary.strip()
            
            # Ensure we have at least some content
            if not summary:
                summary = article_text[:max_length]
            
            logger.debug(f"Extracted summary: {summary[:50]}...")
            return summary
        
        except Exception as e:
            logger.debug(f"Summary extraction error: {str(e)}")
            return ""
    
    async def extract_image(self, html_content: str) -> Optional[str]:
        """
        Extract first image URL from HTML content.
        
        Args:
            html_content: HTML content to extract from.
        
        Returns:
            Optional[str]: Image URL or None if not found.
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Try to find Open Graph image first
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                image_url = og_image.get("content")
                logger.debug(f"Found OG image: {image_url[:50]}...")
                return image_url
            
            # Try to find first image in article
            article = soup.find("article") or soup.find("main") or soup.find("body")
            if article:
                img = article.find("img")
                if img and img.get("src"):
                    image_url = img.get("src")
                    # Convert relative URLs to absolute if needed
                    if image_url.startswith("/"):
                        # Can't convert without base URL, skip
                        pass
                    elif image_url.startswith("http"):
                        logger.debug(f"Found article image: {image_url[:50]}...")
                        return image_url
            
            # Try any image on page
            img = soup.find("img")
            if img and img.get("src"):
                image_url = img.get("src")
                if image_url.startswith("http"):
                    logger.debug(f"Found page image: {image_url[:50]}...")
                    return image_url
        
        except Exception as e:
            logger.debug(f"Image extraction error: {str(e)}")
        
        return None
    
    async def enhance_item(self, item: Dict) -> Dict:
        """
        Enhance a content item with translation, summary, and image.
        
        Args:
            item: Content item to enhance.
        
        Returns:
            Dict: Enhanced item with title_zh, summary, and image_url.
        """
        try:
            # Translate title
            title = item.get("title", "")
            title_zh = await self.translate_to_chinese(title)
            item["title_zh"] = title_zh
            
            # Extract summary and image from URL if available
            url = item.get("url", "")
            if url:
                try:
                    async with self.session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=10),
                        ssl=False
                    ) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            
                            # Extract summary
                            summary = await self.extract_summary(html_content, max_length=150)
                            if summary:
                                item["summary"] = summary
                            
                            # Extract image
                            image_url = await self.extract_image(html_content)
                            if image_url:
                                item["image_url"] = image_url
                except Exception as e:
                    logger.debug(f"Error fetching URL {url}: {str(e)}")
            
            return item
        
        except Exception as e:
            logger.error(f"Error enhancing item: {str(e)}")
            return item
    
    async def enhance_items(self, items: List[Dict]) -> List[Dict]:
        """
        Enhance multiple items in parallel.
        
        Args:
            items: List of items to enhance.
        
        Returns:
            List[Dict]: List of enhanced items.
        """
        tasks = [self.enhance_item(item) for item in items]
        enhanced_items = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        result = []
        for item in enhanced_items:
            if isinstance(item, Exception):
                logger.error(f"Error enhancing item: {str(item)}")
            else:
                result.append(item)
        
        return result
