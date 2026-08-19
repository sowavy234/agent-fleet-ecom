"""Simple Oolama local adapter.
Tries common local Oolama HTTP endpoints. Designed for NO-API-key local usage where the user runs oolama serve locally.
"""
from typing import Optional
import os
import httpx

OOLAMA_URL = os.environ.get("OOLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("OOLAMA_MODEL", "mpt-7b-instruct")
TIMEOUT = 30.0


def generate(prompt: str, model: Optional[str] = None, max_tokens: int = 200) -> dict:
    """Try to call local Oolama HTTP endpoints and return JSON result or error."""
    mdl = model or DEFAULT_MODEL
    client = httpx.Client(timeout=TIMEOUT)
    payloads = [
        {"model": mdl, "prompt": prompt, "max_tokens": max_tokens},
        {"model": mdl, "input": prompt, "max_new_tokens": max_tokens},
    ]
    endpoints = ["/v1/generate", "/v1/completions", "/generate", "/completions"]
    last_err = None
    for ep in endpoints:
        url = OOLAMA_URL.rstrip("/") + ep
        for payload in payloads:
            try:
                r = client.post(url, json=payload)
                if r.status_code == 200:
                    try:
                        return {"ok": True, "endpoint": url, "result": r.json()}
                    except Exception:
                        return {"ok": True, "endpoint": url, "text": r.text}
                else:
                    last_err = {"endpoint": url, "status_code": r.status_code, "text": r.text}
            except httpx.RequestError as e:
                last_err = {"endpoint": url, "error": str(e)}
    return {"ok": False, "error": "no endpoint responded", "last": last_err}
