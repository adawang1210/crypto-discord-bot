"""
Discord formatter module for Crypto Morning Pulse Bot.
Optimized for clean links, continuous numbering, and dynamic batching to respect Discord's 2000 char limit.
Removed image display logic as per user request.
"""

from datetime import datetime
from typing import List, Dict
import pytz
from src.config import TIMEZONE


class DiscordFormatter:
    """Formats crypto data into clean batches for Discord."""
    
    @staticmethod
    def truncate(text: str, limit: int) -> str:
        """Truncate text to a specific limit with ellipsis."""
        if not text: return ""
        return (text[:limit-3] + "...") if len(text) > limit else text

    @staticmethod
    def format_currency(value: float) -> str:
        """Format large numbers into $X.XXT or $XX.XX億."""
        if value >= 1e12: return f"${value/1e12:.2f}T"
        elif value >= 1e8: return f"${value/1e8:.2f}億"
        elif value >= 1e4: return f"${value/1e4:.2f}萬"
        return f"${value:,.2f}"

    @staticmethod
    def create_batches(data: Dict) -> List[str]:
        """Create message batches with dynamic character counting to respect Discord's 2000 limit."""
        now = datetime.now(pytz.timezone(TIMEZONE))
        date_str = now.strftime("%b %d, %Y")
        batches = []
        current_batch = ""
        limit = 1900 # Safe limit slightly below 2000

        def add_to_batch(text: str):
            nonlocal current_batch, batches
            if len(current_batch) + len(text) > limit:
                batches.append(current_batch.strip())
                current_batch = text
            else:
                current_batch += text

        # --- Part 1: Header & Market Overview & Today's Focus ---
        overview = data.get('market_overview', {})
        btc = overview.get('btc', {})
        eth = overview.get('eth', {})
        xrp = overview.get('xrp', {})
        todays_focus = data.get('todays_focus', "市場動態觀察中。")
        
        header = (
            f"**Crypto Morning Pulse | {date_str}**\n"
            f"*Here's what's moving markets today*\n\n"
            f"**市場概況** (過去24小時)\n"
            f"• BTC: ${btc.get('usd', 0):,.0f} ({btc.get('usd_24h_change', 0):+.1f}%)\n"
            f"• ETH: ${eth.get('usd', 0):,.0f} ({eth.get('usd_24h_change', 0):+.1f}%)\n"
            f"• XRP: ${xrp.get('usd', 0):.2f} ({xrp.get('usd_24h_change', 0):+.1f}%)\n"
            f"• 總市值: {DiscordFormatter.format_currency(overview.get('total_market_cap', 0))} ({overview.get('market_cap_change', 0):+.1f}%)\n"
            f"• 恐懼貪婪指數: {overview.get('fng_value', 'N/A')} ({overview.get('fng_classification', 'N/A')})\n\n"
            f"**今日重點:** {todays_focus}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        add_to_batch(header)

        # --- Part 2: Market Dynamics (News) ---
        add_to_batch("**Market Dynamics**\n\n")
        news_items = data.get('news_items', [])
        categories = {
            "macro_policy": "Macro/Policy",
            "capital_flow": "Capital Flow",
            "major_coins": "Major Coins",
            "altcoins_trending": "Altcoins/Trending",
            "tech_narratives": "Tech/Narratives"
        }
        
        grouped_news = {cat: [] for cat in categories.keys()}
        for item in news_items:
            cat = item.get('category', 'macro_policy')
            if cat in grouped_news:
                grouped_news[cat].append(item)
        
        news_counter = 1
        for cat_id, cat_name in categories.items():
            items = grouped_news[cat_id]
            if not items: continue
            
            add_to_batch(f"**{cat_name}**\n")
            for item in items:
                summary = item.get('summary_rewritten', item.get('title', ''))
                source = item.get('source', 'Unknown')
                url = item.get('url', '')
                
                # Format: 1. **[關鍵詞]** - [摘要] | 來源 | [連結](URL)
                # Removed image [📷] logic
                line = f"{news_counter}. {summary} | {source} | [連結]({url})"
                add_to_batch(line + "\n")
                news_counter += 1
            add_to_batch("\n")
        
        add_to_batch("━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")

        # --- Part 3: Community Spotlight (X Posts) ---
        add_to_batch("**Community Spotlight**\n\n**X Trending Posts**\n")
        x_posts = data.get('x_posts', [])
        for i, post in enumerate(x_posts[:5], 1):
            line = f"{i}. **[@{post['username']}]** - {post['text']} | 互動數: {post['likes']} likes | [貼文連結]({post['url']})\n"
            add_to_batch(line)
            
        # --- Footer ---
        footer = (
            f"\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Powered by Manus AI | Data: X, CryptoPanic, CoinGecko\n"
            f"Generated at: {now.strftime('%H:%M')} UTC+8"
        )
        add_to_batch(footer)

        # Finalize batches
        if current_batch:
            batches.append(current_batch.strip())
            
        return batches
