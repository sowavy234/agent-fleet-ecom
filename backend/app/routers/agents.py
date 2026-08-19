from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ..utils import site_checker
from ..tasks import enqueue_url
from ..tasks_redis import enqueue_url_redis
from ..redis_client import get_redis
import time

router = APIRouter()

class SitePayload(BaseModel):
    url: str

# Simple in-memory rate limiter fallback; prefer Redis-based limiter when available
_rate_limit_store = {}
RATE_LIMIT_PER_MIN = 30


def _check_rate_limit_redis(ip: str) -> bool:
    try:
        r = get_redis()
        key = f"rl:{ip}:{int(time.time())//60}"
        # INCR and set TTL
        val = r.incr(key)
        if val == 1:
            r.expire(key, 65)
        return int(val) <= RATE_LIMIT_PER_MIN
    except Exception:
        return _check_rate_limit_inmem(ip)


def _check_rate_limit_inmem(ip: str) -> bool:
    now = int(time.time())
    window = now // 60
    entry = _rate_limit_store.get(ip)
    if not entry or entry.get("window") != window:
        _rate_limit_store[ip] = {"window": window, "count": 1}
        return True
    if entry["count"] >= RATE_LIMIT_PER_MIN:
        return False
    entry["count"] += 1
    return True


async def _check_rate_limit(ip: str) -> bool:
    # async-aware wrapper that prefers Redis-backed limiter
    try:
        r = get_redis()
        key = f"rl:{ip}:{int(time.time())//60}"
        val = await r.incr(key)
        if int(val) == 1:
            await r.expire(key, 65)
        return int(val) <= RATE_LIMIT_PER_MIN
    except Exception:
        return _check_rate_limit_inmem(ip)

@router.post("/check-site")
async def check_site(p: SitePayload, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not await _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    if not p.url:
        raise HTTPException(status_code=400, detail="url required")
    report = await site_checker.analyze_site(p.url)
    return report

@router.post("/enqueue-check")
async def enqueue_check(p: SitePayload, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not await _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    # attempt Redis enqueue first
    try:
        job_id = await enqueue_url_redis(p.url, metadata={"requested_by": client_ip})
        return {"enqueued": True, "job_id": job_id}
    except Exception:
        # fallback to in-process queue
        ok = enqueue_url(p.url)
        if not ok:
            raise HTTPException(status_code=503, detail="queue full")
        return {"enqueued": True}

@router.get("/reports")
async def list_reports():
    data = site_checker._load_reports()
    return data

@router.get("/report")
async def get_report(url: str):
    data = site_checker._load_reports()
    return data.get(url, {})

@router.get("/jobs")
async def list_jobs():
    try:
        r = get_redis()
        # scan for job keys
        keys = await r.keys("job:*")
        jobs = []
        for k in keys:
            jobs.append(await r.hgetall(k))
        return jobs
    except Exception:
        raise HTTPException(status_code=503, detail="redis unavailable")

@router.get("/job")
async def get_job(job_id: str):
    try:
        r = get_redis()
        job = await r.hgetall(f"job:{job_id}")
        return job
    except Exception:
        raise HTTPException(status_code=503, detail="redis unavailable")
