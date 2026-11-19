"""
DOOM AI — AI Employees
Roster, create, modify, analyse. Each employee can run tasks via OpenRouter.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

EMPLOYEES = [
    {
        "id": "ops-officer",
        "name": "Ops Officer",
        "function": "Briefs & follow-ups",
        "connectors": ["notion", "slack"],
        "workflow": "business_day",
        "status": "active",
    },
    {
        "id": "content-lead",
        "name": "Content Lead",
        "function": "Drafts & calendars",
        "connectors": ["linkedin", "canva"],
        "workflow": "content",
        "status": "active",
    },
]

class EmployeeCreate(BaseModel):
    name: str
    function: str
    connectors: List[str] = []
    workflow: str = "general"

class EmployeeTask(BaseModel):
    command: str
    plan: Optional[str] = "free"

@router.get("/")
async def list_employees():
    return {"employees": EMPLOYEES, "count": len(EMPLOYEES)}

@router.post("/")
async def create_employee(req: EmployeeCreate):
    emp_id = req.name.lower().replace(" ", "-")
    emp = {
        "id": emp_id,
        "name": req.name,
        "function": req.function,
        "connectors": req.connectors,
        "workflow": req.workflow,
        "status": "active",
    }
    EMPLOYEES.append(emp)
    return {"status": "created", "employee": emp}

@router.post("/{emp_id}/run")
async def run_employee_task(emp_id: str, req: EmployeeTask):
    emp = next((e for e in EMPLOYEES if e["id"] == emp_id), None)
    if not emp:
        raise HTTPException(404, "Employee not found")

    models = select_models(req.plan or "free", "ai_employees")
    prompt = (
        f"AI Employee: {emp['name']}\n"
        f"Function: {emp['function']}\n"
        f"Command: {req.command}\n"
        f"Give a precise, actionable response in DOOM style."
    )

    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(f"[{m}]\n{ans}")

    combined = "\n\n---\n\n".join(answers) if len(answers) > 1 else answers[0]
    output = doom_wrap(combined, "ai_employees")

    return {
        "employee": emp["name"],
        "status": "complete",
        "plan": req.plan or "free",
        "models_used": models,
        "model_count": len(models),
        "output": output,
    }
