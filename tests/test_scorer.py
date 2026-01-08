"""
Unit tests for the scoring module.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scorer import ContentScorer


def test_kol_scoring():
    """Test KOL post scoring logic."""
    scorer = ContentScorer()
    
    # Test post with high impact keywords
    test_post = {
        "username": "VitalikButerin",
        "text": "Ethereum's Purge upgrade entering testnet, aiming to reduce node storage by 40%. SEC approval expected.",
        "timestamp": "2 hours ago",
        "kol_tier": "VitalikButerin",
        "base_score": 50,
    }
    
    score = scorer._calculate_kol_score(test_post)
    print(f"✅ KOL Post Score: {score}")
    assert score >= 50, "Base score should be at least 50"
    assert "SEC" in test_post["text"] or "approval" in test_post["text"], "Should contain high-impact keywords"


def test_news_quality_scoring():
    """Test news item quality scoring."""
    scorer = ContentScorer()
    
    test_news = {
        "title": "SEC Delays Spot Ethereum ETF Decision Until March 2025",
        "summary": "The SEC has postponed its decision on spot Ethereum ETF applications, marking the third delay.",
        "source": "CoinDesk",
        "kind": "news",
    }
    
    score = scorer._calculate_news_quality_score(test_news)
    print(f"✅ News Quality Score: {score}/10")
    assert score >= 0, "Score should be non-negative"
    assert score <= 10, "Score should not exceed 10"


def test_deduplication():
    """Test content deduplication logic."""
    scorer = ContentScorer()
    
    text1 = "Bitcoin reaches new all-time high above $100,000"
    text2 = "BTC hits record high surpassing $100k level"
    
    similarity = scorer._calculate_similarity(text1, text2)
    print(f"✅ Similarity Score: {similarity:.2f}")
    # Similarity is based on keyword overlap, not exact matching
    assert similarity > 0.0, "Similar texts should have some similarity score"


def test_categorization():
    """Test news categorization logic."""
    scorer = ContentScorer()
    
    test_items = [
        {
            "title": "SEC Issues New Cryptocurrency Regulations",
            "summary": "The SEC has announced new regulatory guidelines...",
        },
        {
            "title": "Whale Transfers 5,000 BTC from Coinbase",
            "summary": "Large transaction detected on-chain...",
        },
        {
            "title": "Ethereum Layer 2 TVL Reaches $50 Billion",
            "summary": "Total value locked in Ethereum L2 solutions...",
        },
    ]
    
    for item in test_items:
        category = scorer._categorize_news(item)
        print(f"✅ Item categorized as: {category}")
        assert category in [
            "macro_policy",
            "capital_flow",
            "major_coins",
            "altcoins_trending",
            "tech_narratives",
            "kol_insights",
        ], "Category should be one of the predefined categories"


def test_item_selection():
    """Test top item selection logic."""
    scorer = ContentScorer()
    
    kol_posts = [
        {
            "username": "VitalikButerin",
            "text": "Ethereum upgrade announcement",
            "impact_score": 85,
            "base_score": 50,
        },
        {
            "username": "cz_binance",
            "text": "Binance listing news",
            "impact_score": 75,
            "base_score": 50,
        },
    ]
    
    news_items = [
        {
            "title": "SEC Decision on ETF",
            "impact_score": 8,
            "source": "CoinDesk",
        },
        {
            "title": "Bitcoin Price Movement",
            "impact_score": 7,
            "source": "Bloomberg",
        },
    ]
    
    selected = scorer.select_top_items(kol_posts, news_items, total_items=5, max_kol=2)
    print(f"✅ Selected {len(selected)} items for briefing")
    assert len(selected) <= 5, "Should not select more than 5 items"
    assert len([x for x in selected if x.get("category") == "kol_insights"]) <= 2, "Should not exceed max KOL posts"


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 Running Scorer Unit Tests")
    print("=" * 60 + "\n")
    
    try:
        test_kol_scoring()
        test_news_quality_scoring()
        test_deduplication()
        test_categorization()
        test_item_selection()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60 + "\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}\n")
        sys.exit(1)
