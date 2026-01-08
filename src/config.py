"""
Configuration module for Crypto Morning Pulse Bot.
Manages environment variables, constants, and settings.
"""

import os
from typing import List, Dict
from dotenv import load_dotenv
from datetime import time

# Load environment variables
load_dotenv()

# ==================== Discord Configuration ====================
DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL_ID: int = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
ADMIN_CHANNEL_ID: int = int(os.getenv("ADMIN_CHANNEL_ID", "0"))
BOT_OWNER_ID: int = int(os.getenv("BOT_OWNER_ID", "0"))

# ==================== Timezone Configuration ====================
TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Taipei")
POSTING_TIME: time = time(9, 0)  # 09:00 AM

# ==================== API Keys ====================
CRYPTOPANIC_API_KEY: str = os.getenv("CRYPTOPANIC_API_KEY", "")
COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")
# Added X API support (if available)
X_API_BEARER_TOKEN: str = os.getenv("X_API_BEARER_TOKEN", "")

# ==================== Scoring Thresholds ====================
MIN_IMPACT_SCORE: int = int(os.getenv("MIN_IMPACT_SCORE", "5"))
MIN_KOL_SCORE: int = int(os.getenv("MIN_KOL_SCORE", "60"))

# ==================== Performance Configuration ====================
MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ==================== News Sources ====================
NEWS_SOURCES: Dict[str, str] = {
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "decrypt": "https://decrypt.co/feed",
    "the_block": "https://www.theblock.co/rss.xml",
    "bitcoin_magazine": "https://bitcoinmagazine.com/.rss/full/",
    "crypto_briefing": "https://cryptobriefing.com/feed/",
    "newsbtc": "https://www.newsbtc.com/feed/",
    "beincrypto": "https://beincrypto.com/feed/",
}

# ==================== Market Data APIs ====================
COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,ripple&vs_currencies=usd&include_24hr_change=true"
COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"
FNG_INDEX_URL = "https://api.alternative.me/fng/"

# ==================== Logging & Cache ====================
LOG_DIR: str = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
CACHE_DIR: str = os.path.join(os.path.dirname(__file__), "..", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_RETENTION_DAYS: int = 7
DEDUP_KEYWORD_THRESHOLD: float = 0.6

def validate_config() -> bool:
    """Validate required configuration."""
    required_fields = [
        ("DISCORD_BOT_TOKEN", DISCORD_BOT_TOKEN),
        ("DISCORD_CHANNEL_ID", DISCORD_CHANNEL_ID),
    ]
    for name, val in required_fields:
        if not val or (isinstance(val, int) and val == 0):
            print(f"❌ Missing config: {name}")
            return False
    return True
