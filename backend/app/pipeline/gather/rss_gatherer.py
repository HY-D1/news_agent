from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import feedparser
from pydantic import HttpUrl

from app.core.schemas import TimeRange
from app.core.source_registry import Feed as RegistryFeed
from app.core.source_registry import Publisher
from app.pipeline.gather.models import ArticleCandidate


def is_domain_allowed(url: str, allowed_domains: list[str]) -> bool:
    """
    Checks if the URL domain matches or is a subdomain of any allowed domains.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    if not domain:
        return False

    for allowed in allowed_domains:
        allowed = allowed.lower()
        if domain == allowed or domain.endswith("." + allowed):
            return True
    return False


def parse_rss_date(entry: feedparser.FeedParserDict) -> datetime | None:
    """
    Gracefully handles different RSS date formats.
    """
    struct_time = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if struct_time:
        try:
            return datetime.fromtimestamp(time.mktime(struct_time), UTC)
        except (ValueError, OverflowError, TypeError):
            return None
    return None


def filter_by_time_range(
    articles: list[ArticleCandidate], range_enum: TimeRange
) -> list[ArticleCandidate]:
    """
    Filters articles based on TimeRange (24h, 3d, 7d).
    """
    now = datetime.now(UTC)
    if range_enum == TimeRange.H24:
        delta = timedelta(hours=24)
    elif range_enum == TimeRange.D3:
        delta = timedelta(days=3)
    elif range_enum == TimeRange.D7:
        delta = timedelta(days=7)
    else:
        return articles

    cutoff = now - delta
    return [a for a in articles if a.published_at and a.published_at >= cutoff]


def deduplicate_articles(articles: list[ArticleCandidate]) -> list[ArticleCandidate]:
    """
    Deduplicates articles by URL.
    """
    seen_urls = set()
    deduped = []
    for a in articles:
        url_str = str(a.url)
        if url_str not in seen_urls:
            seen_urls.add(url_str)
            deduped.append(a)
    return deduped


class RSSGatherer:
    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds

    def gather(
        self,
        publisher: Publisher,
        feed_registry: RegistryFeed,
        time_range: TimeRange,
        raw_xml: str | None = None,
    ) -> list[ArticleCandidate]:
        """
        Fetches or takes raw XML, parses, normalizes, and filters.
        """
        if raw_xml:
            d = feedparser.parse(raw_xml)
        else:
            # In a real app, you'd fetch with requests/httpx here
            # But the user asked for a fetch -> parse -> normalize flow.
            # I'll use feedparser's built-in fetch for simplicity unless told otherwise.
            d = feedparser.parse(str(feed_registry.url))

        candidates = []
        for entry in d.entries:
            link = getattr(entry, "link", None)
            if not link:
                continue

            # Rule 3: Enforce allowlist by domain
            if not is_domain_allowed(link, publisher.allowed_domains):
                continue

            published_at = parse_rss_date(entry)

            # Rule 2: Normalize into ArticleCandidate
            try:
                candidate = ArticleCandidate(
                    title=getattr(entry, "title", "No Title"),
                    url=HttpUrl(link),
                    publisher_name=publisher.name,
                    published_at=published_at,
                    topic=feed_registry.topic,
                    summary=getattr(entry, "summary", None),
                )
                candidates.append(candidate)
            except Exception:
                # Log or skip malformed URLs
                continue

        # Rule 4: Time-range filtering
        candidates = filter_by_time_range(candidates, time_range)

        # Rule 5: URL dedupe
        candidates = deduplicate_articles(candidates)

        return candidates
