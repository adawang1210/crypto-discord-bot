"""
Unit tests for the formatter module.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.formatter import DiscordFormatter, MarkdownFormatter


def test_discord_embed_creation():
    """Test Discord embed creation."""
    test_items = [
        {
            "category": "macro_policy",
            "text": "SEC delays decision on spot Ethereum ETF applications until March 2025.",
            "impact_score": 8,
            "source_name": "CoinDesk",
            "url": "https://example.com/sec-etf",
        },
        {
            "category": "capital_flow",
            "title": "Whale alert detects 5,000 BTC transferred from Coinbase",
            "impact_score": 7,
            "source_name": "Whale Alert",
            "url": "https://example.com/whale-alert",
        },
        {
            "category": "kol_insights",
            "text": "Vitalik Buterin announces Ethereum's Purge upgrade entering testnet.",
            "impact_score": 9,
            "source_name": "VitalikButerin",
            "url": "https://nitter.net/VitalikButerin/status/123456",
        },
    ]
    
    embed = DiscordFormatter.create_daily_briefing_embed(test_items, degraded_mode=False)
    
    print("✅ Discord Embed Created")
    print(f"   Title: {embed.title}")
    print(f"   Color: {hex(embed.color.value)}")
    print(f"   Fields: {len(embed.fields)}")
    
    assert embed.title is not None, "Embed should have a title"
    assert embed.color.value == 0xF7931A, "Embed color should be Bitcoin orange"
    assert len(embed.fields) >= 3, "Embed should have at least 3 fields"


def test_degraded_mode_embed():
    """Test embed creation in degraded mode."""
    test_items = [
        {
            "category": "macro_policy",
            "text": "Limited news available today",
            "impact_score": 6,
            "source_name": "CoinDesk",
            "url": "https://example.com",
        },
    ]
    
    embed = DiscordFormatter.create_daily_briefing_embed(test_items, degraded_mode=True)
    
    print("✅ Degraded Mode Embed Created")
    
    # Check for degradation warning
    has_warning = any("Degraded" in field.name for field in embed.fields)
    assert has_warning, "Degraded mode embed should include warning"


def test_health_check_embed():
    """Test health check embed creation."""
    nitter_status = {
        "nitter.net": True,
        "nitter.poast.org": False,
        "nitter.privacydev.net": True,
    }
    
    embed = DiscordFormatter.create_health_check_embed(
        posted_successfully=True,
        sources_queried=4,
        sources_responded=3,
        nitter_status=nitter_status,
        execution_time=45.2,
        warnings=["One Nitter instance down"],
    )
    
    print("✅ Health Check Embed Created")
    print(f"   Status: {'✅' if embed.color.value == 0x00FF00 else '❌'}")
    print(f"   Fields: {len(embed.fields)}")
    
    assert embed.color.value == 0x00FF00, "Successful status should be green"


def test_error_embed():
    """Test error notification embed."""
    embed = DiscordFormatter.create_error_embed(
        "Failed to fetch data from Nitter instances",
        "Data Fetch Error"
    )
    
    print("✅ Error Embed Created")
    print(f"   Title: {embed.title}")
    print(f"   Color: {hex(embed.color.value)}")
    
    assert embed.color.value == 0xFF0000, "Error embed should be red"
    assert "Error" in embed.title, "Error embed should have 'Error' in title"


def test_markdown_formatting():
    """Test Markdown formatting."""
    test_items = [
        {
            "category": "macro_policy",
            "text": "SEC delays decision on spot Ethereum ETF applications until March 2025.",
            "impact_score": 8,
            "source_name": "CoinDesk",
            "url": "https://example.com/sec-etf",
        },
        {
            "category": "capital_flow",
            "title": "Whale alert detects 5,000 BTC transferred from Coinbase",
            "impact_score": 7,
            "source_name": "Whale Alert",
            "url": "https://example.com/whale-alert",
        },
    ]
    
    markdown = MarkdownFormatter.format_briefing_markdown(test_items)
    
    print("✅ Markdown Briefing Created")
    print(f"   Length: {len(markdown)} characters")
    
    assert "🌅 Crypto Morning Pulse" in markdown, "Should contain title"
    assert "🏛️" in markdown, "Should contain category emoji"
    assert "Impact Score" in markdown, "Should contain impact scores"


def test_scoring_example_markdown():
    """Test scoring breakdown example Markdown."""
    test_item = {
        "title": "SEC Delays Spot Ethereum ETF Decision",
        "base_score": 50,
        "impact_score": 8,
    }
    
    markdown = MarkdownFormatter.format_scoring_example(test_item)
    
    print("✅ Scoring Example Markdown Created")
    print(f"   Content includes base score: {'base_score' in markdown}")
    
    assert "Scoring Breakdown" in markdown, "Should have scoring breakdown header"
    assert "Base Score" in markdown, "Should show base score"


def test_category_name_formatting():
    """Test category name formatting."""
    categories = [
        "macro_policy",
        "capital_flow",
        "major_coins",
        "altcoins_trending",
        "tech_narratives",
        "kol_insights",
    ]
    
    print("✅ Category Name Formatting:")
    for category in categories:
        formatted = DiscordFormatter._format_category_name(category)
        print(f"   {category} → {formatted}")
        assert formatted != category, "Should format category name"


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 Running Formatter Unit Tests")
    print("=" * 60 + "\n")
    
    try:
        test_discord_embed_creation()
        test_degraded_mode_embed()
        test_health_check_embed()
        test_error_embed()
        test_markdown_formatting()
        test_scoring_example_markdown()
        test_category_name_formatting()
        
        print("\n" + "=" * 60)
        print("✅ All formatter tests passed!")
        print("=" * 60 + "\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}\n")
        sys.exit(1)
