from app.core.schemas import Topic
from app.pipeline.gather.models import ArticleCandidate

from .topic_tagger import tag_topics
from .url_canonicalize import canonicalize_url


def filter_by_topics(
    items: list[ArticleCandidate], 
    requested: list[Topic]
) -> list[ArticleCandidate]:
    """
    Tags candidates and filters them based on requested topics.
    Maintains existing item topic and adds new ones based on keywords.
    If multiple tags match, the first matching requested topic is assigned.
    If no matches and DAILY is not requested, falls back to items tagged DAILY.
    """
    requested_set = set(requested)
    results: list[ArticleCandidate] = []

    # First pass: direct matches
    for item in items:
        tags = tag_topics(item.title, item.summary)
        # We also respect the existing topic assigned during gathering
        tags.add(item.topic)
        
        intersection = tags.intersection(requested_set)
        if intersection:
            # Pick the first requested topic that matched for the item
            # to ensure it appears in the right section in UI
            for t in requested:
                if t in intersection:
                    item.topic = t
                    break
            results.append(item)

    # Fallback to DAILY if result empty and DAILY wasn't specifically requested
    if not results and Topic.DAILY not in requested_set:
        for item in items:
            tags = tag_topics(item.title, item.summary)
            tags.add(item.topic)
            if Topic.DAILY in tags:
                item.topic = Topic.DAILY
                results.append(item)

    return results

def deduplicate_candidates(items: list[ArticleCandidate]) -> list[ArticleCandidate]:
    """
    Deduplicates candidates based on canonical URL.
    Tie-breakers:
    1. Newest published_at
    2. Longer summary
    3. First seen
    """
    canonical_map: dict[str, ArticleCandidate] = {}

    for item in items:
        canonical = canonicalize_url(str(item.url))
        
        if canonical not in canonical_map:
            canonical_map[canonical] = item
            continue
            
        existing = canonical_map[canonical]
        
        # Tie-breaker 1: published_at
        if item.published_at and (
            not existing.published_at or item.published_at > existing.published_at
        ):
            canonical_map[canonical] = item
            continue
        elif (
            existing.published_at
            and item.published_at
            and item.published_at < existing.published_at
        ):
            continue
            
        # Tie-breaker 2: longer summary
        item_summary_len = len(item.summary) if item.summary else 0
        existing_summary_len = len(existing.summary) if existing.summary else 0
        
        if item_summary_len > existing_summary_len:
            canonical_map[canonical] = item

    # Return in original relative order if possible, but map values are fine
    return list(canonical_map.values())
