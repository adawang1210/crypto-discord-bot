import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.data_fetcher import DataFetcher
from src.scorer import ContentScorer
from src.formatter import DiscordFormatter
from src.enhancer import ContentEnhancer
from src.logger import logger

async def test_output():
    logger.info("Starting optimization test...")
    
    # 1. Fetch data
    async with DataFetcher() as fetcher:
        data = await fetcher.fetch_all_data()
    
    all_items = data.get("items", [])
    logger.info(f"Fetched {len(all_items)} items")
    
    if not all_items:
        logger.error("No items fetched. Cannot proceed with test.")
        return

    # 2. Score and select items with diversity
    scorer = ContentScorer()
    # Use real KOL posts if available
    kol_posts = data.get("kol_posts", [])
    
    selected_items = scorer.select_top_items_with_diversity(
        kol_posts=kol_posts,
        news_items=all_items,
        total_items=5
    )
    
    logger.info(f"Selected {len(selected_items)} items for briefing")
    for item in selected_items:
        logger.info(f"- Category: {item.get('category')}, Source: {item.get('source_name')}")

    # 3. Enhance items (Summarization & Translation)
    async with ContentEnhancer() as enhancer:
        enhanced_items = await enhancer.enhance_items(selected_items)
    
    # 4. Format output
    embed = DiscordFormatter.create_daily_briefing_embed(enhanced_items)
    
    # 5. Print results to a file for verification
    with open("test_result.md", "w", encoding="utf-8") as f:
        f.write(f"# Crypto Morning Pulse Test Result\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Embed Title: {embed.title}\n")
        f.write(f"## Embed Description: {embed.description}\n\n")
        
        for field in embed.fields:
            if field.name == "━━━━━━━━━━━━━━━━━━━━━━━━━":
                f.write(f"---\n")
            elif field.name == "\u200b":
                f.write(f"{field.value}\n\n")
            else:
                f.write(f"### {field.name}\n{field.value}\n\n")
        
        f.write(f"---\n")
        f.write(f"Footer: {embed.footer.text}\n")

    logger.info("Test completed. Results saved to test_result.md")

if __name__ == "__main__":
    asyncio.run(test_output())
