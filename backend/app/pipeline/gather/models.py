from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, HttpUrl

from app.core.schemas import Topic


class ArticleCandidate(BaseModel):
    title: str
    url: HttpUrl
    publisher_name: str
    published_at: datetime | None
    topic: Topic
    summary: str | None = None
