"""
DOOM AI — Memory and Tool Re-engineering
Learns how to rebuild connected tools.
Saves to DOOM memory file.
Pulls PBE learnings when available.
Skips social platforms.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
import os
from pathlib import Path
from router import select_models, doom_wrap
from openrouter import call_model
from main import SessionLocal
from sqlalchemy import text

router = APIRouter()

MEMORY_PATH = Path(os.getenv("DOOM_MEMORY_PATH", "./doom_memory.json"))

# Tools DOOM will never re-engineer
EXCLUDED = {"youtube", "instagram", "facebook", "linkedin"}

# Tools that exist in DOOM but not in PBE (still learned by DOOM)
DOOM_ONLY = {"canva", "figma", "mixpanel", "amplitude", "zoho-desk", "zoho-books"}

class LearnRequest(BaseModel):
    connector_id: str
    plan: Optional[str] = "free"

class ApplyRequest(BaseModel):
    connector_id: str
    plan: Optional[str] = "free"

def load_memory() -> dict:
    if MEMORY_PATH.exists():
        try:
            return json.loads(MEMORY_PATH.read_text())
        except Exception:
            return {"tools": {}, "pbe": {}, "updated": None}
    return {"tools": {}, "pbe": {}, "updated": None}

def save_memory(mem: dict):
    mem["updated"] = datetime.utcnow().isoformat()
    MEMORY_PATH.write_text(json.dumps(mem, indent=2))

def is_connected(connector_id: str, workspace_id: str = "web-shop") -> bool:
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT 1 FROM connected_accounts WHERE workspace_id = :ws AND connector_id = :cid AND status = 'connected'"),
            {"ws": workspace_id, "cid": connector_id},
        ).fetchone()
        return bool(row)
    finally:
        db.close()

@router.get("/")
async def get_memory():
    return load_memory()

@router.post("/learn")
async def learn_tool(req: LearnRequest):
    cid = req.connector_id.lower()
    if cid in EXCLUDED:
        raise HTTPException(400, f"{cid} is excluded from re-engineering")

    if not is_connected(cid):
        raise HTTPException(403, f"{cid} is not connected and authenticated")

    models = select_models(req.plan or "free", "engineering")
    prompt = (
        f"Tool: {cid}\n"
        "Describe how to re-engineer this tool inside DOOM so the SaaS can be replaced. "
        "List core features, data model, and a minimal internal workflow. Be precise."
    )

    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(ans)

    learning = {
        "connector_id": cid,
        "learned_at": datetime.utcnow().isoformat(),
        "models_used": models,
        "summary": "\n\n---\n\n".join(answers),
        "source": "doom",
    }

    mem = load_memory()
    mem["tools"][cid] = learning
    save_memory(mem)

    return {
        "status": "learned",
        "connector": cid,
        "model_count": len(models),
        "output": doom_wrap(learning["summary"], "engineering"),
    }

@router.post("/learn/pbe")
async def learn_from_pbe():
    """Pull PBE learnings into DOOM memory (only if PBE is reachable)."""
    try:
        import httpx
        from main import settings
        pbe_url = getattr(settings, "pbe_url", None) or os.getenv("PBE_URL", "http://localhost:8001")
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(f"{pbe_url}/api/pbe/history")
            if r.status_code != 200:
                raise HTTPException(503, "PBE history not available")
            pbe_data = r.json()
    except Exception as e:
        raise HTTPException(503, f"PBE not reachable: {e}")

    mem = load_memory()
    mem["pbe"] = {
        "pulled_at": datetime.utcnow().isoformat(),
        "data": pbe_data,
    }
    save_memory(mem)
    return {"status": "pbe_learnings_saved", "count": len(pbe_data) if isinstance(pbe_data, list) else 1}

@router.post("/apply")
async def apply_learning(req: ApplyRequest):
    """Apply a learned tool into the DOOM workspace."""
    cid = req.connector_id.lower()
    mem = load_memory()
    learning = mem["tools"].get(cid)
    if not learning:
        raise HTTPException(404, "No learning found for this tool. Run /learn first.")

    models = select_models(req.plan or "free", "workflow")
    prompt = (
        f"Apply this tool learning inside DOOM workspace.\n"
        f"Tool: {cid}\n"
        f"Learning:\n{learning['summary']}\n"
        "Return a concrete workspace change (new view, workflow step, or internal module)."
    )
    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(ans)

    applied = {
        "connector_id": cid,
        "applied_at": datetime.utcnow().isoformat(),
        "change": "\n\n---\n\n".join(answers),
    }
    mem.setdefault("applied", {})[cid] = applied
    save_memory(mem)

    return {
        "status": "applied",
        "connector": cid,
        "output": doom_wrap(applied["change"], "workflow"),
    }

@router.get("/applied")
async def list_applied():
    mem = load_memory()
    return {"applied": mem.get("applied", {})}
