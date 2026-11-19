"""
DOOM AI — Founder tools (expanded)
10 additional tools + schedule management.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

FOUNDER_TOOLS = [
    {"id": "decision", "name": "Decision Log"},
    {"id": "priority", "name": "Priority Stack"},
    {"id": "delegation", "name": "Delegation Map"},
    {"id": "risk-review", "name": "Risk Review"},
    {"id": "capital", "name": "Capital Allocation"},
    {"id": "hiring", "name": "Hiring Signal"},
    {"id": "board", "name": "Board Brief"},
    {"id": "okrs", "name": "OKR Check"},
    {"id": "reflection", "name": "Weekly Reflection"},
    {"id": "shutdown", "name": "Shutdown Ritual"},
    {"id": "brand-vision", "name": "Brand Vision"},
]

SCHEDULES = []

class FounderToolRun(BaseModel):
    tool: str
    command: str
    plan: Optional[str] = "free"
    password: str

class ScheduleItem(BaseModel):
    title: str
    time: str
    space: str = "founder"
    password: str

def check_pw(pw: str):
    from founder import FOUNDER_STATE
    if not FOUNDER_STATE.get("password_hash"):
        raise HTTPException(403, "Founder password not set")
    if pw != FOUNDER_STATE["password_hash"]:
        raise HTTPException(401, "Wrong founder password")

@router.get("/tools")
async def list_tools():
    return {"tools": FOUNDER_TOOLS, "count": len(FOUNDER_TOOLS)}

@router.post("/run")
async def run_tool(req: FounderToolRun):
    check_pw(req.password)
    tool = next((t for t in FOUNDER_TOOLS if t["id"] == req.tool), None)
    if not tool:
        raise HTTPException(404, "Tool not found")

    models = select_models(req.plan or "free", "workflow")[:5]
    prompt = f"Founder tool: {tool['name']}\nCommand: {req.command}\nGive a precise, commanding output."
    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(ans)
    combined = "\n\n---\n\n".join(answers)
    return {
        "tool": req.tool,
        "status": "complete",
        "model_count": len(models),
        "output": doom_wrap(combined, "workflow"),
    }

@router.post("/schedule")
async def add_schedule(req: ScheduleItem):
    check_pw(req.password)
    item = {
        "id": f"sch{len(SCHEDULES)+1}",
        "title": req.title,
        "time": req.time,
        "space": req.space,
        "created": datetime.utcnow().isoformat(),
    }
    SCHEDULES.append(item)
    return item

@router.get("/schedule")
async def list_schedule():
    return {"schedule": SCHEDULES}
