from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None

class SetPassword(BaseModel):
    email: str
    password: str

# In-memory store for scaffold/demo. Replace with DB-backed store.
_USERS = {}

@router.post("/create")
async def create_user(u: UserCreate):
    if u.email in _USERS:
        raise HTTPException(status_code=400, detail="User exists")
    _USERS[u.email] = {"name": u.name, "email": u.email, "phone": u.phone, "password_hash": None}
    return {"status": "pending_password", "email": u.email}

@router.post("/set-password")
async def set_password(payload: SetPassword):
    user = _USERS.get(payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user['password_hash'] = pwd_context.hash(payload.password)
    return {"status": "ok"}

@router.post("/login")
async def login(payload: SetPassword):
    user = _USERS.get(payload.email)
    if not user or user['password_hash'] is None:
        raise HTTPException(status_code=400, detail="Invalid credentials or password not set")
    if not pwd_context.verify(payload.password, user['password_hash']):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    # Return a simple token for scaffold (not JWT)
    return {"access_token": "scaffold-token", "token_type": "bearer"}
