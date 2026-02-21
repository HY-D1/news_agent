from __future__ import annotations

from dataclasses import dataclass

from app.pipeline.gather.models import ArticleCandidate


@dataclass
class ArticleCluster:
    """Internal cluster of articles representing the same story."""
    lead: ArticleCandidate
    members: list[ArticleCandidate]
    
    @property
    def articles(self) -> list[ArticleCandidate]:
        return [self.lead] + self.members

    @property
    def publishers(self) -> set[str]:
        return {a.publisher_name for a in self.articles}
