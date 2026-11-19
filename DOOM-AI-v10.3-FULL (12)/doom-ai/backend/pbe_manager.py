"""
DOOM AI — PBE process manager
Starts and stops PBE from DOOM.
"""
import os
import subprocess
import signal
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()

PBE_DIR = Path(os.getenv("PBE_DIR", "../PBE-v5.2.4"))
PBE_PORT = int(os.getenv("PBE_PORT", "8001"))
_process = None

def is_running() -> bool:
    global _process
    if _process and _process.poll() is None:
        return True
    return False

@router.get("/status")
async def status():
    return {
        "running": is_running(),
        "port": PBE_PORT,
        "dir": str(PBE_DIR),
    }

@router.post("/start")
async def start_pbe():
    global _process
    if is_running():
        return {"status": "already_running", "port": PBE_PORT}

    pbe_path = PBE_DIR.resolve()
    if not pbe_path.exists():
        raise HTTPException(404, f"PBE directory not found: {pbe_path}")

    # Try start-pbe.bat on Windows, or python -m on others
    bat = pbe_path / "start-pbe.bat"
    if bat.exists() and os.name == "nt":
        _process = subprocess.Popen(
            ["cmd", "/c", str(bat)],
            cwd=str(pbe_path),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
        )
    else:
        _process = subprocess.Popen(
            ["python", "-m", "uvicorn", "pbe.main:app", "--host", "0.0.0.0", "--port", str(PBE_PORT)],
            cwd=str(pbe_path),
        )
    return {"status": "started", "port": PBE_PORT, "pid": _process.pid}

@router.post("/stop")
async def stop_pbe():
    global _process
    if not is_running():
        return {"status": "not_running"}
    _process.terminate()
    try:
        _process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _process.kill()
    _process = None
    return {"status": "stopped"}
