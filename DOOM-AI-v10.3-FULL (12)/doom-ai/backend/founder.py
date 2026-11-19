"""
DOOM AI — Founder controls
Autopilot workflow from Founder Workflow, Roll Call, and Founder Password pages.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

FOUNDER_STATE = {
    "password_hash": None,  # set by founder
    "autopilot_workflow": {
        "daily": "09:00–11:00 deep work · 11:00 comms batch · 15:00 reviews",
        "when_away": "Continue approved briefs, content drafts, and follow-ups. No external sends without approval.",
        "last_set": None,
    },
    "roll_call": [],
}

class FounderPassword(BaseModel):
    password: str

class WorkflowSet(BaseModel):
    daily: str
    when_away: str
    plan: Optional[str] = "free"
    password: str

class RollCallRequest(BaseModel):
    note: str
    password: str

def check_password(pw: str):
    if not FOUNDER_STATE["password_hash"]:
        raise HTTPException(403, "Founder password not set")
    if pw != FOUNDER_STATE["password_hash"]:
        raise HTTPException(401, "Wrong founder password")

@router.post("/password/set")
async def set_password(req: FounderPassword):
    FOUNDER_STATE["password_hash"] = req.password
    return {"status": "password_set"}

@router.post("/autopilot/workflow")
async def set_autopilot_workflow(req: WorkflowSet):
    check_password(req.password)
    models = select_models(req.plan or "free", "workflow")[:5]  # cap at 5
    prompt = (
        f"Founder daily workflow: {req.daily}\n"
        f"When founder is away: {req.when_away}\n"
        "Summarize the exact Autopilot rules DOOM should follow."
    )
    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(f"[{m}]\n{ans}")
    combined = "\n\n---\n\n".join(answers)
    output = doom_wrap(combined, "workflow")

    FOUNDER_STATE["autopilot_workflow"] = {
        "daily": req.daily,
        "when_away": req.when_away,
        "last_set": datetime.utcnow().isoformat(),
        "rules": output,
    }
    return {
        "status": "workflow_set",
        "plan": req.plan or "free",
        "models_used": models,
        "model_count": len(models),
        "output": output,
    }

@router.get("/autopilot/workflow")
async def get_autopilot_workflow():
    return FOUNDER_STATE["autopilot_workflow"]

@router.post("/rollcall")
async def roll_call(req: RollCallRequest):
    check_password(req.password)
    entry = {
        "time": datetime.utcnow().isoformat(),
        "note": req.note,
    }
    FOUNDER_STATE["roll_call"].append(entry)
    return {"status": "logged", "entry": entry}

@router.get("/rollcall")
async def get_roll_call():
    return {"roll_call": FOUNDER_STATE["roll_call"][-20:]}
