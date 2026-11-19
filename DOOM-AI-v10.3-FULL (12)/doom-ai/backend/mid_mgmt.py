"""
DOOM AI — Middle Management Workspace
10 tools for team leads and managers.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

MID_TOOLS = [
    {"id": "sprint", "name": "Sprint Planning"},
    {"id": "one-on-one", "name": "1:1 Prep"},
    {"id": "blocker", "name": "Blocker Removal"},
    {"id": "capacity", "name": "Capacity Check"},
    {"id": "handoff", "name": "Handoff Note"},
    {"id": "kpi", "name": "KPI Review"},
    {"id": "escalation", "name": "Escalation Path"},
    {"id": "coaching", "name": "Coaching Note"},
    {"id": "priority", "name": "Priority Align"},
    {"id": "retro", "name": "Retro Summary"},
]

class MidRun(BaseModel):
    tool: str
    command: str
    plan: Optional[str] = "free"

@router.get("/tools")
async def list_tools():
    return {"tools": MID_TOOLS, "count": len(MID_TOOLS)}

@router.post("/run")
async def run_tool(req: MidRun):
    tool = next((t for t in MID_TOOLS if t["id"] == req.tool), None)
    if not tool:
        raise HTTPException(404, "Tool not found")
    models = select_models(req.plan or "free", "medium")
    prompt = f"Middle management tool: {tool['name']}\nCommand: {req.command}\nGive a clear, actionable output."
    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(ans)
    combined = "\n\n---\n\n".join(answers)
    return {"tool": req.tool, "status": "complete", "model_count": len(models), "output": doom_wrap(combined, "business")}
