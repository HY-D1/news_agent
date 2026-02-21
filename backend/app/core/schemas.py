from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# -----------------------------
# Enums (stable API vocabulary)
# -----------------------------
class Region(StrEnum):
    CANADA = "canada"
    USA = "usa"
    UK = "uk"
    CHINA = "china"
    GLOBAL = "global"


class Topic(StrEnum):
    TECH = "tech"
    FINANCE = "finance"
    HEALTH = "health"
    DAILY = "daily"
    LEARNING = "learning"


class TimeRange(StrEnum):
    H24 = "24h"
    D3 = "3d"
    D7 = "7d"


class ConfidenceTag(StrEnum):
    MULTI_SOURCE = "multi_source"
    SINGLE_SOURCE = "single_source"


class QAStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    FALLBACK = "fallback"  # verified links only (safe mode)


# -----------------------------
# Core models
# -----------------------------
class Citation(BaseModel):
    """
    A single source reference. Keep it minimal and stable.
    """

    publisher: str = Field(..., min_length=1, examples=["BBC News", "CBC News"])
    url: HttpUrl
    published_at: datetime | None = None


class Bullet(BaseModel):
    """
    Each bullet MUST have citations.
    """

    text: str = Field(..., min_length=1, max_length=240)
    citations: list[Citation] = Field(..., min_length=1)


class DigestCard(BaseModel):
    """
    A single story card displayed in the UI.
    """

    id: str = Field(
        ..., min_length=6, description="Stable ID, e.g., hash of canonical URL or cluster id"
    )
    topic: Topic
    headline: str = Field(..., min_length=1, max_length=160)

    publisher: str = Field(..., min_length=1)
    published_at: datetime

    confidence: ConfidenceTag = ConfidenceTag.SINGLE_SOURCE

    bullets: list[Bullet] = Field(..., min_length=1, max_length=5)

    # Optional: flat list of sources for easy UI rendering
    sources: list[Citation] | None = None


class DigestRequest(BaseModel):
    """
    Request from UI. Add new fields as optional defaults (backward compatible).
    """

    topics: list[Topic] = Field(..., min_length=1)
    range: TimeRange = TimeRange.H24
    regions: list[Region] = Field(..., min_length=1)

    # Optional filters / knobs
    publishers: list[str] | None = None
    max_cards: int = Field(12, ge=1, le=50)
    max_cards_per_topic: int = Field(5, ge=1, le=20)


class DigestResponse(BaseModel):
    """
    Response returned to UI. Stable contract.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "v1"
    generated_at: datetime
    qa_status: QAStatus

    request: DigestRequest
    cards: list[DigestCard] = Field(default_factory=list)

    # If FAIL/FALLBACK, explain why (for UI + debugging)
    qa_notes: list[str] | None = None
