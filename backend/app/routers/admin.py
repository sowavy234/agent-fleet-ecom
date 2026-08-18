from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter()

class SeedUser(BaseModel):
    name: str
    email: str
    phone: str | None = None

@router.post("/seed-user")
async def seed_user(u: SeedUser):
    # For scaffold: call auth.create_user endpoint or import _USERS
    from .auth import _USERS
    _USERS[u.email] = {"name": u.name, "email": u.email, "phone": u.phone, "password_hash": None}
    return {"status": "seeded", "email": u.email}
