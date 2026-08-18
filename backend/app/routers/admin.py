from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..utils import user_store

router = APIRouter()

class SeedUser(BaseModel):
    name: str
    email: str
    phone: str | None = None

@router.post("/seed-user")
async def seed_user(u: SeedUser):
    try:
        user_store.create_user(u.name, u.email, u.phone)
    except ValueError:
        raise HTTPException(status_code=400, detail="User exists")
    return {"status": "seeded", "email": u.email}
