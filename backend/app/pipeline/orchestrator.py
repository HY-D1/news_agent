from __future__ import annotations

import hashlib
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
from app.pipeline.cluster.title_cluster import cluster_by_title_similarity
from app.pipeline.gather.models import ArticleCandidate
from app.pipeline.gather.rss_gatherer import RSSGatherer
from app.pipeline.verify.dedupe import deduplicate_candidates
from app.pipeline.verify.topic_tagger import tag_topics
from app.pipeline.verify.verify_items import filter_by_topics

SOURCES_PATH = Path(__file__).parent.parent / "resources" / "sources.yaml"


# Topic tagging and filtering handled in app/pipeline/verify/


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
    # Use deterministic Jaccard-based clustering
    clusters_members = cluster_by_title_similarity(refined_candidates)

    # 7. Convert Clusters to DigestCards and Apply Constraints
    cards: list[DigestCard] = []
    topic_counts: dict[Topic, int] = {}

    for members in clusters_members:
        if len(cards) >= req.max_cards:
            break
            
        # Select primary (latest date, then longest summary)
        def get_sort_key(c: ArticleCandidate):
            pub_date = c.published_at or datetime.min.replace(tzinfo=UTC)
            summary_len = len(c.summary) if c.summary else 0
            return (pub_date, summary_len)
            
        primary = max(members, key=get_sort_key)
        
        t = primary.topic
        count = topic_counts.get(t, 0)
        if count >= req.max_cards_per_topic:
            continue

        # Combine unique citations across all members
        unique_citations: list[Citation] = []
        seen_urls = set()
        seen_publishers = set()
        
        for m in members:
            if str(m.url) not in seen_urls:
                cit = Citation(
                    publisher=m.publisher_name, 
                    url=m.url, 
                    published_at=m.published_at
                )
                unique_citations.append(cit)
                seen_urls.add(str(m.url))
                seen_publishers.add(m.publisher_name)

        # Multi-source if more than one distinct publisher
        confidence = (
            ConfidenceTag.MULTI_SOURCE if len(seen_publishers) >= 2
            else ConfidenceTag.SINGLE_SOURCE
        )

        # Simple ID generation from primary URL
        cid = hashlib.md5(str(primary.url).encode()).hexdigest()[:12]

        # Bullet generation: 1-3 bullets based on what's available
        bullets: list[Bullet] = []
        
        # 1st bullet from primary summary
        primary_text = "Headline summary from source."
        if primary.summary:
            clean_summary = primary.summary.split("<")[0].strip()
            if clean_summary:
                primary_text = clean_summary[:230]
        
        bullets.append(Bullet(text=primary_text, citations=[unique_citations[0]]))

        # Add up to 2 more bullets if there are other members with summaries
        for m in members:
            if len(bullets) >= 3:
                break
            if m == primary:
                continue
            
            if m.summary:
                m_text = m.summary.split("<")[0].strip()
                if m_text and m_text[:200] not in [b.text[:200] for b in bullets]:
                    # Find citation for this member
                    m_cit = next(
                        (c for c in unique_citations if str(c.url) == str(m.url)),
                        unique_citations[0],
                    )
                    bullets.append(Bullet(text=m_text[:230], citations=[m_cit]))

        cards.append(
            DigestCard(
                id=f"rss-{cid}",
                topic=t,
                headline=primary.title[:155],
                publisher=primary.publisher_name,
                published_at=primary.published_at or now,
                confidence=confidence,
                bullets=bullets,
                sources=unique_citations,
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
