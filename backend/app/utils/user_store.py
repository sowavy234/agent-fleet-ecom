import json
from pathlib import Path
from typing import Dict, Any, Optional

STORE_DIR = Path(__file__).resolve().parents[2] / "data"
STORE_DIR.mkdir(parents=True, exist_ok=True)
STORE_FILE = STORE_DIR / "users.json"

def _load() -> Dict[str, Any]:
    if not STORE_FILE.exists():
        return {}
    try:
        return json.loads(STORE_FILE.read_text())
    except Exception:
        return {}

def _save(data: Dict[str, Any]):
    STORE_FILE.write_text(json.dumps(data, indent=2))

def get_user(email: str) -> Optional[Dict[str, Any]]:
    data = _load()
    return data.get(email)

def create_user(name: str, email: str, phone: str | None = None):
    data = _load()
    if email in data:
        raise ValueError("user exists")
    data[email] = {"name": name, "email": email, "phone": phone, "password_hash": None}
    _save(data)
    return data[email]

def set_password_hash(email: str, password_hash: str):
    data = _load()
    if email not in data:
        raise ValueError("user not found")
    data[email]["password_hash"] = password_hash
    _save(data)

def list_users() -> Dict[str, Any]:
    return _load()
