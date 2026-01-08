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
        intents = discord.Intents.all()
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
            logger.info(">>> [STEP 1] Starting daily briefing post process...")
            
            # 1. Fetch all data
            logger.info(">>> [STEP 2] Fetching data from APIs and RSS...")
            async with DataFetcher() as fetcher:
                data = await fetcher.fetch_all_data()
            logger.info(f">>> [STEP 2 DONE] Fetched {len(data.get('news_items', []))} news items")
            
            # 2. Score and select news
            logger.info(">>> [STEP 3] Scoring and selecting news...")
            scorer = ContentScorer()
            selected_news = scorer.score_news_items(
                news_items=data.get("news_items", []),
                total_items=8
            )
            
            if not selected_news:
                logger.warning(">>> [ABORT] Insufficient items for briefing: 0")
                return False
            logger.info(f">>> [STEP 3 DONE] Selected {len(selected_news)} news items")

            # 3. Enhance news (summarize)
            logger.info(">>> [STEP 4] Summarizing news items...")
            async with ContentSummarizer() as summarizer:
                enhanced_news = await summarizer.summarize_items(
                    selected_news, 
                    [item.get('category', 'macro_policy') for item in selected_news]
                )
            logger.info(">>> [STEP 4 DONE] Summarization complete")
            
            # 3.5 Extract images for selected news
            logger.info(">>> [STEP 5] Extracting images...")
            async with DataFetcher() as fetcher:
                for item in enhanced_news:
                    img_url = await fetcher.extract_og_image(item.get('url', ''))
                    if img_url:
                        item['image_url'] = img_url
            logger.info(">>> [STEP 5 DONE] Image extraction complete")
            
            # 4. Prepare final data
            final_data = {
                "market_overview": data.get("market_overview"),
                "news_items": enhanced_news,
                "x_posts": data.get("x_posts")
            }
            
            # 5. Generate "Today's Focus"
            logger.info(">>> [STEP 6] Generating Today's Focus...")
            async with ContentSummarizer() as summarizer:
                todays_focus = await summarizer.generate_todays_focus(
                    final_data['market_overview'], 
                    final_data['news_items']
                )
                final_data['todays_focus'] = todays_focus
            logger.info(">>> [STEP 6 DONE] Today's Focus generated")

            # 6. Create batches and send
            logger.info(">>> [STEP 7] Formatting and sending to Discord...")
            batches = DiscordFormatter.create_batches(final_data)
            channel = self.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                for i, batch in enumerate(batches, 1):
                    logger.info(f">>> Sending batch {i}/{len(batches)}...")
                    await channel.send(batch)
                    await asyncio.sleep(1)
                logger.info(">>> [SUCCESS] Daily briefing posted successfully")
                return True
            else:
                logger.error(f">>> [ERROR] Could not find channel with ID {DISCORD_CHANNEL_ID}")
                return False
        except Exception as e:
            logger.error(f">>> [FATAL ERROR] {str(e)}", exc_info=True)
            return False

    async def on_ready(self):
        logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        logger.info("------ Bot is ready and listening for commands ------")

    @commands.command(name="crypto-pulse-now")
    async def trigger_briefing(self, ctx):
        logger.info(f"Manual trigger requested by {ctx.author}")
        # Immediate feedback to test if bot can send messages
        await ctx.send("⏳ 正在生成今日簡報，請稍候...")
        
        success = await self.post_daily_briefing()
        if success:
            await ctx.send("✅ 簡報已成功發布！")
        else:
            await ctx.send("❌ 簡報發布失敗，請檢查日誌。")

async def run_bot():
    bot = CryptoBot()
    async with bot:
        await bot.start(DISCORD_BOT_TOKEN)
