from __future__ import annotations

from app.pipeline.gather.models import ArticleCandidate
from app.pipeline.verify.url_canonicalize import canonicalize_url


def dedupe_by_canonical_url(items: list[ArticleCandidate]) -> list[ArticleCandidate]:
    """
    Deduplicates ArticleCandidate items based on their canonicalized URL.

    Tie-breaker rules:
    - Prefer items with published_at not None
    - If both have published_at, keep newest
    - Else prefer longer summary
    """
    canonical_map: dict[str, ArticleCandidate] = {}

    for item in items:
        url_str = str(item.url)
        canonical = canonicalize_url(url_str)

        if canonical not in canonical_map:
            canonical_map[canonical] = item
            continue

        existing = canonical_map[canonical]

        # Tie-breaker logic
        keep_new = False

        if item.published_at is not None and existing.published_at is None:
            keep_new = True
        elif item.published_at is not None and existing.published_at is not None:
            if item.published_at > existing.published_at:
                keep_new = True
        elif item.published_at is None and existing.published_at is None:
            # Both None, compare summary length
            item_summary_len = len(item.summary) if item.summary else 0
            existing_summary_len = len(existing.summary) if existing.summary else 0
            if item_summary_len > existing_summary_len:
                keep_new = True

        if keep_new:
            canonical_map[canonical] = item

    return list(canonical_map.values())
