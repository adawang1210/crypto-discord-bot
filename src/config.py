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

# ==================== Nitter Configuration ====================
NITTER_INSTANCES: List[str] = os.getenv(
    "NITTER_INSTANCES",
    "nitter.net,nitter.poast.org,nitter.privacydev.net,nitter.privacytools.io"
).split(",")
NITTER_REQUEST_DELAY: float = float(os.getenv("NITTER_REQUEST_DELAY", "2.5"))

# ==================== Scoring Thresholds ====================
MIN_IMPACT_SCORE: int = int(os.getenv("MIN_IMPACT_SCORE", "7"))
MIN_KOL_SCORE: int = int(os.getenv("MIN_KOL_SCORE", "60"))

# ==================== Performance Configuration ====================
MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ==================== KOL Watch List ====================
KOL_TIER_1: Dict[str, int] = {
    "VitalikButerin": 50,
    "cz_binance": 50,
    "saylor": 50,
    "elonmusk": 50,
    "aantonop": 50,
}

KOL_TIER_2: Dict[str, int] = {
    "DocumentingBTC": 30,
    "santimentfeed": 30,
    "whale_alert": 30,
    "glassnode": 30,
    "lookonchain": 30,
}

KOL_TIER_3: Dict[str, int] = {
    "cnLedger": 30,
    "WuBlockchain": 30,
    "thecryptodog": 30,
    "cryptohayes": 30,
}

# ==================== Content Scoring Multipliers ====================
CONTENT_KEYWORD_MULTIPLIERS: Dict[str, int] = {
    "SEC|regulation|lawsuit": 15,
    "ETF|approval": 15,
    "hack|exploit|vulnerability": 20,
    "all-time high|ATH|new high": 10,
    "price target|\\$\\d+k": 10,
    "partnership|acquisition": 10,
    "BTC.*ETH|ETH.*BTC": 5,
}

RECENCY_BONUS: Dict[str, int] = {
    "2_hours": 15,
    "6_hours": 10,
    "12_hours": 5,
}

# ==================== Discord Embed Configuration ====================
EMBED_COLOR: int = 0xF7931A  # Bitcoin orange
EMBED_TITLE_FORMAT: str = "🌅 Crypto Morning Pulse | {date}"
EMBED_DESCRIPTION: str = "Here's what's moving markets today"
EMBED_FOOTER_TEXT: str = "Powered by Manus AI | Data sources: X (via Nitter), CryptoPanic, CoinGecko"

# ==================== Category Emojis ====================
CATEGORY_EMOJIS: Dict[str, str] = {
    "macro_policy": "🏛️",
    "capital_flow": "💰",
    "major_coins": "₿",
    "altcoins_trending": "🚀",
    "tech_narratives": "🔬",
    "kol_insights": "🎤",
}

# ==================== News Sources ====================
NEWS_SOURCES: Dict[str, str] = {
    "coindesk": "https://feeds.coindesk.com/news",
    "cointelegraph": "https://cointelegraph.com/feed",
    "decrypt": "https://decrypt.co/feed",
    "the_block": "https://www.theblockresearch.com/feed",
    "whale_alert": "https://whale-alert.io/feed",
}

# ==================== Logging Configuration ====================
LOG_DIR: str = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ==================== Cache Configuration ====================
CACHE_DIR: str = os.path.join(os.path.dirname(__file__), "..", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_RETENTION_DAYS: int = 7
DEDUP_KEYWORD_THRESHOLD: float = 0.6  # 60% similarity for deduplication

# ==================== Validation ====================
def validate_config() -> bool:
    """
    Validate that all required configuration values are set.
    
    Returns:
        bool: True if all required configs are valid, False otherwise.
    """
    required_fields = [
        ("DISCORD_BOT_TOKEN", DISCORD_BOT_TOKEN),
        ("DISCORD_CHANNEL_ID", DISCORD_CHANNEL_ID),
        ("ADMIN_CHANNEL_ID", ADMIN_CHANNEL_ID),
    ]
    
    for field_name, field_value in required_fields:
        if not field_value or (isinstance(field_value, int) and field_value == 0):
            print(f"❌ Missing or invalid configuration: {field_name}")
            return False
    
    return True
