from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from ..utils import user_store

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None

class SetPassword(BaseModel):
    email: str
    password: str

@router.post("/create")
async def create_user(u: UserCreate):
    try:
        user_store.create_user(u.name, u.email, u.phone)
    except ValueError:
        raise HTTPException(status_code=400, detail="User exists")
    return {"status": "pending_password", "email": u.email}

@router.post("/set-password")
async def set_password(payload: SetPassword):
    user = user_store.get_user(payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    pwd_hash = pwd_context.hash(payload.password)
    user_store.set_password_hash(payload.email, pwd_hash)
    return {"status": "ok"}

@router.post("/login")
async def login(payload: SetPassword):
    user = user_store.get_user(payload.email)
    if not user or user.get('password_hash') is None:
        raise HTTPException(status_code=400, detail="Invalid credentials or password not set")
    if not pwd_context.verify(payload.password, user.get('password_hash')):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    # Return a simple token for scaffold (not JWT)
    return {"access_token": "scaffold-token", "token_type": "bearer"}
