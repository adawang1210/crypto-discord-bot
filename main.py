"""
Main entry point for Crypto Morning Pulse Bot.
"""

import asyncio
import sys
from src.bot import run_bot
from src.config import validate_config
from src.logger import logger

def main():
    # Top-level print for Railway logs visibility
    print(">>> Starting Crypto Morning Pulse Bot Application...")
    sys.stdout.flush()
    
    if not validate_config():
        print("❌ Configuration validation failed. Exiting.")
        sys.exit(1)
        
    try:
        logger.info("Application starting...")
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
    except Exception as e:
        logger.error(f"Fatal error during startup: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
