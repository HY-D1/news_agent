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
from app.pipeline.gather.rss_gatherer import RSSGatherer

SOURCES_PATH = Path(__file__).parent.parent / "resources" / "sources.yaml"


def build_digest(req: DigestRequest) -> DigestResponse:
    """
    Day 2 Implementation:
    Gather real news if available in sources.yaml, else fallback to mock.
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

    # Global deduplication across all gathered items
    seen_urls = set()
    unique_candidates = []
    for can in all_candidates:
        url_str = str(can.url)
        if url_str not in seen_urls:
            seen_urls.add(url_str)
            unique_candidates.append(can)

    # 5. Convert candidates to DigestCards (Day 2 basic mapping)
    cards = []
    # Limit to max_cards
    for _i, can in enumerate(unique_candidates[: req.max_cards]):
        citation = Citation(
            publisher=can.publisher_name, url=can.url, published_at=can.published_at
        )

        # Simple ID generation
        cid = hashlib.md5(str(can.url).encode()).hexdigest()[:12]

        # In Day 2, we don't have an LLM summarizer yet,
        # so we use the feed's summary or a placeholder.
        bullet_text = "Headline summary from source."
        if can.summary:
            # Clean up HTML if any (very basic)
            clean_summary = can.summary.split("<")[0].strip()
            if clean_summary:
                bullet_text = clean_summary[:230]

        cards.append(
            DigestCard(
                id=f"rss-{cid}",
                topic=can.topic,
                headline=can.title[:155],
                publisher=can.publisher_name,
                published_at=can.published_at or now,
                confidence=ConfidenceTag.SINGLE_SOURCE,
                bullets=[Bullet(text=bullet_text, citations=[citation])],
                sources=[citation],
            )
        )

    return DigestResponse(
        generated_at=now,
        qa_status=QAStatus.PASS,
        request=req,
        cards=cards,
        qa_notes=["Successfully gathered real news from RSS."],
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
