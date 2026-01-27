from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import HttpUrl

from app.core.schemas import (
    Bullet,
    Citation,
    ConfidenceTag,
    DigestCard,
    DigestRequest,
    DigestResponse,
    QAStatus,
    Topic,
)
from app.core.source_registry import get_feeds_for_request, load_source_registry
from app.pipeline.gather.models import ArticleCandidate
from app.pipeline.gather.rss_gatherer import RSSGatherer
from app.pipeline.verify.topic_tagger import tag_topics
from app.pipeline.verify.verify_items import deduplicate_candidates, filter_by_topics

SOURCES_PATH = Path(__file__).parent.parent / "resources" / "sources.yaml"


# Tagging and filtering now handled in app/pipeline/verify/


def get_title_signature(title: str) -> set[str]:
    """
    Returns a set of significant words from the title.
    """
    words = re.findall(r"\w+", title.lower())
    # Filter out common short words
    return {w for w in words if len(w) > 3}


def are_related(sig1: set[str], sig2: set[str]) -> bool:
    """
    Simple overlap check to see if two titles are likely related stories.
    """
    if not sig1 or not sig2:
        return False
    intersection = sig1.intersection(sig2)
    # Share 2+ words and >= 40% of keywords
    return len(intersection) >= 2 and (len(intersection) / min(len(sig1), len(sig2)) >= 0.4)


def refine_topic(title: str, summary: str | None, original_topic: Topic) -> Topic:
    """
    Helper to refine topic from DAILY to a more specific one if keywords match.
    Preserves non-DAILY original topics.
    """
    if original_topic != Topic.DAILY:
        return original_topic

    tags = tag_topics(title, summary)
    for t in [Topic.TECH, Topic.FINANCE, Topic.HEALTH, Topic.LEARNING]:
        if t in tags:
            return t
    return Topic.DAILY


def build_digest(req: DigestRequest) -> DigestResponse:
    """
    Day 3 Implementation:
    Gather real news, refine topics, cluster related stories, and rank.
    """
    now = datetime.now(UTC)

    # 1. Load Source Registry
    registry = load_source_registry(SOURCES_PATH)
    matches = get_feeds_for_request(registry, req.regions, req.topics)

    # 2. If no feeds found, return mock
    if not matches:
        return build_mock_digest(
            req, notes=["No feeds configured for these regions/topics. Showing mock demo data."]
        )

    # 3. Gather real data
    gatherer = RSSGatherer()
    all_candidates = []
    for pub, feed in matches:
        try:
            candidates = gatherer.gather(pub, feed, req.range)
            all_candidates.extend(candidates)
        except Exception:
            continue

    # 4. If no articles found, return mock with note
    if not all_candidates:
        return build_mock_digest(
            req, notes=["No recent articles found in feeds. Showing mock demo data."]
        )

    # Global deduplication across all gathered items using canonical URLs
    unique_candidates = deduplicate_candidates(all_candidates)

    # 5. Refine Topics and Filter by requested topics
    refined_candidates = filter_by_topics(unique_candidates, req.topics)

    # 6. Clustering related stories
    # We'll group candidates by topic first, then cluster within topic.
    clusters: list[list[ArticleCandidate]] = []
    
    # Sort by date descending before clustering so oldest stories don't accidentally become leads
    refined_candidates.sort(
        key=lambda x: x.published_at or datetime.min.replace(tzinfo=UTC), reverse=True
    )

    for can in refined_candidates:
        assigned = False
        sig = get_title_signature(can.title)
        
        for cluster in clusters:
            # Check if it matches the lead story of any cluster (within same topic)
            lead = cluster[0]
            if lead.topic == can.topic and are_related(get_title_signature(lead.title), sig):
                cluster.append(can)
                assigned = True
                break
        
        if not assigned:
            clusters.append([can])

    # 7. Convert Clusters to DigestCards and Apply Constraints
    cards: list[DigestCard] = []
    topic_counts: dict[Topic, int] = {}

    for cluster in clusters:
        if len(cards) >= req.max_cards:
            break
            
        lead = cluster[0]
        t = lead.topic
        count = topic_counts.get(t, 0)
        if count >= req.max_cards_per_topic:
            continue

        # Combine citations
        citations = []
        seen_publishers = set()
        for c in cluster:
            cit = Citation(
                publisher=c.publisher_name, url=c.url, published_at=c.published_at
            )
            citations.append(cit)
            seen_publishers.add(c.publisher_name)

        # Multi-source if more than one publisher
        confidence = (
            ConfidenceTag.MULTI_SOURCE if len(seen_publishers) > 1
            else ConfidenceTag.SINGLE_SOURCE
        )

        # Simple ID generation from lead URL
        cid = hashlib.md5(str(lead.url).encode()).hexdigest()[:12]

        bullet_text = "Headline summary from source."
        if lead.summary:
            clean_summary = lead.summary.split("<")[0].strip()
            if clean_summary:
                bullet_text = clean_summary[:230]

        cards.append(
            DigestCard(
                id=f"rss-{cid}",
                topic=t,
                headline=lead.title[:155],
                publisher=lead.publisher_name,
                published_at=lead.published_at or now,
                confidence=confidence,
                bullets=[Bullet(text=bullet_text, citations=[citations[0]])],
                sources=citations,
            )
        )
        topic_counts[t] = count + 1

    # Final Ranking: Multi-source first, then by date
    cards.sort(
        key=lambda x: (x.confidence == ConfidenceTag.MULTI_SOURCE, x.published_at),
        reverse=True
    )

    # 8. QA Final Gate
    # Ensure all cards have citations and meet basic quality
    final_cards = []
    for card in cards:
        if not card.bullets or not card.sources:
            continue
        # Every bullet must have at least one citation
        if any(not b.citations for b in card.bullets):
            continue
        final_cards.append(card)

    qa_status = QAStatus.PASS if final_cards else QAStatus.FAIL
    qa_notes = ["Successfully gathered, refined, and clustered news from RSS."]
    if not final_cards:
        qa_notes = ["QA Check failed: No stories met quality requirements (citations/bullets)."]

    return DigestResponse(
        generated_at=now,
        qa_status=qa_status,
        request=req,
        cards=final_cards,
        qa_notes=qa_notes,
    )


def build_mock_digest(req: DigestRequest, notes: list[str] | None = None) -> DigestResponse:
    """
    Fallback mock implementation.
    """
    now = datetime.now(UTC)
    c1 = Citation(
        publisher="Mock Publisher",
        url=HttpUrl("https://example.com/story-1"),
        published_at=now,
    )
    c2 = Citation(
        publisher="Mock Publisher",
        url=HttpUrl("https://example.com/story-2"),
        published_at=now,
    )
    cards = [
        DigestCard(
            id="mock-1",
            topic=req.topics[0] if req.topics else Topic.DAILY,
            headline="Mock headline: Example story about the selected topic",
            publisher="Mock Publisher",
            published_at=now,
            confidence=ConfidenceTag.SINGLE_SOURCE,
            bullets=[
                Bullet(text="Mock bullet 1 with a citation.", citations=[c1]),
                Bullet(text="Mock bullet 2 with a citation.", citations=[c1]),
                Bullet(text="Mock bullet 3 with a citation.", citations=[c2]),
            ],
            sources=[c1, c2],
        ),
    ]

    return DigestResponse(
        generated_at=now,
        qa_status=QAStatus.FALLBACK,
        request=req,
        cards=cards,
        qa_notes=notes or ["Mock digest (Day 1 logic)."],
    )
