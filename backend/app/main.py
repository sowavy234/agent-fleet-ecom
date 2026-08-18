from fastapi import FastAPI
from .routers import health, auth, admin

def create_app():
    app = FastAPI(title="Agent Fleet Ecom API")
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/auth")
    app.include_router(admin.router, prefix="/admin")
    return app

app = create_app()

