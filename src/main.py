"""
Main entry point for Crypto Morning Pulse Bot.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import validate_config
from src.logger import logger
from src.bot import run_bot


async def main() -> None:
    """Main entry point for the bot."""
    logger.info("=" * 60)
    logger.info("🚀 Crypto Morning Pulse Bot Starting")
    logger.info("=" * 60)
    
    # Validate configuration
    if not validate_config():
        logger.error("Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    
    logger.info("✅ Configuration validated successfully")
    
    # Run the bot
    try:
        await run_bot()
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)
