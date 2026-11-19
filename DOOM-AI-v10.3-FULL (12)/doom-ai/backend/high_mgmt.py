"""
DOOM AI — High Management Workspace
10 tools for senior leadership.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

HIGH_TOOLS = [
    {"id": "strategy", "name": "Strategy Review"},
    {"id": "capital-alloc", "name": "Capital Allocation"},
    {"id": "board-prep", "name": "Board Prep"},
    {"id": "ma", "name": "M&A Signal"},
    {"id": "risk-portfolio", "name": "Risk Portfolio"},
    {"id": "succession", "name": "Succession Map"},
    {"id": "culture", "name": "Culture Audit"},
    {"id": "investor", "name": "Investor Narrative"},
    {"id": "scenario", "name": "Scenario Planning"},
    {"id": "mandate", "name": "Mandate Check"},
]

class HighRun(BaseModel):
    tool: str
    command: str
    plan: Optional[str] = "free"

@router.get("/tools")
async def list_tools():
    return {"tools": HIGH_TOOLS, "count": len(HIGH_TOOLS)}

@router.post("/run")
async def run_tool(req: HighRun):
    tool = next((t for t in HIGH_TOOLS if t["id"] == req.tool), None)
    if not tool:
        raise HTTPException(404, "Tool not found")
    models = select_models(req.plan or "free", "analysis")
    prompt = f"High management tool: {tool['name']}\nCommand: {req.command}\nGive a strategic, precise output."
    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(ans)
    combined = "\n\n---\n\n".join(answers)
    return {"tool": req.tool, "status": "complete", "model_count": len(models), "output": doom_wrap(combined, "business")}
