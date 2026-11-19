"""
DOOM AI — Billing and usage
Basic plan status and upgrade path.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from limits import PLAN_LIMITS, check_plan_limit

router = APIRouter()

@router.get("/plans")
async def list_plans():
    return {
        "plans": [
            {"id": "free", "name": "Free", "price": 0, "daily_calls": 20, "models": 1, "note": "14-day"},
            {"id": "basic", "name": "Basic", "price": 29, "daily_calls": 100, "models": 2},
            {"id": "pro", "name": "Pro", "price": 79, "daily_calls": 500, "models": 4},
            {"id": "pro_max", "name": "Pro Max", "price": 149, "daily_calls": 2000, "models": 7},
            {"id": "elite", "name": "Elite", "price": 299, "daily_calls": 10000, "models": 10},
        ]
    }

@router.get("/usage")
async def get_usage(plan: str = "pro", workspace_id: str = "web-shop"):
    allowed, used, cap = check_plan_limit(plan, workspace_id)
    return {
        "plan": plan,
        "used_today": used,
        "daily_cap": cap,
        "remaining": max(0, cap - used),
        "allowed": allowed,
    }

class UpgradeRequest(BaseModel):
    plan: str
    workspace_id: str = "web-shop"

@router.post("/upgrade")
async def upgrade(req: UpgradeRequest):
    # Placeholder — real payment later
    return {
        "status": "upgrade_requested",
        "plan": req.plan,
        "note": "Payment integration pending. Plan flag can be set manually for now.",
    }
