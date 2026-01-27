from datetime import UTC, datetime, timedelta

from pydantic import HttpUrl

from app.core.schemas import Topic
from app.pipeline.gather.models import ArticleCandidate
from app.pipeline.verify.dedupe import dedupe_by_canonical_url
from app.pipeline.verify.url_canonicalize import canonicalize_url


def test_canonicalize_url():
    # Base normalization
    assert canonicalize_url("HTTPS://Example.COM/Path") == "https://example.com/Path"
    
    # Strip fragment
    assert canonicalize_url("https://example.com/path#fragment") == "https://example.com/path"
    
    # Remove default ports
    assert canonicalize_url("http://example.com:80/path") == "http://example.com/path"
    assert canonicalize_url("https://example.com:443/path") == "https://example.com/path"
    assert canonicalize_url("https://example.com:8443/path") == "https://example.com:8443/path"
    
    # Remove tracking params
    url = "https://example.com/path?utm_source=news&gclid=123&keep=true&fbclid=abc"
    # Keep 'keep', remove utm_*, gclid, fbclid
    assert canonicalize_url(url) == "https://example.com/path?keep=true"
    
    # Sort params
    url = "https://example.com/path?b=2&a=1"
    assert canonicalize_url(url) == "https://example.com/path?a=1&b=2"

def test_dedupe_by_canonical_url():
    now = datetime.now(UTC)
    earlier = now - timedelta(hours=1)
    
    # Same canonical URL, different publishers
    c1 = ArticleCandidate(
        title="Title 1",
        url=HttpUrl("https://example.com/p1?utm_source=a"),
        publisher_name="Pub A",
        published_at=earlier,
        topic=Topic.TECH,
        summary="Short summary"
    )
    c2 = ArticleCandidate(
        title="Title 2",
        url=HttpUrl("https://example.com/p1?utm_source=b"),
        publisher_name="Pub B",
        published_at=now,
        topic=Topic.TECH,
        summary="Longer summary of the same article"
    )
    
    # Should keep c2 because it's newer
    deduped = dedupe_by_canonical_url([c1, c2])
    assert len(deduped) == 1
    assert deduped[0].publisher_name == "Pub B"
    
    # Tie-breaker: None vs published_at
    c3 = ArticleCandidate(
        title="Title 3",
        url=HttpUrl("https://example.com/p2"),
        publisher_name="Pub C",
        published_at=None,
        topic=Topic.TECH,
        summary="Summary"
    )
    c4 = ArticleCandidate(
        title="Title 4",
        url=HttpUrl("https://example.com/p2"),
        publisher_name="Pub D",
        published_at=now,
        topic=Topic.TECH,
        summary="S"
    )
    deduped = dedupe_by_canonical_url([c3, c4])
    assert len(deduped) == 1
    assert deduped[0].published_at == now
    
    # Tie-breaker: Summary length if both published_at are None
    c5 = ArticleCandidate(
        title="Title 5",
        url=HttpUrl("https://example.com/p3"),
        publisher_name="Pub E",
        published_at=None,
        topic=Topic.TECH,
        summary="Short"
    )
    c6 = ArticleCandidate(
        title="Title 6",
        url=HttpUrl("https://example.com/p3"),
        publisher_name="Pub F",
        published_at=None,
        topic=Topic.TECH,
        summary="Much longer summary"
    )
    deduped = dedupe_by_canonical_url([c5, c6])
    assert len(deduped) == 1
    assert deduped[0].summary == "Much longer summary"
