import httpx
import re
from typing import Dict, Any

TP_SEARCH = "https://www.trustpilot.com/search?query={}"

async def query_trustpilot_by_domain(domain: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Try to find Trustpilot references for the domain. This is a best-effort adapter.

    Returns a dict with found(bool), rating (if parsed), reviews_sample (list of short excerpts).
    If Trustpilot API key is provided later, this adapter can be swapped.
    """
    out = {"found": False, "rating": None, "reviews_sample": []}
    try:
        url = TP_SEARCH.format(domain)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers={"User-Agent":"agent-fleet-bot/1.0"}) as client:
            r = await client.get(url)
            text = r.text
            # Trustpilot markup often includes "star-rating" or "review-count" keywords
            if "trustpilot" in text.lower():
                out["found"] = True
            # Attempt to extract a rating like "4.5" near "stars" words
            m = re.search(r"([0-5]\.?[0-9]?)\s+star", text, re.IGNORECASE)
            if m:
                out["rating"] = m.group(1)
            # extract short review snippets (naive)
            snippets = re.findall(r">([^<>]{30,200})<", text)
            for s in snippets[:3]:
                out["reviews_sample"].append(re.sub(r"\s+", " ", s).strip())
    except Exception as e:
        out["error"] = str(e)
    return out
