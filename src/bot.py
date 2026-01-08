"""
Main Discord bot module for Crypto Morning Pulse Bot.
"""

import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime
import pytz
from typing import Optional

from src.config import (
    DISCORD_BOT_TOKEN,
    DISCORD_CHANNEL_ID,
    TIMEZONE,
    POSTING_TIME,
)
from src.logger import logger
from src.data_fetcher import DataFetcher
from src.scorer import ContentScorer
from src.formatter import DiscordFormatter
from src.enhancer import ContentEnhancer


class CryptoMorningPulseBot(commands.Cog):
    """Main bot cog for Crypto Morning Pulse functionality."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scorer = ContentScorer()
        self.timezone = pytz.timezone(TIMEZONE)
        self.last_post_time: Optional[datetime] = None
        self.daily_post_task.start()
    
    @tasks.loop(minutes=1)
    async def daily_post_task(self):
        now = datetime.now(self.timezone)
        posting_hour, posting_minute = POSTING_TIME.hour, POSTING_TIME.minute
        if now.hour == posting_hour and now.minute == posting_minute:
            if self.last_post_time and self.last_post_time.date() == now.date():
                return
            logger.info("Daily posting time reached")
            await self.post_daily_briefing()
            self.last_post_time = now
    
    @daily_post_task.before_loop
    async def before_daily_post_task(self):
        await self.bot.wait_until_ready()
    
    async def post_daily_briefing(self) -> bool:
        logger.info("Starting daily briefing post")
        try:
            async with DataFetcher() as fetcher:
                data = await fetcher.fetch_all_data()
            
            # 1. Filter and score news
            news_items = self.scorer.score_news_items(data.get("news_items", []))
            
            # 2. Select top items with diversity
            selected_news = self.scorer.select_top_items_with_diversity(
                kol_posts=[],
                news_items=news_items,
                total_items=4
            )
            
            # 3. Enhance news (summarize and extract images)
            async with ContentEnhancer() as enhancer:
                enhanced_news = await enhancer.enhance_items(selected_news)
            
            # 3.5 Extract images for selected news
            async with DataFetcher() as fetcher:
                for item in enhanced_news:
                    img_url = await fetcher.extract_og_image(item.get('url', ''))
                    if img_url:
                        item['image_url'] = img_url
            
            # 4. Prepare final data for formatter
            final_data = {
                "market_overview": data.get("market_overview"),
                "news_items": enhanced_news,
                "x_posts": data.get("x_posts")
            }
            
            # 5. Generate "Today's Focus"
            from src.summarizer import ContentSummarizer
            async with ContentSummarizer() as summarizer:
                todays_focus = await summarizer.generate_todays_focus(
                    final_data['market_overview'], 
                    final_data['news_items']
                )
                final_data['todays_focus'] = todays_focus

            # 6. Create batches and send multiple messages
            batches = DiscordFormatter.create_batches(final_data)
            channel = self.bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                for batch in batches:
                    await channel.send(batch)
                    await asyncio.sleep(1) # Small delay to prevent rate limiting
                logger.info("Daily briefing posted successfully in batches")
                return True
            return False
        except Exception as e:
            logger.error(f"Error posting daily briefing: {str(e)}")
            return False

    @commands.command(name="crypto-pulse-now")
    async def trigger_briefing(self, ctx):
        await ctx.send("🔄 Generating daily briefing...")
        success = await self.post_daily_briefing()
        if success:
            await ctx.send("✅ Posted!")
        else:
            await ctx.send("❌ Failed. Check logs.")


async def setup(bot: commands.Bot):
    await bot.add_cog(CryptoMorningPulseBot(bot))


async def run_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        logger.info(f"Bot logged in as {bot.user}")
    
    async with bot:
        await setup(bot)
        await bot.start(DISCORD_BOT_TOKEN)
