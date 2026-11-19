"""
DOOM AI — Powers
Uses router to decide how many models to call based on plan + task weight.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

class PowerCommand(BaseModel):
    command: str
    plan: Optional[str] = "free"
    context: Optional[dict] = None

async def run_power(power: str, cmd: PowerCommand) -> dict:
    models = select_models(cmd.plan or "free", power)
    prompt = f"Power: {power}\nCommand: {cmd.command}\nGive a precise, actionable answer."

    answers: List[str] = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(f"[{m}]\n{ans}")

    if len(models) == 1:
        combined = answers[0]
    else:
        combined = f"Council of {len(models)} models:\n\n" + "\n\n---\n\n".join(answers)

    wrapped = doom_wrap(combined, power)
    return {
        "power": power,
        "status": "complete",
        "plan": cmd.plan or "free",
        "models_used": models,
        "model_count": len(models),
        "output": wrapped,
    }

@router.post("/business/execute")
async def business_execute(cmd: PowerCommand):
    return await run_power("business", cmd)

@router.post("/website/execute")
async def website_execute(cmd: PowerCommand):
    return await run_power("website", cmd)

@router.post("/content/execute")
async def content_execute(cmd: PowerCommand):
    return await run_power("content", cmd)

@router.post("/workflow/execute")
async def workflow_execute(cmd: PowerCommand):
    return await run_power("workflow", cmd)

@router.post("/predictor/run")
async def predictor_run(cmd: PowerCommand):
    return await run_power("predictor", cmd)
