from __future__ import annotations

import re

from app.pipeline.gather.models import ArticleCandidate


def get_title_signature(title: str) -> set[str]:
    """
    Returns a set of significant words from the title (words > 3 chars).
    """
    words = re.findall(r"\w+", title.lower())
    return {w for w in words if len(w) > 3}


def calculate_similarity(sig1: set[str], sig2: set[str]) -> float:
    """
    Calculates the overlap coefficient between two sets of words.
    Formula: |A ∩ B| / min(|A|, |B|)
    """
    if not sig1 or not sig2:
        return 0.0
    intersection = sig1.intersection(sig2)
    return len(intersection) / min(len(sig1), len(sig2))


def cluster_articles(
    items: list[ArticleCandidate], threshold: float = 0.60
) -> list[list[ArticleCandidate]]:
    """
    Greedy clustering of articles based on title similarity.
    Items should be pre-sorted by published_at DESC for deterministic lead selection.
    Each item is only compared to the lead (newest) item of existing clusters.
    """
    clusters: list[list[ArticleCandidate]] = []

    for item in items:
        assigned = False
        sig = get_title_signature(item.title)

        for cluster in clusters:
            lead = cluster[0]
            # Must be same topic to cluster
            if lead.topic == item.topic:
                lead_sig = get_title_signature(lead.title)
                if calculate_similarity(lead_sig, sig) >= threshold:
                    cluster.append(item)
                    assigned = True
                    break

        if not assigned:
            clusters.append([item])

    return clusters
