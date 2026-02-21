from datetime import datetime

from pydantic import HttpUrl

from app.core.schemas import Topic
from app.pipeline.gather.models import ArticleCandidate
from app.pipeline.verify.verify_items import filter_by_topics


def create_article(title: str, summary: str, topic: Topic = Topic.DAILY) -> ArticleCandidate:
    return ArticleCandidate(
        title=title,
        url=HttpUrl("https://example.com/article"),
        publisher_name="Example News",
        published_at=datetime.now(),
        topic=topic,
        summary=summary
    )

def test_filter_by_topics_tech_only():
    articles = [
        create_article("AI chip released", "NVIDIA announced a new chip", Topic.DAILY),
        create_article("Stock market crash", "Markets are down today", Topic.DAILY),
        create_article("New vaccine approved", "Health officials approved vaccine", Topic.DAILY),
        create_article("Python tutorial", "Learn how to code in Python", Topic.DAILY),
        create_article("Weather update", "It will rain today", Topic.DAILY),
        create_article("Local news report", "Some local event happened", Topic.DAILY),
    ]
    
    # Filter for Tech
    filtered = filter_by_topics(articles, [Topic.TECH])
    
    # "AI chip released" should be tagged TECH and returned
    assert len(filtered) == 1
    assert filtered[0].title == "AI chip released"
    assert filtered[0].topic == Topic.TECH

def test_filter_by_topics_fallback():
    articles = [
        create_article("Stock market crash", "Finance markets are down today", Topic.DAILY),
        create_article("Daily weather update", "It will rain today", Topic.DAILY),
    ]
    
    # Request Health, which is not present.
    # Fallback behavior: if no matches and DAILY not requested, returns DAILY items.
    filtered = filter_by_topics(articles, [Topic.HEALTH])
    
    assert len(filtered) > 0
    assert all(a.topic == Topic.DAILY for a in filtered)
    # The weather update has "daily" and "today" which are DAILY keywords.
    # Actually filter_by_topics calls tag_topics which returns DAILY if no keywords match.
    # So both might be returned as DAILY if they don't match HEALTH.

def test_filter_by_topics_multi_request():
    articles = [
        create_article("AI chip released", "NVIDIA announced a new chip", Topic.DAILY),
        create_article("Stock market crash", "Finance markets are down today", Topic.DAILY),
    ]
    
    filtered = filter_by_topics(articles, [Topic.TECH, Topic.FINANCE])
    assert len(filtered) == 2
    topics = {a.topic for a in filtered}
    assert Topic.TECH in topics
    assert Topic.FINANCE in topics
