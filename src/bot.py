"""
Main Discord bot module for Crypto Morning Pulse Bot.
Implements bot logic, scheduling, and command handling.
"""

import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import pytz
from typing import Optional, List
import re

from difflib import SequenceMatcher
from src.config import (
    DISCORD_BOT_TOKEN,
    DISCORD_CHANNEL_ID,
    ADMIN_CHANNEL_ID,
    BOT_OWNER_ID,
    TIMEZONE,
    POSTING_TIME,
    CONTENT_KEYWORD_MULTIPLIERS,
)
from src.logger import logger
from src.data_fetcher import DataFetcher
from src.scorer import ContentScorer
from src.formatter import DiscordFormatter, MarkdownFormatter
from src.enhancer import ContentEnhancer


class CryptoMorningPulseBot(commands.Cog):
    """Main bot cog for Crypto Morning Pulse functionality."""
    
    def __init__(self, bot: commands.Bot):
        """
        Initialize the bot cog.
        
        Args:
            bot: Discord bot instance.
        """
        self.bot = bot
        self.data_fetcher: Optional[DataFetcher] = None
        self.scorer = ContentScorer()
        self.timezone = pytz.timezone(TIMEZONE)
        self.last_post_time: Optional[datetime] = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        
        # Start the daily posting task
        self.daily_post_task.start()
        self.health_check_task.start()
    
    async def cog_load(self):
        """Initialize data fetcher when cog loads."""
        self.data_fetcher = DataFetcher()
    
    @tasks.loop(minutes=1)
    async def daily_post_task(self):
        """
        Main task for daily posting.
        Runs every minute and checks if it's time to post.
        """
        try:
            now = datetime.now(self.timezone)
            
            # Check if it's time to post (09:00 AM)
            if now.hour == POSTING_TIME.hour and now.minute == POSTING_TIME.minute:
                # Avoid posting multiple times in the same minute
                if self.last_post_time and \
                   self.last_post_time.date() == now.date():
                    return
                
                await self.post_daily_briefing()
                self.last_post_time = now
        
        except Exception as e:
            logger.error(f"Error in daily_post_task: {str(e)}")
    
    @tasks.loop(hours=24)
    async def health_check_task(self):
        """
        Health check task that runs daily at 09:05 AM.
        Sends status report to admin channel.
        """
        try:
            now = datetime.now(self.timezone)
            
            # Check if it's 09:05 AM
            if now.hour == POSTING_TIME.hour and now.minute == POSTING_TIME.minute + 5:
                await self.send_health_check()
        
        except Exception as e:
            logger.error(f"Error in health_check_task: {str(e)}")
    
    async def post_daily_briefing(self) -> bool:
        """
        Fetch data, score content, and post daily briefing.
        
        Returns:
            bool: True if posting was successful, False otherwise.
        """
        start_time = datetime.now()
        logger.info("Starting daily briefing post")
        
        try:
            # Fetch data from all sources
            async with DataFetcher() as fetcher:
                data = await fetcher.fetch_all_data()
            
            all_items = data.get("items", [])
            
            # Score items
            scored_items = []
            for item in all_items:
                score = item.get("score_base", 5)
                
                # Add keyword bonuses
                title = item.get("title", "").lower()
                for keyword_pattern, multiplier in CONTENT_KEYWORD_MULTIPLIERS.items():
                    if re.search(keyword_pattern, title, re.IGNORECASE):
                        score += multiplier
                
                scored_item = {**item, "score": score}
                scored_items.append(scored_item)
            
            # Sort by score
            scored_items.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            # Deduplicate
            unique_items = []
            for item in scored_items:
                is_duplicate = False
                for existing in unique_items:
                    similarity = SequenceMatcher(
                        None,
                        item.get("title", ""),
                        existing.get("title", "")
                    ).ratio()
                    if similarity > 0.6:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_items.append(item)
            
            total_items = len(unique_items)
            
            if total_items < 3:
                logger.warning(f"Insufficient items for briefing: {total_items}")
                await self.send_admin_alert(
                    f"⚠️ Insufficient content items: {total_items} (minimum: 3)"
                )
                self.consecutive_failures += 1
                return False
            
            # Select top items
            selected_items = unique_items[:min(5, total_items)]
            
            # Enhance items with translation, summary, and images
            async with ContentEnhancer() as enhancer:
                selected_items = await enhancer.enhance_items(selected_items)
            
            # Add items to cache
            for item in selected_items:
                self.scorer.add_to_cache(item)
            
            # Create and send embed
            degraded_mode = total_items < 5
            embed = DiscordFormatter.create_daily_briefing_embed(
                selected_items,
                degraded_mode=degraded_mode
            )
            
            channel = self.bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
                logger.info(f"Posted daily briefing with {len(selected_items)} items")
                
                # Reset failure counter on success
                self.consecutive_failures = 0
                
                # Log execution time
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Daily briefing posted successfully in {execution_time:.2f}s")
                
                return True
            else:
                logger.error(f"Channel {DISCORD_CHANNEL_ID} not found")
                self.consecutive_failures += 1
                return False
        
        except Exception as e:
            logger.error(f"Error posting daily briefing: {str(e)}")
            self.consecutive_failures += 1
            
            # Send error alert if consecutive failures exceed threshold
            if self.consecutive_failures >= self.max_consecutive_failures:
                await self.send_critical_alert(
                    f"❌ Bot failed to post for {self.consecutive_failures} consecutive days"
                )
            
            return False
    
    async def send_health_check(self) -> None:
        """Send health check report to admin channel."""
        try:
            admin_channel = self.bot.get_channel(ADMIN_CHANNEL_ID)
            if admin_channel:
                embed = DiscordFormatter.create_health_check_embed(
                    self.consecutive_failures,
                    self.last_post_time
                )
                await admin_channel.send(embed=embed)
                logger.info("Health check report sent")
        except Exception as e:
            logger.error(f"Error sending health check: {str(e)}")
    
    async def send_admin_alert(self, message: str) -> None:
        """
        Send alert message to admin channel.
        
        Args:
            message: Alert message to send.
        """
        try:
            admin_channel = self.bot.get_channel(ADMIN_CHANNEL_ID)
            if admin_channel:
                await admin_channel.send(f"⚠️ {message}")
                logger.info(f"Admin alert sent: {message}")
        except Exception as e:
            logger.error(f"Error sending admin alert: {str(e)}")
    
    async def send_critical_alert(self, message: str) -> None:
        """
        Send critical alert message to admin channel.
        
        Args:
            message: Critical alert message to send.
        """
        try:
            admin_channel = self.bot.get_channel(ADMIN_CHANNEL_ID)
            if admin_channel:
                await admin_channel.send(f"🚨 {message}")
                logger.error(f"Critical alert sent: {message}")
        except Exception as e:
            logger.error(f"Error sending critical alert: {str(e)}")
    
    @commands.command(name="crypto-pulse-now")
    async def manual_trigger(self, ctx):
        """
        Manually trigger the daily briefing post.
        
        Args:
            ctx: Discord context.
        """
        logger.info(f"Manual trigger requested by {ctx.author}")
        
        if ctx.author.id != BOT_OWNER_ID:
            await ctx.send("❌ Only the bot owner can use this command")
            return
        
        await self.post_daily_briefing()
        await ctx.send("✅ Daily briefing posted")
    
    @commands.command(name="crypto-pulse-status")
    async def status_command(self, ctx):
        """
        Show bot status.
        
        Args:
            ctx: Discord context.
        """
        embed = discord.Embed(
            title="🤖 Crypto Morning Pulse Bot Status",
            color=0xF7931A
        )
        embed.add_field(
            name="Last Post",
            value=self.last_post_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_post_time else "Never",
            inline=False
        )
        embed.add_field(
            name="Consecutive Failures",
            value=str(self.consecutive_failures),
            inline=False
        )
        embed.add_field(
            name="Status",
            value="🟢 Online" if self.consecutive_failures < self.max_consecutive_failures else "🔴 Degraded",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="crypto-pulse-shutdown")
    async def shutdown_command(self, ctx):
        """
        Shutdown the bot.
        
        Args:
            ctx: Discord context.
        """
        if ctx.author.id != BOT_OWNER_ID:
            await ctx.send("❌ Only the bot owner can use this command")
            return
        
        logger.info("Bot shutdown requested")
        await ctx.send("👋 Bot shutting down...")
        await self.bot.close()


async def setup_bot() -> commands.Bot:
    """
    Set up and initialize the Discord bot.
    
    Returns:
        commands.Bot: Configured bot instance.
    """
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        """Event handler when bot is ready."""
        logger.info(f"Bot logged in as {bot.user}")
        logger.info(f"Connected to {len(bot.guilds)} guild(s)")
        
        # Set bot status
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="crypto markets 📈"
            )
        )
    
    @bot.event
    async def on_error(event, *args, **kwargs):
        """Event handler for errors."""
        logger.error(f"Error in {event}: {args} {kwargs}")
    
    # Add cog
    await bot.add_cog(CryptoMorningPulseBot(bot))
    
    return bot


async def run_bot() -> None:
    """Run the Discord bot."""
    bot = await setup_bot()
    
    try:
        logger.info("Starting Discord bot...")
        await bot.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")
        raise
