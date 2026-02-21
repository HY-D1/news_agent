
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests


def canonicalize_url(url: str) -> str:
    """Minimal reproduction of canonicalization logic for verification."""
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        if ":" in netloc:
            host, port = netloc.rsplit(":", 1)
            if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
                netloc = host
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_params = []
        tracking_params = {
            "gclid", "fbclid", "mc_cid", "mc_eid", "igshid",
            "ref", "ref_src", "spm", "cmpid"
        }
        for key, value in query_params:
            key_lower = key.lower()
            if key_lower.startswith("utm_") or key_lower in tracking_params:
                continue
            filtered_params.append((key, value))
        filtered_params.sort()
        new_query = urlencode(filtered_params)
        return urlunparse((scheme, netloc, parsed.path, parsed.params, new_query, ""))
    except Exception:
        return url

def main():
    url = "http://localhost:8000/digest"
    payload = {
        "topics": ["tech", "finance", "daily"],
        "range": "24h",
        "regions": ["usa", "uk", "canada"],
        "max_cards": 20
    }
    
    print(f"Calling {url} with topics: {payload['topics']}...")
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error calling backend: {e}")
        print("Make sure the backend is running at http://localhost:8000")
        return

    data = response.json()
    cards = data.get("cards", [])
    
    print(f"\nResponse received at {data.get('generated_at')}")
    print(f"QA Status: {data.get('qa_status')}")
    print(f"Total cards: {len(cards)}")
    
    if not cards:
        print("No cards returned. Check if RSS feeds are reachable or if mock data was expected.")
        return

    canonical_to_original: dict[str, str] = {}
    duplicates = []
    
    for card in cards:
        # Check citations exist
        if not card.get("sources"):
            print(f"CRITICAL: Card {card.get('id')} has no sources!")
            continue
            
        for source in card["sources"]:
            source_url = str(source["url"])
            if not source_url:
                print(f"CRITICAL: Source in card {card.get('id')} has no URL!")
                continue
                
            # Verify domain is allowlisted implicitly by checking if it's there
            # (In a real test we'd check against source_registry)
            
            canonical = canonicalize_url(source_url)
            if canonical in canonical_to_original:
                duplicates.append({
                    "url1": canonical_to_original[canonical],
                    "url2": source_url,
                    "canonical": canonical
                })
            else:
                canonical_to_original[canonical] = source_url

    print(f"Unique canonical URLs: {len(canonical_to_original)}")
    print(f"Duplicate canonical URLs detected: {len(duplicates)}")
    
    if duplicates:
        print("\nERROR: Duplicates found!")
        for d in duplicates:
            print(f"  Canonical: {d['canonical']}")
            print(f"    Orig 1: {d['url1']}")
            print(f"    Orig 2: {d['url2']}")
    else:
        print("\nSUCCESS: No duplicate canonical URLs found in the response cards.")

    # Check for multi-source evidence
    multi_source_cards = [c for c in cards if c.get("confidence") == "multi_source"]
    print(f"Cards with multi-source info: {len(multi_source_cards)}")
    if multi_source_cards:
        for c in multi_source_cards:
            publishers = [s['publisher'] for s in c['sources']]
            urls = [str(s['url']) for s in c['sources']]
            print(f"  - {c['headline'][:50]}... ({', '.join(publishers)})")
            for i, url in enumerate(urls):
                print(f"    S{i+1} [{publishers[i]}]: {url} -> Canonical: {canonicalize_url(url)}")

if __name__ == "__main__":
    main()
