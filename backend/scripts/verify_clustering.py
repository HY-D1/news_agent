
import requests
import json
from typing import List, Dict, Any

def main():
    url = "http://localhost:8000/digest"
    # Using regions with high overlap potential
    payload = {
        "topics": ["tech", "finance", "daily"],
        "range": "48h",
        "regions": ["usa", "uk", "canada"],
        "max_cards": 30
    }
    
    print(f"Step 1: Calling {url}...")
    try:
        response = requests.post(url, json=payload, timeout=45)
        response.raise_for_status()
    except Exception as e:
        print(f"FAILED: Could not reach backend at {url}")
        print(f"Error: {e}")
        print("\nPlease ensure the backend is running (e.g., `uvicorn app.main:app --reload`) and try again.")
        return

    data = response.json()
    cards = data.get("cards", [])
    
    if not cards:
        print("WARNING: No cards returned. RSS feeds might be empty or unreachable.")
        return

    # Metrics
    total_cards = len(cards)
    multi_source_cards = [c for c in cards if c.get("confidence") == "multi_source"]
    single_source_cards = [c for c in cards if c.get("confidence") == "single_source"]
    
    total_sources = sum(len(c.get("sources", [])) for c in cards)
    avg_sources = total_sources / total_cards if total_cards > 0 else 0
    
    print("\n" + "="*40)
    print("STAGE 3: CLUSTERING VERIFICATION")
    print("="*40)
    print(f"Total Cards:        {total_cards}")
    print(f"MULTI_SOURCE Cards: {len(multi_source_cards)}")
    print(f"SINGLE_SOURCE Cards:{len(single_source_cards)}")
    print(f"Avg Sources/Card:   {avg_sources:.2f}")
    print("="*40)
    
    if multi_source_cards:
        print("\nExample Multi-Source Clusters:")
        for i, card in enumerate(multi_source_cards[:3]):
            print(f"\n{i+1}. Headline: {card['headline']}")
            print(f"   Sources ({len(card['sources'])}):")
            for src in card["sources"]:
                print(f"     - [{src['publisher']}] {src.get('url')}")
    else:
        print("\nNo multi-source clusters found in this run.")
        print("Note: This is normal if there are no overlapping stories in the last 48h.")

if __name__ == "__main__":
    main()
