"""
DOOM AI — Deep Warning System + Autopilot
Multi-model analysis, risk scoring, safer paths, schedules, and rules.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

# Model counts by plan for these modules
WARNING_COUNTS = {"free": 1, "basic": 1, "pro": 2, "pro_max": 3, "elite": 4}
AUTOPILOT_COUNTS = {"free": 1, "basic": 2, "pro": 3, "pro_max": 4, "elite": 5}

MODULE_STATE = {
    "autopilot": {
        "enabled": True,
        "cadence": "approved work continues",
        "schedules": [
            {"id": "morning-brief", "cron": "08:00", "action": "ops brief", "enabled": True},
            {"id": "day-close", "cron": "18:00", "action": "day close summary", "enabled": True},
            {"id": "weekly-content", "cron": "Mon 09:00", "action": "weekly content pack", "enabled": False},
        ],
    },
    "warning_system": {
        "enabled": True,
        "open_flags": 2,
        "flags": [
            {"id": "f1", "title": "Follow-up timing outside hours", "risk": "medium", "safer": "Schedule 10:00 IST tomorrow"},
            {"id": "f2", "title": "Landing conversion drop >10%", "risk": "high", "safer": "Propose copy change before next deploy"},
        ],
    },
}

class AnalyzeRequest(BaseModel):
    context: str
    plan: Optional[str] = "free"

class AutopilotRun(BaseModel):
    schedule_id: Optional[str] = None
    command: Optional[str] = None
    plan: Optional[str] = "free"

def get_models_for(module: str, plan: str) -> List[str]:
    plan = (plan or "free").lower()
    count = WARNING_COUNTS.get(plan, 1) if module == "warning" else AUTOPILOT_COUNTS.get(plan, 1)
    # Reuse existing pool selection then slice
    base = select_models(plan, "warning" if module == "warning" else "workflow")
    return base[:count] if base else ["openrouter/free"]

@router.get("/status")
async def modules_status():
    return MODULE_STATE

@router.post("/warning/analyze")
async def analyze_warning(req: AnalyzeRequest):
    models = get_models_for("warning", req.plan or "free")
    prompt = (
        f"Warning System analysis.\nContext: {req.context}\n"
        "Return: risk level (low/medium/high), reason, consequence, safer path, and whether to block."
    )
    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(f"[{m}]\n{ans}")
    combined = "\n\n---\n\n".join(answers)
    output = doom_wrap(combined, "warning")

    # Simple risk extraction for demo
    risk = "medium"
    if "high" in combined.lower():
        risk = "high"
    elif "low" in combined.lower():
        risk = "low"

    flag = {
        "id": f"f{len(MODULE_STATE['warning_system']['flags'])+1}",
        "title": req.context[:60],
        "risk": risk,
        "safer": "See analysis",
        "created": datetime.utcnow().isoformat(),
    }
    MODULE_STATE["warning_system"]["flags"].append(flag)
    MODULE_STATE["warning_system"]["open_flags"] = len(MODULE_STATE["warning_system"]["flags"])

    return {
        "status": "analyzed",
        "plan": req.plan or "free",
        "models_used": models,
        "model_count": len(models),
        "risk": risk,
        "output": output,
        "flag": flag,
    }

@router.post("/warning/acknowledge")
async def acknowledge_warning(flag_id: str):
    flags = MODULE_STATE["warning_system"]["flags"]
    MODULE_STATE["warning_system"]["flags"] = [f for f in flags if f["id"] != flag_id]
    MODULE_STATE["warning_system"]["open_flags"] = len(MODULE_STATE["warning_system"]["flags"])
    return {"acknowledged": flag_id, "open_flags": MODULE_STATE["warning_system"]["open_flags"]}

@router.post("/autopilot/toggle")
async def toggle_autopilot():
    MODULE_STATE["autopilot"]["enabled"] = not MODULE_STATE["autopilot"]["enabled"]
    return {"autopilot": MODULE_STATE["autopilot"]}

@router.post("/autopilot/run")
async def run_autopilot(req: AutopilotRun):
    if not MODULE_STATE["autopilot"]["enabled"]:
        raise HTTPException(400, "Autopilot is off")

    models = get_models_for("autopilot", req.plan or "free")
    target = req.command or "Run next scheduled approved work"
    if req.schedule_id:
        sched = next((s for s in MODULE_STATE["autopilot"]["schedules"] if s["id"] == req.schedule_id), None)
        if sched:
            target = sched["action"]

    prompt = f"Autopilot execution.\nTask: {target}\nPlan the exact steps and confirm they are approved-safe."
    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(f"[{m}]\n{ans}")
    combined = "\n\n---\n\n".join(answers)
    output = doom_wrap(combined, "workflow")

    return {
        "status": "executed",
        "plan": req.plan or "free",
        "models_used": models,
        "model_count": len(models),
        "target": target,
        "output": output,
    }

@router.get("/autopilot/schedules")
async def list_schedules():
    return {"schedules": MODULE_STATE["autopilot"]["schedules"]}
