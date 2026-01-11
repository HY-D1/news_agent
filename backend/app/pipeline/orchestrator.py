from __future__ import annotations

from datetime import datetime, timezone

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


def build_digest(req: DigestRequest) -> DigestResponse:
    """
    Day-1 mock implementation.
    Later: this function becomes the orchestrator that calls:
    Gather -> Verify -> Summarize -> Format -> QA -> (retry/fallback)
    """
    now = datetime.now(timezone.utc)

    # Mock citations (placeholders). Later these must come from allowlisted sources.
    c1 = Citation(publisher="Mock Publisher", url="https://example.com/story-1", published_at=now)
    c2 = Citation(publisher="Mock Publisher", url="https://example.com/story-2", published_at=now)

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
        DigestCard(
            id="mock-2",
            topic=req.topics[0] if req.topics else Topic.DAILY,
            headline="Mock headline: Another example story",
            publisher="Mock Publisher",
            published_at=now,
            confidence=ConfidenceTag.MULTI_SOURCE,
            bullets=[
                Bullet(text="Mock bullet 1 (multi-source tag for demo).", citations=[c1, c2]),
                Bullet(text="Mock bullet 2 (grounded by citations).", citations=[c2]),
            ],
            sources=[c1, c2],
        ),
    ]

    return DigestResponse(
        generated_at=now,
        qa_status=QAStatus.FALLBACK,  # honest: mock data, not verified yet
        request=req,
        cards=cards,
        qa_notes=["Mock digest (Day 1). Replace with real pipeline in Day 2."],
    )
