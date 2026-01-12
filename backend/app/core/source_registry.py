from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, HttpUrl

from app.core.schemas import Region, Topic


class Feed(BaseModel):
    name: str
    url: HttpUrl
    topic: Topic


class Publisher(BaseModel):
    name: str
    allowed_domains: list[str]
    feeds: list[Feed]


class RegionSources(BaseModel):
    region: Region
    publishers: list[Publisher]


class SourceRegistry(BaseModel):
    regions: list[RegionSources]


def load_source_registry(path: Path) -> SourceRegistry:
    """
    Loads and validates sources.yaml into a typed SourceRegistry object.
    """
    if not path.exists():
        return SourceRegistry(regions=[])

    with open(path) as f:
        data = yaml.safe_load(f)

    if not data:
        return SourceRegistry(regions=[])

    return SourceRegistry.model_validate(data)


def get_feeds_for_request(
    registry: SourceRegistry, regions: list[Region], topics: list[Topic]
) -> list[tuple[Publisher, Feed]]:
    """
    Returns a list of (Publisher, Feed) tuples that match requested regions and topics.
    If no feed matches the specific topic, it falls back to Topic.DAILY for that publisher.
    """
    matches = []
    requested_regions_set = set(regions)
    requested_topics_set = set(topics)

    for rs in registry.regions:
        if rs.region in requested_regions_set:
            for pub in rs.publishers:
                pub_matches = []
                # First pass: try to find exact topic matches
                for feed in pub.feeds:
                    if feed.topic in requested_topics_set:
                        pub_matches.append((pub, feed))

                # Second pass: if no specific topic matches for this publisher,
                # fallback to DAILY feeds.
                if not pub_matches:
                    for feed in pub.feeds:
                        if feed.topic == Topic.DAILY:
                            pub_matches.append((pub, feed))

                matches.extend(pub_matches)
    return matches
