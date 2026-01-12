from urllib.parse import urlparse

import feedparser
import requests


def is_domain_allowed(url, allowed_domains):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    for allowed in allowed_domains:
        if domain == allowed or domain.endswith("." + allowed):
            return True
    return False


FEEDS = [
    ("Canada", "CBC News", "https://www.cbc.ca/cmlink/rss-topstories", ["cbc.ca"]),
    ("Canada", "Global News", "https://globalnews.ca/feed/", ["globalnews.ca"]),
    (
        "UK",
        "BBC News",
        "http://feeds.bbci.co.uk/news/rss.xml",
        ["bbc.co.uk", "bbci.co.uk", "bbc.com"],
    ),
    ("UK", "The Guardian", "https://www.theguardian.com/uk/rss", ["theguardian.com"]),
    (
        "USA",
        "NYT",
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        ["nytimes.com"],
    ),
    ("USA", "NPR", "https://feeds.npr.org/1001/rss.xml", ["npr.org"]),
    (
        "China",
        "China Daily",
        "http://www.chinadaily.com.cn/rss/cndy_rss.xml",
        ["chinadaily.com.cn"],
    ),
    ("China", "SCMP Latest", "https://www.scmp.com/rss/92/feed", ["scmp.com"]),
]


def validate():
    print("| Region | Publisher | Feed URL | Status | Reason |")
    print("|---|---|---|---|---|")
    for region, pub, url, allowed in FEEDS:
        try:
            # Add User-Agent to avoid blocks
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"| {region} | {pub} | {url} | FAIL | HTTP {resp.status_code} |")
                continue

            d = feedparser.parse(resp.content)
            if not d.entries:
                print(f"| {region} | {pub} | {url} | FAIL | No entries found |")
                continue

            mismatch = []
            for entry in d.entries[:3]:
                link = getattr(entry, "link", None)
                if not link or not is_domain_allowed(link, allowed):
                    mismatch.append(link)

            if mismatch:
                print(f"| {region} | {pub} | {url} | FAIL | Domain mismatch: {mismatch[0]} |")
            else:
                print(f"| {region} | {pub} | {url} | PASS | OK |")

        except Exception as e:
            print(f"| {region} | {pub} | {url} | FAIL | {str(e)} |")


if __name__ == "__main__":
    validate()
