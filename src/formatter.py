"""
Discord formatter module for Crypto Morning Pulse Bot.
Implements the new layout with Market Overview, News, and X Trending.
"""

from datetime import datetime
import discord
from typing import List, Dict


class DiscordFormatter:
    """Formats crypto data into the new Discord embed layout."""
    
    @staticmethod
    def format_currency(value: float) -> str:
        """Format large numbers into $X.XXT or $XX.XX億."""
        if value >= 1e12:
            return f"${value/1e12:.2f}T"
        elif value >= 1e8:
            return f"${value/1e8:.2f}億"
        elif value >= 1e4:
            return f"${value/1e4:.2f}萬"
        return f"${value:,.2f}"

    @staticmethod
    def create_daily_briefing_embed(data: Dict) -> discord.Embed:
        """Create the new structured daily briefing embed."""
        now = datetime.now()
        date_str = now.strftime("%b %d, %2026")
        
        embed = discord.Embed(
            title=f"Crypto Morning Pulse | {date_str}",
            description="Here's what's moving markets today",
            color=0xF7931A,
            timestamp=now
        )
        
        # 1. Market Overview
        overview = data.get('market_overview', {})
        btc = overview.get('btc', {})
        eth = overview.get('eth', {})
        xrp = overview.get('xrp', {})
        
        market_text = (
            f"• BTC: ${btc.get('usd', 0):,.0f} ({btc.get('usd_24h_change', 0):+.1f}%)\n"
            f"• ETH: ${eth.get('usd', 0):,.0f} ({eth.get('usd_24h_change', 0):+.1f}%)\n"
            f"• XRP: ${xrp.get('usd', 0):.2f} ({xrp.get('usd_24h_change', 0):+.1f}%)\n"
            f"• 總市值: {DiscordFormatter.format_currency(overview.get('total_market_cap', 0))} ({overview.get('market_cap_change', 0):+.1f}%)\n"
            f"• 恐懼貪婪指數: {overview.get('fng_value', 'N/A')} ({overview.get('fng_classification', 'N/A')})"
        )
        embed.add_field(name="**市場概況** (過去24小時)", value=market_text, inline=False)
        
        # Visual Separator
        embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
        
        # 2. Market Dynamics (News)
        news_items = data.get('news_items', [])
        categories = {
            "macro_policy": "Macro/Policy",
            "capital_flow": "Capital Flow",
            "major_coins": "Major Coins",
            "altcoins_trending": "Altcoins/Trending",
            "tech_narratives": "Tech/Narratives"
        }
        
        news_text = ""
        # Group news by category (simplified for now)
        for item in news_items[:4]:
            cat_name = categories.get(item.get('category', 'macro_policy'), "Macro/Policy")
            summary = item.get('summary_rewritten', item.get('title', ''))
            source = item.get('source', 'Unknown')
            news_text += f"**{cat_name}**\n• {summary} | {source}\n\n"
        
        if news_text:
            embed.add_field(name="**市場動態**", value=news_text, inline=False)
            
        # Visual Separator
        embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━━━━━━", inline=False)
        
        # 3. X Trending Posts
        x_posts = data.get('x_posts', [])
        x_text = ""
        for post in x_posts[:5]:
            x_text += f"• **[@{post['username']}]** - {post['text']} | 互動數: {post['likes']} likes\n"
            
        if x_text:
            embed.add_field(name="**社群焦點**\n\nX Trending Posts", value=x_text, inline=False)
            
        # Footer
        embed.set_footer(
            text=f"Powered by Manus AI | Data: X, CryptoPanic, CoinGecko\nGenerated at: {now.strftime('%H:%M')} UTC+8"
        )
        
        return embed
