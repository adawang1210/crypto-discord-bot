"""
Formatter module for Crypto Morning Pulse Bot.
Handles Discord embed formatting and message composition.
"""

from typing import List, Dict, Optional
from datetime import datetime
import discord

from src.config import (
    EMBED_COLOR,
    EMBED_TITLE_FORMAT,
    EMBED_DESCRIPTION,
    EMBED_FOOTER_TEXT,
    CATEGORY_EMOJIS,
    TIMEZONE,
)
from src.logger import logger


class DiscordFormatter:
    """Formats content into Discord embeds and messages."""
    
    @staticmethod
    def create_daily_briefing_embed(
        items: List[Dict],
        degraded_mode: bool = False
    ) -> discord.Embed:
        """
        Create a Discord embed for the daily crypto briefing.
        
        Args:
            items: List of selected news/KOL items to include.
            degraded_mode: Whether to include degradation warning.
        
        Returns:
            discord.Embed: Formatted Discord embed.
        """
        # Create embed with title and basic info
        now = datetime.now()
        date_str = now.strftime("%b %d, %Y")
        
        embed = discord.Embed(
            title=EMBED_TITLE_FORMAT.format(date=date_str),
            description=EMBED_DESCRIPTION,
            color=EMBED_COLOR,
            timestamp=now
        )
        
        # Add items as fields
        for idx, item in enumerate(items, 1):
            # Determine category based on item type
            item_type = item.get("type", "news")
            if item_type == "trending":
                category = "trending"
            else:
                category = item.get("category", "macro_policy")
            
            emoji = CATEGORY_EMOJIS.get(category, "📰")
            category_name = DiscordFormatter._format_category_name(category)
            
            # Prepare summary text
            summary = item.get("title", item.get("text", ""))[:280]
            
            # Get impact score (use item score or calculate from base)
            impact_score = int(item.get("score", item.get("score_base", 5)))
            
            # Get source link and name
            source_url = item.get("url", "")
            source_name = item.get("source", "Unknown")
            
            # Format field value with impact score and source
            if source_url:
                field_value = (
                    f"{summary}\n"
                    f"   └ 📊 **Impact Score:** {impact_score}/10 | "
                    f"🔗 [{source_name}]({source_url})"
                )
            else:
                field_value = (
                    f"{summary}\n"
                    f"   └ 📊 **Impact Score:** {impact_score}/10"
                )
            
            # Add field to embed
            embed.add_field(
                name=f"{emoji} **{category_name}**",
                value=field_value,
                inline=False
            )
        
        # Add degradation warning if needed
        if degraded_mode:
            embed.add_field(
                name="⚠️ **Degraded Mode**",
                value="Some data sources temporarily unavailable. "
                      "Showing available items only.",
                inline=False
            )
        
        # Set footer with timestamp and data sources
        footer_text = EMBED_FOOTER_TEXT
        if degraded_mode:
            footer_text += " | ⚠️ Partial data"
        
        embed.set_footer(
            text=footer_text,
            icon_url="https://cdn-icons-png.flaticon.com/512/1/1383.png"
        )
        
        return embed
    
    @staticmethod
    def _format_category_name(category: str) -> str:
        """
        Format category name for display.
        
        Args:
            category: Internal category name.
        
        Returns:
            str: Formatted category name.
        """
        category_names = {
            "macro_policy": "Macro/Policy",
            "capital_flow": "Capital Flow",
            "major_coins": "Major Coins (BTC/ETH)",
            "altcoins_trending": "Altcoins/Trending",
            "tech_narratives": "Tech/Narratives",
            "kol_insights": "KOL Insights",
        }
        return category_names.get(category, "News")
    
    @staticmethod
    def create_health_check_embed(
        posted_successfully: bool,
        sources_queried: int,
        sources_responded: int,
        nitter_status: Dict[str, bool],
        execution_time: float,
        warnings: Optional[List[str]] = None
    ) -> discord.Embed:
        """
        Create a health check status embed.
        
        Args:
            posted_successfully: Whether the post was successful.
            sources_queried: Number of sources queried.
            sources_responded: Number of sources that responded.
            nitter_status: Status of Nitter instances.
            execution_time: Execution time in seconds.
            warnings: Optional list of warning messages.
        
        Returns:
            discord.Embed: Health check status embed.
        """
        status_emoji = "✅" if posted_successfully else "❌"
        status_color = 0x00FF00 if posted_successfully else 0xFF0000
        
        embed = discord.Embed(
            title=f"{status_emoji} Health Check Report",
            color=status_color,
            timestamp=datetime.now()
        )
        
        # Add status information
        embed.add_field(
            name="Post Status",
            value="✅ Published successfully" if posted_successfully else "❌ Failed to publish",
            inline=False
        )
        
        embed.add_field(
            name="Data Sources",
            value=f"Queried: {sources_queried} | Responded: {sources_responded}",
            inline=True
        )
        
        embed.add_field(
            name="Execution Time",
            value=f"{execution_time:.2f}s",
            inline=True
        )
        
        # Add Nitter instance status
        healthy_instances = sum(1 for status in nitter_status.values() if status)
        total_instances = len(nitter_status)
        
        embed.add_field(
            name="Nitter Instances",
            value=f"{healthy_instances}/{total_instances} healthy",
            inline=True
        )
        
        # Add warnings if any
        if warnings:
            warnings_text = "\n".join(f"• {w}" for w in warnings)
            embed.add_field(
                name="⚠️ Warnings",
                value=warnings_text,
                inline=False
            )
        
        embed.set_footer(
            text="Powered by Manus AI"
        )
        
        return embed
    
    @staticmethod
    def create_error_embed(
        error_message: str,
        error_type: str = "Error"
    ) -> discord.Embed:
        """
        Create an error notification embed.
        
        Args:
            error_message: Error message to display.
            error_type: Type of error.
        
        Returns:
            discord.Embed: Error notification embed.
        """
        embed = discord.Embed(
            title=f"❌ {error_type}",
            description=error_message,
            color=0xFF0000,
            timestamp=datetime.now()
        )
        
        embed.set_footer(
            text="Powered by Manus AI"
        )
        
        return embed


