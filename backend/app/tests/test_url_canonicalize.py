from app.pipeline.verify.url_canonicalize import canonicalize_url


def test_canonicalize_removes_utm_params():
    url = "https://example.com/a?utm_source=x&utm_medium=y&id=1"
    expected = "https://example.com/a?id=1"
    assert canonicalize_url(url) == expected

def test_canonicalize_removes_fragment():
    url = "https://example.com/a#section"
    expected = "https://example.com/a"
    assert canonicalize_url(url) == expected

def test_canonicalize_sorts_query_params():
    url = "https://example.com/a?b=2&a=1"
    expected = "https://example.com/a?a=1&b=2"
    assert canonicalize_url(url) == expected

def test_canonicalize_removes_tracking_ids():
    url = "https://example.com/a?gclid=xyz&fbclid=abc&real=true"
    expected = "https://example.com/a?real=true"
    assert canonicalize_url(url) == expected

def test_canonicalize_preserves_meaningful_params():
    url = "https://example.com/article?id=1&name=test"
    expected = "https://example.com/article?id=1&name=test"
    assert canonicalize_url(url) == expected

def test_canonicalize_edge_cases():
    # Path is kept unchanged if empty by current implementation
    assert canonicalize_url("https://example.com") == "https://example.com"
    # Only utm params
    assert canonicalize_url("https://example.com/a?utm_source=x") == "https://example.com/a"
