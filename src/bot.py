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
from src.formatter import DiscordFormatter
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
    
    @tasks.loop(minutes=1)
    async def daily_post_task(self):
        """
        Background task that runs every minute to check if it's time to post.
        """
        now = datetime.now(self.timezone)
        
        # Check if it's the posting time
        posting_hour, posting_minute = POSTING_TIME
        if now.hour == posting_hour and now.minute == posting_minute:
            # Avoid posting multiple times in the same minute
            if self.last_post_time and self.last_post_time.date() == now.date():
                return
            
            logger.info("Daily posting time reached, triggering briefing post")
            await self.post_daily_briefing()
            self.last_post_time = now
    
    @daily_post_task.before_loop
    async def before_daily_post_task(self):
        """Wait for bot to be ready before starting the task."""
        await self.bot.wait_until_ready()
    
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
            
            # Score and filter items using ContentScorer
            unique_items = self.scorer.score_news_items(all_items)
            
            total_items = len(unique_items)
            
            if total_items < 3:
                logger.warning(f"Insufficient items for briefing: {total_items}")
                await self.send_admin_alert(
                    f"⚠️ Insufficient content items: {total_items} (minimum: 3)"
                )
                self.consecutive_failures += 1
                return False
            
            # Select top items with category diversity
            selected_items = self.scorer.select_top_items_with_diversity(
                kol_posts=data.get("kol_posts", []),
                news_items=unique_items,
                total_items=5
            )
            
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
    
    @commands.command(name="crypto-pulse-now")
    async def trigger_briefing(self, ctx):
        """
        Manual command to trigger the daily briefing.
        Only bot owner can use this command.
        """
        if ctx.author.id != BOT_OWNER_ID:
            await ctx.send("❌ Only the bot owner can use this command")
            return
        
        logger.info(f"Manual trigger requested by {ctx.author}")
        success = await self.post_daily_briefing()
        
        if success:
            await ctx.send("✅ Daily briefing posted successfully")
        else:
            await ctx.send("❌ Failed to post daily briefing. Check logs for details.")
    
    @commands.command(name="crypto-pulse-status")
    async def status_command(self, ctx):
        """
        Check the bot's current status.
        """
        status_info = {
            "status": "Healthy" if self.consecutive_failures == 0 else "Degraded",
            "consecutive_failures": self.consecutive_failures,
            "last_post_time": self.last_post_time.isoformat() if self.last_post_time else "Never",
        }
        
        embed = DiscordFormatter.create_health_check_embed(
            status_info,
            degraded=self.consecutive_failures > 0
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="crypto-pulse-shutdown")
    async def shutdown_command(self, ctx):
        """
        Shutdown the bot. Only bot owner can use this command.
        """
        if ctx.author.id != BOT_OWNER_ID:
            await ctx.send("❌ Only the bot owner can use this command")
            return
        
        logger.info(f"Shutdown requested by {ctx.author}")
        await ctx.send("🛑 Bot shutting down...")
        await self.bot.close()
    
    async def send_admin_alert(self, message: str):
        """
        Send an alert message to the admin channel.
        
        Args:
            message: Alert message to send.
        """
        try:
            admin_channel = self.bot.get_channel(ADMIN_CHANNEL_ID)
            if admin_channel:
                await admin_channel.send(f"⚠️ Alert: {message}")
        except Exception as e:
            logger.error(f"Error sending admin alert: {str(e)}")
    
    async def send_critical_alert(self, message: str):
        """
        Send a critical alert message to the admin channel.
        
        Args:
            message: Critical alert message to send.
        """
        try:
            admin_channel = self.bot.get_channel(ADMIN_CHANNEL_ID)
            if admin_channel:
                embed = DiscordFormatter.create_error_notification_embed(
                    message,
                    error_count=self.consecutive_failures
                )
                await admin_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending critical alert: {str(e)}")


async def setup(bot: commands.Bot):
    """Setup function to load the cog."""
    await bot.add_cog(CryptoMorningPulseBot(bot))


async def run_bot():
    """
    Run the Discord bot.
    """
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        logger.info(f"Bot logged in as {bot.user}")
        logger.info(f"Connected to {len(bot.guilds)} guild(s)")
    
    @bot.event
    async def on_command_error(ctx, error):
        logger.error(f"Command error: {str(error)}")
        await ctx.send(f"❌ Error: {str(error)}")
    
    async with bot:
        await setup(bot)
        await bot.start(DISCORD_BOT_TOKEN)
