"""
DOOM AI — Automations
Real flow: AI (1–2 models) decides → Composio executes on connected tool → DOOM wrap.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from router import select_models, doom_wrap
from openrouter import call_model
from connectors import CONNECTORS
import httpx
from main import settings

router = APIRouter()

class AutomationRequest(BaseModel):
    command: str
    connector_id: str
    action: str
    params: Optional[dict] = None
    plan: Optional[str] = "free"

class AutomationResponse(BaseModel):
    status: str
    plan: str
    models_used: List[str]
    connector: str
    action: str
    ai_decision: str
    tool_result: dict
    output: str

async def execute_composio(connector_id: str, action: str, params: dict) -> dict:
    conn = next((c for c in CONNECTORS if c["id"] == connector_id), None)
    if not conn:
        return {"error": "Connector not found"}

    if not settings.composio_api_key or settings.composio_api_key == "your-composio-key":
        return {
            "status": "demo",
            "result": f"[demo] Executed {action} on {conn['name']} with {params}",
        }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.composio_base}/actions/execute",
            headers={"x-api-key": settings.composio_api_key},
            json={
                "appName": conn["composio_app"],
                "actionName": action,
                "params": params or {},
            },
        )
        if resp.status_code != 200:
            return {"status": "error", "detail": resp.text}
        return {"status": "executed", "result": resp.json()}

from limits import check_plan_limit, log_usage
from approvals import APPROVALS
from datetime import datetime

@router.post("/run", response_model=AutomationResponse)
async def run_automation(req: AutomationRequest):
    # Hard plan limit
    allowed, used, cap = check_plan_limit(req.plan or "free")
    if not allowed:
        raise HTTPException(429, f"Plan limit reached ({used}/{cap} daily calls)")

    # Approval gate — create pending approval and stop
    approval_id = f"appr-auto-{int(datetime.utcnow().timestamp())}"
    APPROVALS.append({
        "id": approval_id,
        "title": f"Automation · {req.connector_id} · {req.action}",
        "detail": req.command,
        "risk": "medium",
        "status": "pending",
        "created": datetime.utcnow().isoformat(),
        "payload": req.model_dump(),
    })

    return AutomationResponse(
        status="pending_approval",
        plan=req.plan or "free",
        models_used=[],
        connector=req.connector_id,
        action=req.action,
        ai_decision="Waiting for approval",
        tool_result={"approval_id": approval_id},
        output=doom_wrap(f"Action queued for approval.\nID: {approval_id}\nApprove in Approval Cards to execute.", "workflow"),
    )
