"""
DOOM AI — Power tools
Choosable tools inside each power window.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

POWER_TOOLS = {
    "business": [
        {"id": "product-review", "name": "Product Review"},
        {"id": "reports", "name": "Reports"},
        {"id": "ppt", "name": "PPT"},
        {"id": "ops-overview", "name": "Operation Overview"},
    ],
    "website": [
        {"id": "site-url", "name": "Site URL Analysis"},
        {"id": "ui-analyze", "name": "Site UI Analyze"},
        {"id": "site-analytics", "name": "Site Analytics"},
    ],
    "content": [
        {"id": "content-analytics", "name": "Content Analytics"},
    ],
    "predictor": [
        {"id": "competitor", "name": "Competitor Prediction"},
        {"id": "share-market", "name": "Share Market Prediction"},
        {"id": "30-day", "name": "Current 30-Day Prediction"},
        {"id": "health-future", "name": "Current Health → Future"},
    ],
}

class PowerToolRun(BaseModel):
    power: str
    tool: str
    command: str
    plan: Optional[str] = "free"
    extra: Optional[dict] = None

@router.get("/{power}/tools")
async def list_tools(power: str):
    tools = POWER_TOOLS.get(power, [])
    return {"power": power, "tools": tools, "count": len(tools)}

@router.post("/run")
async def run_power_tool(req: PowerToolRun):
    tools = POWER_TOOLS.get(req.power, [])
    tool = next((t for t in tools if t["id"] == req.tool), None)
    if not tool:
        raise HTTPException(404, "Tool not found in this power")

    models = select_models(req.plan or "free", "analysis" if req.power == "predictor" else "medium")
    prompt = (
        f"Power: {req.power}\n"
        f"Tool: {tool['name']}\n"
        f"Command: {req.command}\n"
        f"Extra: {req.extra or {}}\n"
        "Answer strictly in the style and format of this tool."
    )
    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(ans)
    combined = "\n\n---\n\n".join(answers)
    return {
        "power": req.power,
        "tool": req.tool,
        "status": "complete",
        "model_count": len(models),
        "output": doom_wrap(combined, req.power),
    }
