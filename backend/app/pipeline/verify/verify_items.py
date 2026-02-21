from app.core.schemas import Topic
from app.pipeline.gather.models import ArticleCandidate

from .topic_tagger import tag_topics


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
