from datetime import UTC, datetime

from pydantic import HttpUrl

from app.core.schemas import Topic
from app.pipeline.gather.models import ArticleCandidate
from app.pipeline.verify.dedupe import dedupe_by_canonical_url


def test_dedupe_same_canonical_url():
    c1 = ArticleCandidate(
        title="Title 1",
        url=HttpUrl("https://example.com/a?utm_source=x"),
        publisher_name="Pub 1",
        published_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
        topic=Topic.TECH,
        summary="Summary 1"
    )
    c2 = ArticleCandidate(
        title="Title 2",
        url=HttpUrl("https://example.com/a?utm_medium=y"),
        publisher_name="Pub 2",
        published_at=datetime(2026, 1, 1, 11, 0, tzinfo=UTC),
        topic=Topic.TECH,
        summary="Summary 2"
    )
    
    results = dedupe_by_canonical_url([c1, c2])
    assert len(results) == 1
    # Tie-breaker should keep c2 because it's newer
    assert results[0].url == HttpUrl("https://example.com/a?utm_medium=y")

def test_dedupe_tie_breaker_published_at():
    # keep newest published_at
    c1 = ArticleCandidate(
        title="Old",
        url=HttpUrl("https://example.com/a"),
        publisher_name="P1",
        published_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
        topic=Topic.TECH,
        summary="Slow news"
    )
    c2 = ArticleCandidate(
        title="New",
        url=HttpUrl("https://example.com/a"),
        publisher_name="P2",
        published_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        topic=Topic.TECH,
        summary="Fast news"
    )
    
    results = dedupe_by_canonical_url([c1, c2])
    assert len(results) == 1
    assert results[0].published_at == datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

def test_dedupe_tie_breaker_missing_published_at():
    # if published_at missing, keep longer summary
    c1 = ArticleCandidate(
        title="Short",
        url=HttpUrl("https://example.com/a"),
        publisher_name="P1",
        published_at=None,
        topic=Topic.TECH,
        summary="Short summary"
    )
    c2 = ArticleCandidate(
        title="Long",
        url=HttpUrl("https://example.com/a"),
        publisher_name="P2",
        published_at=None,
        topic=Topic.TECH,
        summary="A much longer summary that provides more detail."
    )
    
    results = dedupe_by_canonical_url([c1, c2])
    assert len(results) == 1
    assert results[0].title == "Long"

def test_dedupe_prefer_presence_of_published_at():
    c1 = ArticleCandidate(
        title="No Date",
        url=HttpUrl("https://example.com/a"),
        publisher_name="P1",
        published_at=None,
        topic=Topic.TECH,
        summary="I have a long summary but no date" * 5
    )
    c2 = ArticleCandidate(
        title="With Date",
        url=HttpUrl("https://example.com/a"),
        publisher_name="P2",
        published_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
        topic=Topic.TECH,
        summary="Short"
    )
    
    results = dedupe_by_canonical_url([c1, c2])
    assert len(results) == 1
    assert results[0].published_at is not None
