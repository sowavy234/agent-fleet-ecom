from typing import Optional
import os
import redis.asyncio as redis

_redis: Optional[redis.Redis] = None

def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
        _redis = redis.from_url(url, decode_responses=True)
    return _redis

async def close_redis():
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
