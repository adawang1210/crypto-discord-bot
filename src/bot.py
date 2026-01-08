"""
Discord bot module for Crypto Morning Pulse.
Handles commands, events, and the daily briefing task.
"""

import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import pytz

from src.config import (
    DISCORD_BOT_TOKEN,
    DISCORD_CHANNEL_ID,
    TIMEZONE,
    POSTING_TIME
)
from src.data_fetcher import DataFetcher
from src.scorer import ContentScorer
from src.summarizer import ContentSummarizer
from src.formatter import DiscordFormatter
from src.logger import logger


class CryptoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.tz = pytz.timezone(TIMEZONE)

    async def setup_hook(self):
        self.daily_briefing.start()
        logger.info(f"Scheduled daily briefing at {POSTING_TIME} {TIMEZONE}")

    @tasks.loop(time=POSTING_TIME)
    async def daily_briefing(self):
        await self.post_daily_briefing()

    async def post_daily_briefing(self):
        """Fetch, score, summarize and post the daily briefing."""
        try:
            logger.info("Starting daily briefing post")
            
            # 1. Fetch all data
            async with DataFetcher() as fetcher:
                data = await fetcher.fetch_all_data()
            
            # 2. Score and select news
            scorer = ContentScorer()
            selected_news = scorer.score_news_items(
                news_items=data.get("news_items", []),
                total_items=8 # Fetch more to ensure variety
            )
            
            if not selected_news:
                logger.warning("Insufficient items for briefing: 0")
                return False

            # 3. Enhance news (summarize)
            async with ContentSummarizer() as summarizer:
                enhanced_news = await summarizer.summarize_items(
                    selected_news, 
                    [item.get('category', 'macro_policy') for item in selected_news]
                )
            
            # 3.5 Extract images for selected news
            async with DataFetcher() as fetcher:
                for item in enhanced_news:
                    img_url = await fetcher.extract_og_image(item.get('url', ''))
                    if img_url:
                        item['image_url'] = img_url
            
            # 4. Prepare final data
            final_data = {
                "market_overview": data.get("market_overview"),
                "news_items": enhanced_news,
                "x_posts": data.get("x_posts")
            }
            
            # 5. Generate "Today's Focus"
            async with ContentSummarizer() as summarizer:
                todays_focus = await summarizer.generate_todays_focus(
                    final_data['market_overview'], 
                    final_data['news_items']
                )
                final_data['todays_focus'] = todays_focus

            # 6. Create batches and send
            batches = DiscordFormatter.create_batches(final_data)
            channel = self.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                for batch in batches:
                    await channel.send(batch)
                    await asyncio.sleep(1)
                logger.info("Daily briefing posted successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error posting daily briefing: {str(e)}")
            return False

    @commands.command(name="crypto-pulse-now")
    async def trigger_briefing(self, ctx):
        # Removed "Generating..." message
        success = await self.post_daily_briefing()
        # Removed "Posted!" message

async def run_bot():
    bot = CryptoBot()
    async with bot:
        await bot.start(DISCORD_BOT_TOKEN)
