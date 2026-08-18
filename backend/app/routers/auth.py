from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from passlib.context import CryptContext
from ..utils import user_store
from jose import jwt
from datetime import datetime, timedelta
import os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class UserCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None

class SetPassword(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

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

@router.post("/login", response_model=Token)
async def login(payload: SetPassword):
    user = user_store.get_user(payload.email)
    if not user or user.get('password_hash') is None:
        raise HTTPException(status_code=400, detail="Invalid credentials or password not set")
    if not pwd_context.verify(payload.password, user.get('password_hash')):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": payload.email, "exp": expire}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

# Dependency example to get current user from token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = user_store.get_user(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
