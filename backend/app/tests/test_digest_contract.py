from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_digest_contract_smoke():
    res = client.post("/digest", json={"topics": ["tech"], "range": "24h", "regions": ["canada"]})
    assert res.status_code == 200
    data = res.json()

    assert data["schema_version"] == "v1"
    assert "generated_at" in data
    assert data["qa_status"] in ["pass", "fail", "fallback"]
    assert isinstance(data["cards"], list)
    assert len(data["cards"]) >= 1

    # Hard trust rule: every bullet has >= 1 citation
    for card in data["cards"]:
        for bullet in card["bullets"]:
            assert len(bullet["citations"]) >= 1


def test_digest_rejects_empty_topics():
    res = client.post("/digest", json={"topics": [], "range": "24h", "regions": ["canada"]})
    assert res.status_code == 422
