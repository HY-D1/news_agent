import sys
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests

# Add backend to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))
from app.core.source_registry import load_source_registry

SOURCES_PATH = Path(__file__).parent.parent / "app" / "resources" / "sources.yaml"


def is_domain_allowed(url, allowed_domains):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    for allowed in allowed_domains:
        if domain == allowed or domain.endswith("." + allowed):
            return True
    return False


def validate():
    registry = load_source_registry(SOURCES_PATH)

    print("| Region | Publisher | Feed URL | Status | Reason |")
    print("|---|---|---|---|---|")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    for rs in registry.regions:
        for pub in rs.publishers:
            for feed in pub.feeds:
                region = rs.region.value
                pub_name = pub.name
                feed_url = str(feed.url)
                allowed = pub.allowed_domains

                try:
                    resp = requests.get(feed_url, headers=headers, timeout=15)
                    if resp.status_code != 200:
                        print(
                            f"| {region} | {pub_name} | {feed_url} | "
                            f"FAIL | HTTP {resp.status_code} |"
                        )
                        continue

                    d = feedparser.parse(resp.content)
                    if not d.entries:
                        print(f"| {region} | {pub_name} | {feed_url} | FAIL | No entries found |")
                        continue

                    mismatch = []
                    for entry in d.entries[:3]:
                        link = getattr(entry, "link", None)
                        if not link or not is_domain_allowed(link, allowed):
                            mismatch.append(link)

                    if mismatch:
                        print(
                            f"| {region} | {pub_name} | {feed_url} | "
                            f"FAIL | Domain mismatch: {mismatch[0]} |"
                        )
                    else:
                        print(f"| {region} | {pub_name} | {feed_url} | PASS | OK |")

                except Exception as e:
                    print(f"| {region} | {pub_name} | {feed_url} | FAIL | {str(e)} |")


if __name__ == "__main__":
    validate()
