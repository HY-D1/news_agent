from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def canonicalize_url(url: str) -> str:
    """
    Normalizes a URL for deduplication purposes.

    Rules:
    - Strip fragment
    - Lowercase scheme and netloc
    - Remove default ports (:80, :443)
    - Remove tracking query parameters (utm_*, gclid, etc.)
    - Sort remaining query parameters
    - Keep path unchanged
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return url

    # 1. Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # 2. Remove default ports
    if ":" in netloc:
        host, port = netloc.rsplit(":", 1)
        if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
            netloc = host

    # 3. Handle query parameters
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    filtered_params = []

    tracking_params = {
        "gclid",
        "fbclid",
        "mc_cid",
        "mc_eid",
        "igshid",
        "ref",
        "ref_src",
        "spm",
        "cmpid",
    }

    for key, value in query_params:
        key_lower = key.lower()
        if key_lower.startswith("utm_") or key_lower in tracking_params:
            continue
        filtered_params.append((key, value))

    # 4. Sort query parameters by key then value
    filtered_params.sort()

    # 5. Reconstruct URL
    new_query = urlencode(filtered_params)

    return urlunparse(
        (
            scheme,
            netloc,
            parsed.path,
            parsed.params,
            new_query,
            "",  # Strip fragment
        )
    )
