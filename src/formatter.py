"""
Discord formatter module for Crypto Morning Pulse Bot.
Implements batch output, continuous numbering, and the new "Today's Focus" section.
"""

from datetime import datetime
from typing import List, Dict


class DiscordFormatter:
    """Formats crypto data into batches for Discord's 2000 character limit."""
    
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
        """Create three batches of messages as requested."""
        now = datetime.now()
        date_str = now.strftime("%b %d, %Y")
        batches = []
        
        # --- Batch 1: Market Overview + Today's Focus ---
        overview = data.get('market_overview', {})
        btc = overview.get('btc', {})
        eth = overview.get('eth', {})
        xrp = overview.get('xrp', {})
        todays_focus = data.get('todays_focus', "市場動態觀察中。")
        
        batch1 = (
            f"Crypto Morning Pulse | {date_str}\n"
            f"Here's what's moving markets today\n\n"
            f"**市場概況** (過去24小時)\n"
            f"• BTC: ${btc.get('usd', 0):,.0f} ({btc.get('usd_24h_change', 0):+.1f}%)\n"
            f"• ETH: ${eth.get('usd', 0):,.0f} ({eth.get('usd_24h_change', 0):+.1f}%)\n"
            f"• XRP: ${xrp.get('usd', 0):.2f} ({xrp.get('usd_24h_change', 0):+.1f}%)\n"
            f"• 總市值: {DiscordFormatter.format_currency(overview.get('total_market_cap', 0))} ({overview.get('market_cap_change', 0):+.1f}%)\n"
            f"• 恐懼貪婪指數: {overview.get('fng_value', 'N/A')} ({overview.get('fng_classification', 'N/A')})\n\n"
            f"**今日重點:** {todays_focus}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"[續下則訊息...]"
        )
        batches.append(batch1)
        
        # --- Batch 2: Market Dynamics (News) ---
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
        
        batch2 = "**Market Dynamics**\n\n"
        news_counter = 1
        for cat_id, cat_name in categories.items():
            items = grouped_news[cat_id]
            if not items: continue
            
            batch2 += f"**{cat_name}**\n"
            for item in items:
                summary = item.get('summary_rewritten', item.get('title', ''))
                source = item.get('source', 'Unknown')
                url = item.get('url', '')
                img_url = item.get('image_url', '')
                
                # Format: 1. **[關鍵詞]** - [摘要] | 來源 | [連結](URL) | [📷](IMG_URL)
                line = f"{news_counter}. {summary} | {source} | [連結]({url})"
                if img_url:
                    line += f" | [📷]({img_url})"
                batch2 += line + "\n"
                news_counter += 1
            batch2 += "\n"
        
        batch2 += "━━━━━━━━━━━━━━━━━━━━━━━━━\n[續下則訊息...]"
        batches.append(batch2)
        
        # --- Batch 3: Community Spotlight (X Posts) ---
        x_posts = data.get('x_posts', [])
        batch3 = "**Community Spotlight**\n\n**X Trending Posts**\n"
        for i, post in enumerate(x_posts[:5], 1):
            # Format: 1. **[@用戶名]** - [摘要] | 互動數: XXk likes | [連結](URL)
            batch3 += f"{i}. **[@{post['username']}]** - {post['text']} | 互動數: {post['likes']} likes | [貼文連結]({post['url']})\n"
            
        batch3 += (
            f"\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Powered by Manus AI | Data: X, CryptoPanic, CoinGecko\n"
            f"Generated at: {now.strftime('%H:%M')} UTC+8"
        )
        batches.append(batch3)
        
        return batches
