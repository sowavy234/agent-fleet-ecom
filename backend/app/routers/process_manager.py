import os
import asyncio
import time
from fastapi import APIRouter, HTTPException, Request, Depends
from ..routers.auth import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")
# Run uvicorn from the backend package directory using module path app.main:app so imports resolve
UVICORN_CMD = [
    "python3",
    "-m",
    "uvicorn",
    "app.main:app",
    "--reload",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
]
# log path under backend/data
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "uvicorn_server.log"))

_process = None
_process_lock = asyncio.Lock()
_process_info = {}

class AuthPayload(BaseModel):
    password: str

class StartPayload(AuthPayload):
    cmd: Optional[list] = None

async def _write_stream(reader, path):
    with open(path, "ab") as f:
        while True:
            line = await reader.readline()
            if not line:
                break
            f.write(line)
            f.flush()

async def _spawn_uvicorn(cmd):
    global _process, _process_info
    stdout = asyncio.subprocess.PIPE
    stderr = asyncio.subprocess.PIPE
    # set working directory to backend package dir so app module path `app.main:app` resolves
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    backend_dir = os.path.join(repo_root, 'backend')
    env = os.environ.copy()
    # prepend backend_dir to PYTHONPATH to make app importable
    prev_pythonpath = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = backend_dir + (os.pathsep + prev_pythonpath if prev_pythonpath else '')
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=stdout, stderr=stderr, cwd=backend_dir, env=env)
    _process = proc
    _process_info = {
        "pid": proc.pid,
        "started_at": time.time(),
        "cmd": cmd,
        "cwd": backend_dir,
    }
    # start background tasks to capture logs
    loop = asyncio.get_event_loop()
    log_path = os.path.abspath(LOG_PATH)
    # ensure directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    loop.create_task(_write_stream(proc.stdout, log_path))
    loop.create_task(_write_stream(proc.stderr, log_path))
    return proc

async def _stop_uvicorn():
    global _process, _process_info
    if _process is None:
        return False
    try:
        _process.terminate()
        await asyncio.wait_for(_process.wait(), timeout=10)
    except Exception:
        try:
            _process.kill()
        except Exception:
            pass
    _process = None
    _process_info["stopped_at"] = time.time()
    return True

def _check_password(pw: str) -> bool:
    return pw == ADMIN_PASSWORD

def _port_in_use(host: str, port: int) -> Optional[int]:
    """Return PID if host:port is in use, otherwise None."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect((host, port))
        s.close()
        # find pid via lsof
        try:
            import subprocess
            out = subprocess.check_output(["lsof", "-i", f"{host}:{port}", "-Pn", "-sTCP:LISTEN"]).decode().strip().splitlines()
            if len(out) >= 2:
                # parse PID from second line
                parts = out[1].split()
                pid = int(parts[1])
                return pid
        except Exception:
            return -1
    except Exception:
        return None

@router.post("/start")
async def start_server(payload: StartPayload, user=Depends(get_current_user)):
    """Start a uvicorn subprocess. Requires authenticated admin user. Optionally provide a custom cmd list."""
    async with _process_lock:
        # if our managed process is running, honor it
        if _process is not None and _process.returncode is None:
            return {"started": False, "reason": "already_running", "pid": _process.pid}
        # check if the desired host:port is already occupied by any process
        host = '127.0.0.1'
        port = 8000
        try:
            # attempt to parse from a provided cmd
            cmd = payload.cmd if payload.cmd else UVICORN_CMD
            if isinstance(cmd, list) and ' --port' in ' '.join(cmd):
                # naive parse fallback; prefer default
                pass
        except Exception:
            pass
        pid = _port_in_use(host, port)
        if pid is not None:
            return {"started": False, "reason": "port_in_use", "pid": pid}
        cmd = payload.cmd if payload.cmd else UVICORN_CMD
        proc = await _spawn_uvicorn(cmd)
        return {"started": True, "pid": proc.pid}

@router.post("/stop")
async def stop_server(payload: AuthPayload, user=Depends(get_current_user)):
    async with _process_lock:
        if _process is None:
            return {"stopped": False, "reason": "not_running"}
        ok = await _stop_uvicorn()
        return {"stopped": ok}

@router.get("/status")
async def status(user=Depends(get_current_user)):
    global _process, _process_info
    if _process is None:
        return {"running": False}
    # check if still alive
    rc = _process.returncode
    running = rc is None
    info = {
        "running": running,
        "pid": _process.pid,
        "started_at": _process_info.get("started_at"),
        "cmd": _process_info.get("cmd"),
    }
    return info

@router.get("/logs")
async def logs(tail: int = 500):
    # return last `tail` bytes of log file
    try:
        path = os.path.abspath(LOG_PATH)
        if not os.path.exists(path):
            return {"logs": ""}
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            to_read = min(size, tail * 1024)
            f.seek(max(0, size - to_read))
            data = f.read().decode(errors="replace")
        return {"logs": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
