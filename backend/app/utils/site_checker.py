import re
from urllib.parse import urlparse, urljoin
import httpx
from pathlib import Path
import json
from typing import Dict, Any, Set
import asyncio

from .whois_ssl import get_ssl_info, get_whois
from ..clients.trustpilot_client import query_trustpilot_by_domain

BLACKLIST = [
    "easysign",
    "easy sign",
    "wholesale",
    "zaza",
    "zaza distribution",
]

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FILE = DATA_DIR / "site_reports.json"

CRAWL_PAGE_LIMIT = 20
CRAWL_TIMEOUT = 8.0


def _load_reports() -> Dict[str, Any]:
    if not REPORT_FILE.exists():
        return {}
    try:
        return json.loads(REPORT_FILE.read_text())
    except Exception:
        return {}


def _save_reports(data: Dict[str, Any]):
    REPORT_FILE.write_text(json.dumps(data, indent=2))


def _domain_from_url(url: str) -> str:
    p = urlparse(url)
    return p.netloc.lower()


def is_blacklisted_domain(domain: str) -> bool:
    for item in BLACKLIST:
        if item in domain:
            return True
    return False


def extract_contact_candidates(text: str):
    # simple email and phone regexes
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phones = re.findall(r"(?:\+?\d{1,3}[\s-])?(?:\(\d{3}\)|\d{3})[\s-]?\d{3}[\s-]?\d{4}", text)
    return list(set(emails)), list(set(phones))


async def _crawl_count_pages(start_url: str, timeout: float = CRAWL_TIMEOUT, limit: int = CRAWL_PAGE_LIMIT) -> int:
    """Shallow BFS crawl within same domain to estimate page count."""
    domain = _domain_from_url(start_url)
    seen: Set[str] = set()
    q = [start_url]
    idx = 0
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers={"User-Agent":"agent-fleet-bot/1.0"}) as client:
        while idx < len(q) and len(seen) < limit:
            url = q[idx]
            idx += 1
            if url in seen:
                continue
            try:
                r = await client.get(url)
                seen.add(url)
                text = r.text
                # find links
                for m in re.findall(r'href=["\']([^"\']+)["\']', text, re.IGNORECASE):
                    # build absolute
                    try:
                        absu = urljoin(url, m)
                    except Exception:
                        continue
                    if _domain_from_url(absu) == domain and absu not in seen and absu not in q:
                        q.append(absu)
                        if len(seen) + len(q) >= limit:
                            break
            except Exception:
                continue
    return len(seen)


async def analyze_site(url: str, timeout: float = 10.0) -> Dict[str, Any]:
    domain = _domain_from_url(url)
    report: Dict[str, Any] = {
        "url": url,
        "domain": domain,
        "blacklisted": is_blacklisted_domain(domain),
        "reachable": False,
        "status_code": None,
        "has_ssl": url.startswith("https://"),
        "contact_emails": [],
        "contact_phones": [],
        "trustpilot": {},
        "whois": {},
        "ssl": {},
        "page_count_estimate": 0,
        "notes": [],
    }

    # initial fetch
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers={"User-Agent":"agent-fleet-bot/1.0"}) as client:
            r = await client.get(url)
            report["reachable"] = True
            report["status_code"] = r.status_code
            content = r.text
            lower = content.lower()
            # look for trustpilot mention
            if "trustpilot" in lower:
                report["trustpilot"]["mention_in_site"] = True
            emails, phones = extract_contact_candidates(content)
            report["contact_emails"] = emails
            report["contact_phones"] = phones
            # heuristic: if few pages and short content, suspicious
            if len(content) < 800:
                report["notes"].append("very small page content; suspicious")
            # blacklist words in body
            for b in BLACKLIST:
                if b in lower:
                    report["notes"].append(f"blacklist keyword present in body: {b}")
    except httpx.HTTPStatusError as e:
        report["status_code"] = e.response.status_code
        report["notes"].append(f"http error: {e}")
    except Exception as e:
        report["notes"].append(f"fetch error: {e}")

    # in parallel: whois, ssl, trustpilot search, page count
    async def _whois():
        try:
            return get_whois(domain)
        except Exception as e:
            return {"error": str(e)}

    async def _ssl():
        try:
            return get_ssl_info(domain)
        except Exception as e:
            return {"error": str(e)}

    async def _tp():
        try:
            return await query_trustpilot_by_domain(domain)
        except Exception as e:
            return {"error": str(e)}

    async def _pages():
        try:
            return await _crawl_count_pages(url)
        except Exception:
            return 0

    whois_task = asyncio.create_task(_whois())
    ssl_task = asyncio.create_task(_ssl())
    tp_task = asyncio.create_task(_tp())
    pages_task = asyncio.create_task(_pages())

    report["whois"] = await whois_task
    report["ssl"] = await ssl_task
    report["trustpilot"] = await tp_task
    report["page_count_estimate"] = await pages_task

    # final heuristic score
    score = 100
    if report["blacklisted"]:
        score -= 60
    if not report["reachable"]:
        score -= 50
    if not report["contact_emails"] and not report["contact_phones"]:
        score -= 20
    if report["trustpilot"] and report["trustpilot"].get("found"):
        score += 10
    # penalize very short lived domains
    try:
        cd = report["whois"].get("creation_date")
        if cd:
            score -= 0
    except Exception:
        pass

    report["trust_score"] = max(0, min(100, score))

    # persist report
    data = _load_reports()
    data[url] = report
    _save_reports(data)
    return report
