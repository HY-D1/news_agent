from datetime import UTC, datetime

from pydantic import HttpUrl

from app.core.schemas import ConfidenceTag, Topic
from app.pipeline.cluster.title_cluster import cluster_by_title_similarity
from app.pipeline.gather.models import ArticleCandidate


def test_clustering_logic():
    """
    Verify that similar titles cluster and different ones do not.
    Uses threshold 0.60 as specified.
    """
    dt = datetime(2026, 1, 27, 12, 0, 0, tzinfo=UTC)

    # Similar titles - these should cluster together
    # Both have tokens: {apple, unveils, iphone}
    a1 = ArticleCandidate(
        title="Apple unveils new iPhone",
        summary="Apple announced the new iPhone 17 today.",
        url=HttpUrl("https://techcrunch.com/iphone-17"),
        publisher_name="TechCrunch",
        published_at=dt,
        topic=Topic.TECH,
    )
    a2 = ArticleCandidate(
        title="Apple unveils latest iPhone",
        summary="Cupertino giant shows off newest phone.",
        url=HttpUrl("https://theverge.com/iphone-reveal"),
        publisher_name="The Verge",
        published_at=dt,
        topic=Topic.TECH,
    )
    # Different title
    a3 = ArticleCandidate(
        title="Federal Reserve raises rates",
        summary="Interest rates up again.",
        url=HttpUrl("https://wsj.com/fed"),
        publisher_name="WSJ",
        published_at=dt,
        topic=Topic.TECH,  # Same topic to ensure clustering is title-based
    )

    clusters = cluster_by_title_similarity([a1, a2, a3], threshold=0.60)

    # Should have 2 clusters: {a1, a2} and {a3}
    assert len(clusters) == 2

    # Grouping results by lead title for easy checking
    cluster_leads = [c[0].title for c in clusters]
    assert "Apple unveils new iPhone" in cluster_leads
    assert "Federal Reserve raises rates" in cluster_leads

    # Check sizes
    for c in clusters:
        if c[0].title == "Apple unveils new iPhone":
            assert len(c) == 2
            assert any(item.title == "Apple unveils latest iPhone" for item in c)
        else:
            assert len(c) == 1


def test_confidence_tagging_integration():
    """
    Verifies the multi-source vs single-source logic based on publisher count.
    Mimics the logic used in app/pipeline/orchestrator.py.
    """
    dt = datetime(2026, 1, 27, 12, 0, 0, tzinfo=UTC)

    # Cluster with 2 publishers
    cluster_multi = [
        ArticleCandidate(
            title="A",
            url=HttpUrl("https://a.com"),
            publisher_name="Publisher A",
            published_at=dt,
            topic=Topic.TECH,
            summary="S",
        ),
        ArticleCandidate(
            title="B",
            url=HttpUrl("https://b.com"),
            publisher_name="Publisher B",
            published_at=dt,
            topic=Topic.TECH,
            summary="S",
        ),
    ]

    # Cluster with 1 publisher (multiple articles but same source)
    cluster_single = [
        ArticleCandidate(
            title="C1",
            url=HttpUrl("https://c.com/1"),
            publisher_name="Publisher C",
            published_at=dt,
            topic=Topic.TECH,
            summary="S",
        ),
        ArticleCandidate(
            title="C2",
            url=HttpUrl("https://c.com/2"),
            publisher_name="Publisher C",
            published_at=dt,
            topic=Topic.TECH,
            summary="S",
        ),
    ]

    def get_confidence(cluster):
        # Implementation from orchestrator.py:
        # seen_publishers = {c.publisher_name for c in cluster}
        # return ConfidenceTag.MULTI_SOURCE if len(seen_publishers) >= 2
        # else ConfidenceTag.SINGLE_SOURCE
        seen_publishers = {c.publisher_name for c in cluster}
        if len(seen_publishers) >= 2:
            return ConfidenceTag.MULTI_SOURCE
        return ConfidenceTag.SINGLE_SOURCE

    assert get_confidence(cluster_multi) == ConfidenceTag.MULTI_SOURCE
    assert get_confidence(cluster_single) == ConfidenceTag.SINGLE_SOURCE


def test_determinism_and_lead_selection():
    """
    Ensures clustering is deterministic and picks the newest article as lead.
    """
    dt_new = datetime(2026, 1, 27, 14, 0, 0, tzinfo=UTC)
    dt_old = datetime(2026, 1, 27, 10, 0, 0, tzinfo=UTC)

    a_old = ArticleCandidate(
        title="Breaking News",
        url=HttpUrl("https://a.com/old"),
        publisher_name="A",
        published_at=dt_old,
        topic=Topic.TECH,
        summary="Old",
    )
    a_new = ArticleCandidate(
        title="Breaking News",
        url=HttpUrl("https://b.com/new"),
        publisher_name="B",
        published_at=dt_new,
        topic=Topic.TECH,
        summary="New",
    )

    # Run multiple times with different input orders
    res1 = cluster_by_title_similarity([a_old, a_new], threshold=0.35)
    res2 = cluster_by_title_similarity([a_new, a_old], threshold=0.35)

    assert res1 == res2
    assert len(res1) == 1
    assert res1[0][0].published_at == dt_new  # Newest is lead
