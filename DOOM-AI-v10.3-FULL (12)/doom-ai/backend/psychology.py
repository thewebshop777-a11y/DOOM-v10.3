"""
DOOM AI — Business Psychology Workspace
10 tools for founder and team psychology.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

PSYCH_TOOLS = [
    {"id": "bias", "name": "Bias Check"},
    {"id": "decision-fatigue", "name": "Decision Fatigue"},
    {"id": "motivation", "name": "Motivation Map"},
    {"id": "conflict", "name": "Conflict Pattern"},
    {"id": "trust", "name": "Trust Signal"},
    {"id": "energy", "name": "Energy Audit"},
    {"id": "narrative", "name": "Narrative Audit"},
    {"id": "stakeholder", "name": "Stakeholder Psychology"},
    {"id": "resilience", "name": "Resilience Score"},
    {"id": "alignment", "name": "Team Alignment"},
]

class PsychRun(BaseModel):
    tool: str
    command: str
    plan: Optional[str] = "free"

@router.get("/tools")
async def list_tools():
    return {"tools": PSYCH_TOOLS, "count": len(PSYCH_TOOLS)}

@router.post("/run")
async def run_tool(req: PsychRun):
    tool = next((t for t in PSYCH_TOOLS if t["id"] == req.tool), None)
    if not tool:
        raise HTTPException(404, "Tool not found")
    models = select_models(req.plan or "free", "analysis")
    prompt = f"Business psychology tool: {tool['name']}\nCommand: {req.command}\nGive a clear psychological insight and action."
    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(ans)
    combined = "\n\n---\n\n".join(answers)
    return {
        "tool": req.tool,
        "status": "complete",
        "model_count": len(models),
        "output": doom_wrap(combined, "business"),
    }