class MarkdownFormatter:
    """Formats content as Markdown for logs and documentation."""
    
    @staticmethod
    def format_briefing_markdown(items: List[Dict]) -> str:
        """
        Format briefing items as Markdown.
        
        Args:
            items: List of items to format.
        
        Returns:
            str: Markdown formatted briefing.
        """
        now = datetime.now()
        date_str = now.strftime("%b %d, %Y")
        
        markdown = f"# 🌅 Crypto Morning Pulse | {date_str}\n\n"
        markdown += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for idx, item in enumerate(items, 1):
            category = item.get("category", "macro_policy")
            emoji = CATEGORY_EMOJIS.get(category, "📰")
            category_name = DiscordFormatter._format_category_name(category)
            
            # Get summary
            if "text" in item:
                summary = item.get("text", "")[:280]
            else:
                summary = item.get("title", "")[:280]
            
            impact_score = item.get("impact_score", 0)
            source_url = item.get("url", "")
            source_name = item.get("source_name", "Unknown")
            
            markdown += f"{emoji} **{category_name}:** {summary}\n"
            
            if source_url:
                markdown += f"   └ 📊 **Impact Score:** {impact_score}/10 | 🔗 [{source_name}]({source_url})\n\n"
            else:
                markdown += f"   └ 📊 **Impact Score:** {impact_score}/10\n\n"
        
        markdown += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        markdown += f"Powered by Manus AI | Data: X, CryptoPanic, CoinGecko\n"
        markdown += f"Generated at: {now.strftime('%H:%M')} {TIMEZONE}\n"
        
        return markdown
    
    @staticmethod
    def format_scoring_example(item: Dict) -> str:
        """
        Format a scoring breakdown example as Markdown.
        
        Args:
            item: Item to show scoring for.
        
        Returns:
            str: Markdown formatted scoring breakdown.
        """
        markdown = f"## Scoring Breakdown Example\n\n"
        markdown += f"**Item:** {item.get('title', item.get('text', 'Unknown'))}\n\n"
        markdown += f"### Score Components\n\n"
        markdown += f"- **Base Score:** {item.get('base_score', 0)} points\n"
        markdown += f"- **Content Multipliers:** +15 points (regulation keyword)\n"
        markdown += f"- **Recency Bonus:** +10 points (within 6 hours)\n"
        markdown += f"- **Total Impact Score:** {item.get('impact_score', 0)}/10\n"
        
        return markdown
