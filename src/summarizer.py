"""
Content summarizer module for Crypto Morning Pulse Bot.
Rewrites extracted content into concise, high-quality summaries in Traditional Chinese.
Includes logic for generating a 150-word "Today's Focus" summary.
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
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _translate_text(self, text: str) -> str:
        """Translate text to Traditional Chinese using free MyMemory API."""
        if not text:
            return ""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        try:
            text_to_translate = text[:500]
            params = {"q": text_to_translate, "langpair": "en|zh-TW"}
            async with self.session.get(self.translate_url, params=params, timeout=10) as response:
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
        text = re.sub(r"\$(\d+(?:\.\d+)?)\s*billion", lambda m: f"${float(m.group(1)):.2f}億", text, flags=re.IGNORECASE)
        text = re.sub(r"\$(\d+(?:\.\d+)?)\s*million", lambda m: f"${float(m.group(1)):.2f}萬", text, flags=re.IGNORECASE)
        text = re.sub(r"(\d+(?:\.\d+)?)\s*%", lambda m: f"{float(m.group(1)):.1f}%", text)
        return text

    async def generate_todays_focus(self, market_data: Dict, news_items: List[Dict]) -> str:
        """Generate a 150-word summary of today's market focus."""
        btc_change = market_data.get('btc', {}).get('usd_24h_change', 0)
        fng_val = market_data.get('fng_value', 'N/A')
        fng_class = market_data.get('fng_classification', 'N/A')
        
        price_trend = "上漲" if btc_change > 0 else "下跌"
        sentiment = "樂觀" if "Greed" in fng_class else "恐慌" if "Fear" in fng_class else "謹慎"
        
        top_news = news_items[0].get('title', '') if news_items else "市場動態平穩"
        top_news_zh = await self._translate_text(top_news)
        
        focus = (
            f"比特幣今日呈現{price_trend}走勢，目前在${market_data.get('btc', {}).get('usd', 0):,.0f}附近波動，"
            f"主要受到市場對{top_news_zh[:30]}的關注影響。ETH和XRP也隨之波動，顯示出整體市場的連動性。"
            f"恐懼貪婪指數目前為{fng_val}，顯示市場情緒處於{fng_class}狀態，投資人表現出{sentiment}態度。"
            f"重大新聞方面，{top_news_zh}引發了廣泛討論。整體而言，短期市場呈現{sentiment}觀望態勢，"
            f"建議投資人密切關注後續政策動向與資金流向，保持資產配置的靈活性。"
        )
        
        if len(focus) > 160:
            focus = focus[:157] + "。"
        elif len(focus) < 140:
            focus += "市場參與者正等待更多宏觀經濟數據公佈，以判斷下一階段的方向。"
            
        return focus

    async def summarize_item(self, item: Dict, category: str) -> Dict:
        """Summarize and format news item with keywords."""
        try:
            title = item.get("title", "")
            content = item.get("summary", "") or item.get("text", "")
            keyword = self._extract_keywords(title + " " + content)
            title_zh = await self._translate_text(title)
            title_zh = self._format_financials(title_zh)
            item["summary_rewritten"] = f"**{keyword}** - {title_zh}"
            return item
        except Exception as e:
            logger.error(f"Error in summarization: {str(e)}")
            return item
    
    async def summarize_items(self, items: List[Dict], categories: List[str]) -> List[Dict]:
        """Summarize multiple items."""
        tasks = [self.summarize_item(item, cat) for item, cat in zip(items, categories)]
        return await asyncio.gather(*tasks)
