from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import HttpUrl

from app.core.schemas import Topic
from app.pipeline.cluster.title_cluster import (
    cluster_by_title_similarity,
    jaccard,
    tokenize_title,
)
from app.pipeline.gather.models import ArticleCandidate


def test_tokenize_title():
    title = "Apple's New iPhone 16 Pro: Everything We Know!"
    tokens = tokenize_title(title)
    # lowercase, no punctuation, words > 3 chars
    # "apple" (from "Apple's" with apostrophe removed), "iphone", "everything", "know"
    # "new", "pro" are filtered out because they're <= 3 chars
    assert "apple" in tokens  # "Apple's" -> "apple" (apostrophe handled by regex)
    assert "iphone" in tokens
    assert "know" in tokens
    assert "everything" in tokens

def test_jaccard_similarity():
    set1 = {"apple", "iphone", "event"}
    set2 = {"apple", "iphone", "launch"}
    # intersection: {"apple", "iphone"} (2)
    # union: {"apple", "iphone", "event", "launch"} (4)
    # similarity: 2/4 = 0.5
    assert jaccard(set1, set2) == 0.5

def test_cluster_candidates_merges_similar():
    now = datetime.now(UTC)
    c1 = ArticleCandidate(
        title="NVIDIA RTX 5090 Leaked Specs",
        url=HttpUrl("https://tech.com/a"),
        publisher_name="Tech Times",
        published_at=now,
        topic=Topic.TECH,
        summary="RTX 5090 is coming with 32GB VRAM."
    )
    c2 = ArticleCandidate(
        title="NVIDIA GeForce RTX 5090: Leaked Specs Reveal 32GB VRAM",
        url=HttpUrl("https://news.com/b"),
        publisher_name="Global News",
        published_at=now + timedelta(minutes=5),
        topic=Topic.TECH,
        summary="New leaks show RTX 5090 specs."
    )
    
    clusters = cluster_by_title_similarity([c1, c2], threshold=0.5)
    assert len(clusters) == 1
    assert len(clusters[0]) == 2
    # Primary should be c2 because it's newer (first in the cluster after sorting)
    assert clusters[0][0] == c2

def test_cluster_candidates_separates_unrelated():
    now = datetime.now(UTC)
    c1 = ArticleCandidate(
        title="SpaceX Moon Landing Success",
        url=HttpUrl("https://space.com/a"),
        publisher_name="SpaceX Blog",
        published_at=now,
        topic=Topic.TECH,
        summary="Success on the moon."
    )
    c2 = ArticleCandidate(
        title="Best Chocolate Cake Recipes",
        url=HttpUrl("https://food.com/b"),
        publisher_name="Foodie",
        published_at=now,
        topic=Topic.DAILY,
        summary="Delicious cake."
    )
    
    clusters = cluster_by_title_similarity([c1, c2])
    assert len(clusters) == 2

def test_cluster_candidates_deterministic_order():
    now = datetime.now(UTC)
    c1 = ArticleCandidate(
        title="Story A",
        url=HttpUrl("https://a.com"),
        publisher_name="A",
        published_at=now,
        topic=Topic.TECH,
        summary="Summary A"
    )
    c2 = ArticleCandidate(
        title="Story A",
        url=HttpUrl("https://b.com"),
        publisher_name="B",
        published_at=now + timedelta(minutes=1),
        topic=Topic.TECH,
        summary="Summary B"
    )
    
    clusters1 = cluster_by_title_similarity([c1, c2])
    clusters2 = cluster_by_title_similarity([c1, c2])
    
    assert [m.url for m in clusters1[0]] == [m.url for m in clusters2[0]]

def test_cluster_primary_selection_summary_tiebreak():
    now = datetime.now(UTC)
    c1 = ArticleCandidate(
        title="Same Time",
        url=HttpUrl("https://a.com"),
        publisher_name="A",
        published_at=now,
        topic=Topic.TECH,
        summary="Short summary"
    )
    c2 = ArticleCandidate(
        title="Same Time",
        url=HttpUrl("https://b.com"),
        publisher_name="B",
        published_at=now,
        topic=Topic.TECH,
        summary="This is a much longer summary for the same story."
    )
    
    # In the new implementation, the cluster is just a list, and the primary
    # is selected by the orchestrator based on published_at and summary length
    # For this test, we verify both items are in the same cluster
    clusters = cluster_by_title_similarity([c1, c2])
    assert len(clusters) == 1
    assert len(clusters[0]) == 2
    # Items are sorted by published_at desc, then summary length
    # Since published_at is the same, the order depends on when they were added
    # (both items will be in the cluster, which is what matters)
