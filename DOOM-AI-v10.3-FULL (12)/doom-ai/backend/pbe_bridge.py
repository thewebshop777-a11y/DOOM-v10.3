"""
DOOM AI — PBE Bridge
Thin proxy to PBE running on its own port.
No PBE code is copied into DOOM.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import httpx
import os

router = APIRouter()

PBE_URL = os.getenv("PBE_URL", "http://localhost:8001")

class ObserveRequest(BaseModel):
    service: str

class PlanRequest(BaseModel):
    goal: str
    context: Optional[dict] = None

async def proxy(method: str, path: str, json: dict = None, params: dict = None):
    url = f"{PBE_URL}{path}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            if method == "GET":
                r = await client.get(url, params=params)
            else:
                r = await client.post(url, json=json or {})
            if r.status_code >= 400:
                return {"error": r.text, "status": r.status_code}
            return r.json()
        except httpx.ConnectError:
            raise HTTPException(503, f"PBE not reachable at {PBE_URL}. Start PBE first.")
        except Exception as e:
            raise HTTPException(500, str(e))

@router.get("/health")
async def pbe_health():
    return await proxy("GET", "/health")

@router.get("/state")
async def pbe_state():
    return await proxy("GET", "/api/state")

@router.post("/observe")
async def observe(req: ObserveRequest):
    return await proxy("POST", "/api/observation/runs", {"service": req.service})

@router.post("/plan")
async def create_plan(req: PlanRequest):
    return await proxy("POST", "/api/pbe/plan", {"goal": req.goal, "context": req.context or {}})

@router.get("/plans")
async def list_plans():
    return await proxy("GET", "/api/pbe/plans")

@router.get("/history")
async def history():
    return await proxy("GET", "/api/pbe/history")

@router.post("/plans/{plan_id}/approve")
async def approve_plan(plan_id: str):
    return await proxy("POST", f"/api/pbe/plans/{plan_id}/approve")

@router.get("/connections")
async def connections():
    return await proxy("GET", "/api/connections/status")
