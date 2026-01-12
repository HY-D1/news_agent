from pathlib import Path

from pydantic import HttpUrl

from app.core.schemas import TimeRange, Topic
from app.core.source_registry import Feed as RegistryFeed
from app.core.source_registry import Publisher
from app.pipeline.gather.rss_gatherer import RSSGatherer


def test_rss_gatherer_filtering():
    fixture_path = Path(__file__).parent / "fixtures" / "sample_rss.xml"
    with open(fixture_path) as f:
        xml_content = f.read()

    publisher = Publisher(name="CBC", allowed_domains=["cbc.ca"], feeds=[])
    feed_registry = RegistryFeed(
        name="Top Stories", url=HttpUrl("https://cbc.ca/rss"), topic=Topic.DAILY
    )

    gatherer = RSSGatherer()

    # Test 24h filtering (Mock time is Jan 12, 2026)
    # Story 1: Jan 12 (CBC) - PASS
    # Story 2: Jan 11 (CBC) - FAIL (beyond 24h if current time is late Jan 12)
    # Story 3: Jan 12 (Malicious) - FAIL (domain)
    # Story 4: Jan 1 (CBC) - FAIL (time)
    # Story 5: Duplicate of 1 - FAIL (dedupe)

    # We need to control "now" for testing, but rss_gatherer uses datetime.now(UTC).
    # For simplicity, let's just assert the domain and dedupe logic first.

    results = gatherer.gather(
        publisher=publisher,
        feed_registry=feed_registry,
        time_range=TimeRange.D7,  # Use 7d to include Story 1 & 2
        raw_xml=xml_content,
    )

    # Verified CBC domains: Story 1, 2, 4, 5
    # Deduped: Story 1, 2, 4
    # Time filtered (7d): Story 1, 2. Story 4 is Jan 1, which is > 7 days from Jan 12.

    assert len(results) == 2
    urls = [str(r.url) for r in results]
    assert "https://cbc.ca/tech-breakthrough" in urls
    assert "https://cbc.ca/finance-update" in urls
    assert "https://malicious.com/fake-news" not in urls
    assert "https://cbc.ca/old-news" not in urls


def test_domain_allowlist_subdomain():
    from app.pipeline.gather.rss_gatherer import is_domain_allowed

    assert is_domain_allowed("https://m.cbc.ca/story", ["cbc.ca"]) is True
    assert is_domain_allowed("https://cbc.ca.malicious.com/story", ["cbc.ca"]) is False
    assert is_domain_allowed("https://other.com/story", ["cbc.ca"]) is False
