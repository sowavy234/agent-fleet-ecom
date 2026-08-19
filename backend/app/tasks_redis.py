import asyncio
import uuid
import time
from typing import Dict, Any
from .redis_client import get_redis
from .utils.site_checker import analyze_site

QUEUE_KEY = "site_queue"
JOB_PREFIX = "job:"

WORKER_COUNT = 2

async def enqueue_url_redis(url: str, metadata: Dict[str, Any] | None = None) -> str:
    r = get_redis()
    job_id = str(uuid.uuid4())
    job_key = JOB_PREFIX + job_id
    job = {
        "id": job_id,
        "url": url,
        "status": "queued",
        "created_at": str(time.time()),
    }
    if metadata:
        job.update({k: str(v) for k, v in metadata.items()})
    await r.hset(job_key, mapping=job)
    await r.lpush(QUEUE_KEY, job_id)
    return job_id

async def worker_runner():
    r = get_redis()
    while True:
        # BRPOP returns [key, value] or None on timeout
        try:
            item = await r.brpop(QUEUE_KEY, timeout=5)
        except Exception:
            await asyncio.sleep(1)
            continue
        if not item:
            await asyncio.sleep(0.1)
            continue
        _, job_id = item
        job_key = JOB_PREFIX + job_id
        await r.hset(job_key, mapping={"status": "running", "started_at": str(time.time())})
        job = await r.hgetall(job_key)
        url = job.get("url")
        try:
            # run analyze (persists to file as well)
            result = await analyze_site(url)
            # store result summary in job
            await r.hset(job_key, mapping={"status": "done", "finished_at": str(time.time()), "trust_score": str(result.get("trust_score", ""))})
        except Exception as e:
            await r.hset(job_key, mapping={"status": "failed", "error": str(e), "finished_at": str(time.time())})

async def start_workers(loop: asyncio.AbstractEventLoop):
    # spawn worker tasks
    for _ in range(WORKER_COUNT):
        loop.create_task(worker_runner())
