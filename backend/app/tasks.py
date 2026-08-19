import asyncio
import time
from typing import Any
from fastapi import FastAPI
from .utils.site_checker import analyze_site

QUEUE_CONCURRENCY = 2
QUEUE_MAXSIZE = 100

queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=QUEUE_MAXSIZE)

async def worker_loop(app: FastAPI):
    """Background worker that consumes enqueue requests and runs analyze_site.

    Reports are persisted by analyze_site itself.
    """
    sem = asyncio.Semaphore(QUEUE_CONCURRENCY)
    while True:
        item = await queue.get()
        url, submitted_at = item.get("url"), item.get("submitted_at")
        try:
            async with sem:
                # run analyze (already persists)
                await analyze_site(url)
        except Exception:
            pass
        finally:
            queue.task_done()


def setup_background_tasks(app: FastAPI):
    loop = asyncio.get_event_loop()
    # start a few workers
    for _ in range(QUEUE_CONCURRENCY):
        loop.create_task(worker_loop(app))


def enqueue_url(url: str):
    try:
        queue.put_nowait({"url": url, "submitted_at": time.time()})
        return True
    except asyncio.QueueFull:
        return False
