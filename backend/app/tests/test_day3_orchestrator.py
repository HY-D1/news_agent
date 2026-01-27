from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from pydantic import HttpUrl

from app.core.schemas import ConfidenceTag, DigestRequest, Region, TimeRange, Topic
from app.pipeline.gather.models import ArticleCandidate
from app.pipeline.orchestrator import build_digest, refine_topic


def test_refine_topic_basic():
    # TECH keywords in title
    assert refine_topic("New AI breakthrough", None, Topic.DAILY) == Topic.TECH
    # FINANCE keywords in summary
    assert refine_topic(
        "Market Update", "The stock market is up today.", Topic.DAILY
    ) == Topic.FINANCE
    # HEALTH
    assert refine_topic(
        "New medical study", "Vaccine results are promising.", Topic.DAILY
    ) == Topic.HEALTH
    # Fallback
    assert refine_topic("Normal News Day", "Nothing much happened.", Topic.DAILY) == Topic.DAILY
    # Specific topic from feed should be preserved
    assert refine_topic("New AI breakthrough", None, Topic.FINANCE) == Topic.FINANCE


@patch("app.pipeline.orchestrator.load_source_registry")
@patch("app.pipeline.orchestrator.get_feeds_for_request")
@patch("app.pipeline.orchestrator.RSSGatherer.gather")
def test_build_digest_topic_constraints(mock_gather, mock_get_feeds, mock_load_registry):
    # Setup mocks
    mock_load_registry.return_value = MagicMock()
    mock_get_feeds.return_value = [("Publisher A", MagicMock())]
    
    now = datetime.now(UTC)
    mock_gather.return_value = [
        ArticleCandidate(
            title="Tech news 1", url=HttpUrl("https://a.com/1"), publisher_name="A",
            published_at=now, topic=Topic.TECH, summary="AI"
        ),
        ArticleCandidate(
            title="Tech news 2", url=HttpUrl("https://a.com/2"), publisher_name="A",
            published_at=now, topic=Topic.TECH, summary="AI"
        ),
        ArticleCandidate(
            title="Finance news 1", url=HttpUrl("https://a.com/3"), publisher_name="A",
            published_at=now, topic=Topic.FINANCE, summary="Market"
        ),
    ]

    # Use a request that limits per topic
    req = DigestRequest(
        topics=[Topic.TECH, Topic.FINANCE],
        range=TimeRange.H24,
        regions=[Region.GLOBAL],
        max_cards=10,
        max_cards_per_topic=1  # Only 1 card per topic allowed
    )

    resp = build_digest(req)

    # Should have 2 cards total (1 for TECH, 1 for FINANCE)
    assert len(resp.cards) == 2
    topics = [c.topic for c in resp.cards]
    assert topics.count(Topic.TECH) == 1
    assert topics.count(Topic.FINANCE) == 1


@patch("app.pipeline.orchestrator.load_source_registry")
@patch("app.pipeline.orchestrator.get_feeds_for_request")
@patch("app.pipeline.orchestrator.RSSGatherer.gather")
def test_build_digest_topic_filtering(mock_gather, mock_get_feeds, mock_load_registry):
    # Setup mocks
    mock_load_registry.return_value = MagicMock()
    mock_get_feeds.return_value = [("Publisher A", MagicMock())]
    
    now = datetime.now(UTC)
    mock_gather.return_value = [
        ArticleCandidate(
            title="Tech news", url=HttpUrl("https://a.com/1"), publisher_name="A",
            published_at=now, topic=Topic.DAILY, summary="AI is cool" # Will be refined to TECH
        ),
        ArticleCandidate(
            title="Random news", url=HttpUrl("https://a.com/2"), publisher_name="A",
            published_at=now, topic=Topic.DAILY, summary="Just daily news" # Stays DAILY
        ),
    ]

    # Request ONLY TECH
    req = DigestRequest(
        topics=[Topic.TECH],
        range=TimeRange.H24,
        regions=[Region.GLOBAL],
        max_cards=10,
        max_cards_per_topic=5
    )

    resp = build_digest(req)

    # Should only have 1 card (the refined TECH one)
    assert len(resp.cards) == 1
    assert resp.cards[0].topic == Topic.TECH


@patch("app.pipeline.orchestrator.load_source_registry")
@patch("app.pipeline.orchestrator.get_feeds_for_request")
@patch("app.pipeline.orchestrator.RSSGatherer.gather")
def test_build_digest_clustering(mock_gather, mock_get_feeds, mock_load_registry):
    # Setup mocks
    mock_load_registry.return_value = MagicMock()
    mock_get_feeds.return_value = [("Publisher A", MagicMock())]
    
    now = datetime.now(UTC)
    mock_gather.return_value = [
        ArticleCandidate(
            title="Massive Tech Merger Announced", url=HttpUrl("https://a.com/1"),
            publisher_name="Publisher A", published_at=now, topic=Topic.TECH,
            summary="Story A"
        ),
        ArticleCandidate(
            title="Tech Merger: Huge Deal Revealed", url=HttpUrl("https://b.com/1"),
            publisher_name="Publisher B", published_at=now, topic=Topic.TECH,
            summary="Story B"
        ),
        ArticleCandidate(
            title="Unrelated Daily News Story", url=HttpUrl("https://c.com/1"),
            publisher_name="Publisher C", published_at=now, topic=Topic.TECH,
            summary="Story C"
        ),
    ]

    req = DigestRequest(
        topics=[Topic.TECH],
        range=TimeRange.H24,
        regions=[Region.GLOBAL],
        max_cards=10,
        max_cards_per_topic=5
    )

    resp = build_digest(req)

    # Should have 2 cards (one clustered, one single)
    assert len(resp.cards) == 2
    
    # The first card should be the clustered one (due to multi-source ranking)
    multi_card = resp.cards[0]
    assert multi_card.confidence == ConfidenceTag.MULTI_SOURCE
    assert len(multi_card.sources or []) == 2
    
    # The second card should be single source
    single_card = resp.cards[1]
    assert single_card.confidence == ConfidenceTag.SINGLE_SOURCE
    assert len(single_card.sources or []) == 1
