from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import feedparser
import requests
from pydantic import HttpUrl, ValidationError

from app.core.schemas import TimeRange
from app.core.source_registry import Feed as RegistryFeed
from app.core.source_registry import Publisher
from app.pipeline.gather.models import ArticleCandidate
from app.pipeline.verify.url_canonicalize import canonicalize_url

logger = logging.getLogger(__name__)


def is_valid_url(url: str) -> bool:
    """
    Validates that a URL has required components (scheme and netloc).
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


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
            # struct_time is in UTC. calendar.timegm is better than time.mktime
            # because mktime assumes local time.
            import calendar

            return datetime.fromtimestamp(calendar.timegm(struct_time), UTC)
        except (ValueError, OverflowError, TypeError):
            return None
    return None


def filter_by_time_range(
    articles: list[ArticleCandidate],
    range_enum: TimeRange,
    now: datetime | None = None,
) -> list[ArticleCandidate]:
    """
    Filters articles based on TimeRange (24h, 3d, 7d).
    Accepts an optional `now` parameter for deterministic testing.
    """
    if now is None:
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
    Deduplicates articles by canonical URL.
    """
    seen_urls = set()
    deduped = []
    for a in articles:
        url_str = canonicalize_url(str(a.url))
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
        now: datetime | None = None,
    ) -> list[ArticleCandidate]:
        """
        Fetches or takes raw XML, parses, normalizes, and filters.
        """
        if raw_xml:
            d = feedparser.parse(raw_xml)
        else:
            # Use requests with User-Agent and timeout
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            try:
                resp = requests.get(
                    str(feed_registry.url), headers=headers, timeout=self.timeout_seconds
                )
                resp.raise_for_status()
                d = feedparser.parse(resp.content)
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch feed {feed_registry.url}: {e}")
                return []

        candidates: list[ArticleCandidate] = []
        skipped_count = {
            "no_link": 0, "invalid_url": 0,
            "domain_not_allowed": 0, "validation_error": 0
        }

        for entry in d.entries:
            link = getattr(entry, "link", None)
            if not link:
                skipped_count["no_link"] += 1
                continue

            # Rule 1: Validate URL format
            if not is_valid_url(link):
                skipped_count["invalid_url"] += 1
                logger.debug(f"Skipping invalid URL: {link}")
                continue

            # Rule 2: Enforce allowlist by domain
            if not is_domain_allowed(link, publisher.allowed_domains):
                skipped_count["domain_not_allowed"] += 1
                logger.debug(f"Skipping URL from non-allowed domain: {link}")
                continue

            published_at = parse_rss_date(entry)

            # Rule 3: Normalize into ArticleCandidate
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
            except ValidationError as e:
                skipped_count["validation_error"] += 1
                title = getattr(entry, 'title', 'No Title')
                logger.debug(f"Validation error for entry '{title}': {e}")
                continue

        total_skipped = sum(skipped_count.values())
        if total_skipped > 0:
            logger.info(
                f"Feed {feed_registry.url}: gathered {len(candidates)} candidates, "
                f"skipped {total_skipped} (no_link={skipped_count['no_link']}, "
                f"invalid_url={skipped_count['invalid_url']}, "
                f"domain_not_allowed={skipped_count['domain_not_allowed']}, "
                f"validation_error={skipped_count['validation_error']})"
            )

        # Rule 4: Time-range filtering
        candidates = filter_by_time_range(candidates, time_range, now=now)

        # Rule 5: URL dedupe
        candidates = deduplicate_articles(candidates)

        return candidates
