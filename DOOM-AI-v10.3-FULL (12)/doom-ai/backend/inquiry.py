"""
DOOM AI — Inquiry Desk (light task → 1 model)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from main import settings
from router import select_models, doom_wrap
from openrouter import call_model
from limits import check_plan_limit, check_free_trial, log_usage

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class InquiryRequest(BaseModel):
    messages: List[Message]
    plan: Optional[str] = "free"
    temperature: float = 0.7

class InquiryResponse(BaseModel):
    reply: str
    model_used: str
    tokens: Optional[int] = None

@router.post("/chat", response_model=InquiryResponse)
async def chat(req: InquiryRequest):
    plan = req.plan or "free"
    if plan == "free":
        allowed, days_left, expired = check_free_trial()
        if expired:
            raise HTTPException(402, "Free 14-day trial ended. Upgrade to continue.")

    models = select_models(plan, "inquiry")
    model = models[0]
    last = req.messages[-1].content if req.messages else ""

    if not settings.openrouter_api_key or settings.openrouter_api_key.startswith("sk-or-v1-your"):
        demo = f"Inquiry Desk (demo · plan={plan} · model={model})\n\nReceived: \"{last}\"\n\nAdd OPENROUTER_API_KEY to backend/.env for real routing."
        return InquiryResponse(reply=doom_wrap(demo, "inquiry"), model_used=model, tokens=None)

    raw = await call_model(model, last, req.temperature)
    log_usage(plan, "inquiry", 1)
    return InquiryResponse(
        reply=doom_wrap(raw, "inquiry"),
        model_used=model,
        tokens=None,
    )
