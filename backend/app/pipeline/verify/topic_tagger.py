import re

from app.core.schemas import Topic

from .topic_keywords import TOPIC_KEYWORDS


def tag_topics(title: str, summary: str | None) -> set[Topic]:
    """
    Deterministically tags an article based on keywords in title and summary.
    If no keywords match, returns {Topic.DAILY}.
    """
    # Normalize text: lowercase and collapse whitespace
    text = f"{title} {summary or ''}".lower()
    text = " ".join(text.split())

    tags: set[Topic] = set()

    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            # Simple substring match (simple v1)
            # We use word boundaries to avoid matching "ai" in "daily"
            # while still keeping the logic simple and deterministic.
            pattern = rf"\b{re.escape(kw.lower())}\b"
            if re.search(pattern, text):
                tags.add(topic)
                break

    if not tags:
        return {Topic.DAILY}

    return tags
