import json
import sys


def compare_digests(file_tech, file_finance):
    try:
        with open(file_tech) as f:
            tech_data = json.load(f)
        with open(file_finance) as f:
            finance_data = json.load(f)
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    tech_cards = tech_data.get("cards", [])
    finance_cards = finance_data.get("cards", [])

    tech_urls = {
        str(source["url"]) for card in tech_cards for source in (card.get("sources") or [])
    }
    finance_urls = {
        str(source["url"]) for card in finance_cards for source in (card.get("sources") or [])
    }

    tech_headlines = {card['headline'] for card in tech_cards}
    finance_headlines = {card['headline'] for card in finance_cards}

    overlap_urls = tech_urls.intersection(finance_urls)
    overlap_headlines = tech_headlines.intersection(finance_headlines)

    print("--- Stage 1 Verification Report ---")
    print(f"Tech Digest: {len(tech_cards)} cards, {len(tech_urls)} unique URLs")
    print(f"Finance Digest: {len(finance_cards)} cards, {len(finance_urls)} unique URLs")
    print(f"URL Overlap Count: {len(overlap_urls)}")
    print(f"Headline Overlap Count: {len(overlap_headlines)}")

    if len(tech_cards) > 0 and len(finance_cards) > 0:
        if len(overlap_urls) / max(len(tech_urls), 1) < 0.2:
            print("SUCCESS: Low overlap detected between Tech and Finance.")
        else:
            print("WARNING: High overlap detected. Topic filtering might be weak.")
    else:
        print(
            "NOTICE: One or both digests are empty. "
            "Check if server is running and feeds are reachable."
        )

    # Citation check
    for digest_name, cards in [("Tech", tech_cards), ("Finance", finance_cards)]:
        missing_citations = []
        for card in cards:
            if not card.get('sources') or not card.get('bullets'):
                missing_citations.append(card['id'])
            for bullet in card.get('bullets', []):
                if not bullet.get('citations'):
                    missing_citations.append(f"{card['id']} (bullet)")

        if missing_citations:
            print(
                f"FAIL: {digest_name} digest has cards/bullets missing citations: "
                f"{missing_citations}"
            )
        else:
            print(f"PASS: {digest_name} digest has valid citations for all cards and bullets.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 verify_stage1.py tech_digest.json finance_digest.json")
    else:
        compare_digests(sys.argv[1], sys.argv[2])
