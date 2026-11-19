"""
DOOM AI — Finance Workspace
10 tools for financial operations.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

FINANCE_TOOLS = [
    {"id": "cashflow", "name": "Cash Flow Forecast"},
    {"id": "invoice", "name": "Invoice Tracker"},
    {"id": "expense", "name": "Expense Audit"},
    {"id": "budget", "name": "Budget vs Actual"},
    {"id": "runway", "name": "Runway Calculator"},
    {"id": "tax", "name": "Tax Reserve"},
    {"id": "vendor-pay", "name": "Vendor Payments"},
    {"id": "margin", "name": "Margin Analysis"},
    {"id": "forecast", "name": "Revenue Forecast"},
    {"id": "alert", "name": "Finance Alert"},
]

class FinanceRun(BaseModel):
    tool: str
    command: str
    plan: Optional[str] = "free"

@router.get("/tools")
async def list_tools():
    return {"tools": FINANCE_TOOLS, "count": len(FINANCE_TOOLS)}

@router.post("/run")
async def run_tool(req: FinanceRun):
    tool = next((t for t in FINANCE_TOOLS if t["id"] == req.tool), None)
    if not tool:
        raise HTTPException(404, "Tool not found")
    models = select_models(req.plan or "free", "analysis")
    prompt = f"Finance tool: {tool['name']}\nCommand: {req.command}\nGive precise numbers and actions."
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
