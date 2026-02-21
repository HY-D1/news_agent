from __future__ import annotations

import re
from datetime import UTC, datetime

from app.pipeline.gather.models import ArticleCandidate


def tokenize_title(title: str) -> set[str]:
    """
    Tokenizes a title into a set of lowercased words longer than 3 characters.
    """
    words = re.findall(r"\w+", title.lower())
    return {w for w in words if len(w) > 3}


def jaccard(a: set[str], b: set[str]) -> float:
    """
    Calculates the Jaccard similarity between two sets of tokens.
    """
    if not a or not b:
        return 0.0
    intersection = a.intersection(b)
    union = a.union(b)
    return len(intersection) / len(union)


def cluster_by_title_similarity(
    items: list[ArticleCandidate], threshold: float = 0.60
) -> list[list[ArticleCandidate]]:
    """
    Greedy clustering: iterate items sorted by published_at desc.
    Put item into first cluster whose representative matches above threshold.
    Else create new cluster.
    """
    # Sort by published_at desc
    sorted_items = sorted(
        items,
        key=lambda x: x.published_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )

    clusters: list[list[ArticleCandidate]] = []

    for item in sorted_items:
        tokens = tokenize_title(item.title)
        assigned = False

        for cluster in clusters:
            # First item in cluster is the representative
            lead = cluster[0]
            lead_tokens = tokenize_title(lead.title)

            if jaccard(tokens, lead_tokens) >= threshold:
                cluster.append(item)
                assigned = True
                break

        if not assigned:
            clusters.append([item])

    return clusters
