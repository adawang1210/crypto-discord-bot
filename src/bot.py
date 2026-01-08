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

from src.config import (
    DISCORD_BOT_TOKEN,
    DISCORD_CHANNEL_ID,
    ADMIN_CHANNEL_ID,
    BOT_OWNER_ID,
    TIMEZONE,
    POSTING_TIME,
)
from src.logger import logger
from src.data_fetcher import DataFetcher
from src.scorer import ContentScorer
from src.formatter import DiscordFormatter, MarkdownFormatter


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
        logger.info("CryptoMorningPulseBot cog loaded")
    
    def cog_unload(self):
        """Clean up when cog unloads."""
        self.daily_post_task.cancel()
        self.health_check_task.cancel()
        logger.info("CryptoMorningPulseBot cog unloaded")
    
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
            
            kol_posts = data.get("kol_posts", [])
            news_items = data.get("news", [])
            nitter_status = data.get("nitter_status", {})
            
            # Score and filter content
            scored_kol_posts = self.scorer.score_kol_posts(kol_posts)
            scored_news_items = self.scorer.score_news_items(news_items)
            
            # Select top items
            total_items = len(scored_kol_posts) + len(scored_news_items)
            
            if total_items < 3:
                logger.warning(f"Insufficient items for briefing: {total_items}")
                await self.send_admin_alert(
                    f"⚠️ Insufficient content items: {total_items} (minimum: 3)"
                )
                self.consecutive_failures += 1
                return False
            
            # Select items ensuring diversity
            selected_items = self.scorer.select_top_items(
                scored_kol_posts,
                scored_news_items,
                total_items=min(5, total_items)
            )
            
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
        """Send health check status to admin channel."""
        try:
            admin_channel = self.bot.get_channel(ADMIN_CHANNEL_ID)
            if not admin_channel:
                logger.warning(f"Admin channel {ADMIN_CHANNEL_ID} not found")
                return
            
            # Prepare health check data
            posted_successfully = self.consecutive_failures == 0
            execution_time = 0.0  # Would track actual execution time
            
            # Get Nitter status
            fetcher = DataFetcher()
            nitter_status = fetcher.nitter_rotator.get_status_report()
            
            # Create health check embed
            embed = DiscordFormatter.create_health_check_embed(
                posted_successfully=posted_successfully,
                sources_queried=4,
                sources_responded=3,
                nitter_status=nitter_status,
                execution_time=execution_time,
                warnings=["Some Nitter instances unstable"] if not all(nitter_status.values()) else None
            )
            
            await admin_channel.send(embed=embed)
            logger.info("Health check report sent to admin channel")
        
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
                embed = DiscordFormatter.create_error_embed(message, "Alert")
                await admin_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending admin alert: {str(e)}")
    
    async def send_critical_alert(self, message: str) -> None:
        """
        Send critical alert to bot owner via DM.
        
        Args:
            message: Critical alert message.
        """
        try:
            owner = await self.bot.fetch_user(BOT_OWNER_ID)
            if owner:
                embed = DiscordFormatter.create_error_embed(message, "Critical Alert")
                await owner.send(embed=embed)
                logger.info(f"Critical alert sent to owner: {message}")
        except Exception as e:
            logger.error(f"Error sending critical alert: {str(e)}")
    
    @commands.command(name="crypto-pulse-now")
    @commands.is_owner()
    async def manual_trigger(self, ctx: commands.Context) -> None:
        """
        Manually trigger the daily briefing post.
        Only available to bot owner.
        
        Args:
            ctx: Command context.
        """
        logger.info(f"Manual trigger requested by {ctx.author}")
        await ctx.defer()
        
        success = await self.post_daily_briefing()
        
        if success:
            await ctx.send("✅ Daily briefing posted successfully!")
        else:
            await ctx.send("❌ Failed to post daily briefing. Check logs for details.")
    
    @commands.command(name="crypto-pulse-shutdown")
    @commands.is_owner()
    async def shutdown_command(self, ctx: commands.Context) -> None:
        """
        Shutdown the bot.
        Only available to bot owner.
        
        Args:
            ctx: Command context.
        """
        logger.info(f"Shutdown requested by {ctx.author}")
        await ctx.send("🛑 Bot shutting down...")
        await self.bot.close()
    
    @commands.command(name="crypto-pulse-status")
    @commands.is_owner()
    async def status_command(self, ctx: commands.Context) -> None:
        """
        Get current bot status.
        Only available to bot owner.
        
        Args:
            ctx: Command context.
        """
        await ctx.defer()
        
        status_text = f"""
        **🤖 Crypto Morning Pulse Bot Status**
        
        **Uptime:** {self.bot.latency * 1000:.0f}ms
        **Last Post:** {self.last_post_time or 'Never'}
        **Consecutive Failures:** {self.consecutive_failures}
        **Timezone:** {TIMEZONE}
        **Posting Time:** {POSTING_TIME.strftime('%H:%M')} UTC+8
        """
        
        await ctx.send(status_text)


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
