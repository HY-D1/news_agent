from datetime import UTC, datetime
from pathlib import Path

from pydantic import HttpUrl

from app.core.schemas import TimeRange, Topic
from app.core.source_registry import Feed as RegistryFeed
from app.core.source_registry import Publisher
from app.pipeline.gather.rss_gatherer import RSSGatherer

# Deterministic "now" for testing: Jan 12, 2026 noon
TEST_NOW = datetime(2026, 1, 12, 12, 0, 0, tzinfo=UTC)


def test_rss_gatherer_deterministic_filtering():
    fixture_path = Path(__file__).parent / "fixtures" / "sample_rss.xml"
    with open(fixture_path) as f:
        xml_content = f.read()

    publisher = Publisher(name="CBC", allowed_domains=["cbc.ca"], feeds=[])
    feed_registry = RegistryFeed(
        name="Top Stories", url=HttpUrl("https://cbc.ca/rss"), topic=Topic.DAILY
    )

    gatherer = RSSGatherer()

    # Fixture dates:
    # Story 1: Jan 12 10:00 (2h old)
    # Story 2: Jan 11 10:00 (26h old)
    # Story 3: Jan 12 10:00 (Malicious domain)
    # Story 4: Jan 1 10:00 (11 days old)
    # Story 5: Jan 12 11:00 (Duplicate of Story 1)

    # Test H24 (24h)
    results = gatherer.gather(
        publisher=publisher,
        feed_registry=feed_registry,
        time_range=TimeRange.H24,
        raw_xml=xml_content,
        now=TEST_NOW,
    )
    # Only Story 1 (CBC) and Story 5 (CBC, dup) are < 24h.
    # Story 1 is kept, Story 5 is deduped. Story 2 is 26h > 24h.
    assert len(results) == 1
    assert str(results[0].url) == "https://cbc.ca/tech-breakthrough"

    # Test D3 (3 days)
    results_3d = gatherer.gather(
        publisher=publisher,
        feed_registry=feed_registry,
        time_range=TimeRange.D3,
        raw_xml=xml_content,
        now=TEST_NOW,
    )
    # Story 1 and Story 2 are < 3 days. Story 4 is not.
    assert len(results_3d) == 2
    urls = [str(r.url) for r in results_3d]
    assert "https://cbc.ca/tech-breakthrough" in urls
    assert "https://cbc.ca/finance-update" in urls


def test_domain_allowlist_subdomain():
    from app.pipeline.gather.rss_gatherer import is_domain_allowed

    assert is_domain_allowed("https://m.cbc.ca/story", ["cbc.ca"]) is True
    assert is_domain_allowed("https://cbc.ca.malicious.com/story", ["cbc.ca"]) is False
    assert is_domain_allowed("https://other.com/story", ["cbc.ca"]) is False


def test_real_feeds_schema_validation():
    # Verify we can load the real sources.yaml
    from pathlib import Path

    from app.core.source_registry import load_source_registry

    sources_path = Path(__file__).parent.parent / "resources" / "sources.yaml"
    registry = load_source_registry(sources_path)

    # Check some known data from our populated sources.yaml
    regions = [rs.region.value for rs in registry.regions]
    assert "canada" in regions
    assert "usa" in regions
    assert "uk" in regions
    assert "china" in regions

    # Check CBC Tech feed exists
    canada = next(rs for rs in registry.regions if rs.region.value == "canada")
    cbc = next(pub for pub in canada.publishers if pub.name == "CBC News")
    tech_feed = next(f for f in cbc.feeds if f.topic == Topic.TECH)
    assert str(tech_feed.url) == "https://www.cbc.ca/cmlink/rss-technology"
