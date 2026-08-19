from fastapi import FastAPI
from .routers import health, auth, admin, agents, process_manager

# prefer Redis-backed workers when available
from .tasks import setup_background_tasks
from .tasks_redis import start_workers as start_redis_workers
from .redis_client import get_redis, close_redis


def create_app():
    app = FastAPI(title="Agent Fleet Ecom API")
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/auth")
    app.include_router(admin.router, prefix="/admin")
    app.include_router(agents.router, prefix="/agents")
    # server process manager (start/stop/status/logs) under /admin/server
    app.include_router(process_manager.router, prefix="/admin/server")

    @app.on_event("startup")
    async def _startup():
        # try to connect to Redis; if available, start Redis workers, else fallback
        try:
            r = get_redis()
            # ensure connection
            await r.ping()
            loop = app.state._loop if hasattr(app.state, '_loop') else None
            # FastAPI/uvicorn provides event loop — use asyncio.get_event_loop inside start
            import asyncio
            loop = asyncio.get_event_loop()
            await start_redis_workers(loop)
        except Exception:
            # fallback to local asyncio queue workers
            setup_background_tasks(app)

    @app.on_event("shutdown")
    async def _shutdown():
        try:
            await close_redis()
        except Exception:
            pass

    return app

app = create_app()

