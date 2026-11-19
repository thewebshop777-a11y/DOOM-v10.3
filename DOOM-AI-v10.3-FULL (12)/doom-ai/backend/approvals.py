"""
DOOM AI — Approval Cards
Queue of actions that need human approval before execution.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()

APPROVALS = [
    {
        "id": "appr-1",
        "title": "Content · LinkedIn post #42",
        "detail": "Own your stack angle",
        "risk": "medium",
        "status": "pending",
        "created": "2026-11-15T09:15:00",
    },
    {
        "id": "appr-2",
        "title": "Business · Convin follow-up",
        "detail": "HubSpot email",
        "risk": "medium",
        "status": "pending",
        "created": "2026-11-15T09:41:00",
    },
]

class ApprovalDecision(BaseModel):
    decision: str  # approve | reject
    note: Optional[str] = None

@router.get("/")
async def list_approvals():
    pending = [a for a in APPROVALS if a["status"] == "pending"]
    return {"approvals": pending, "count": len(pending)}

@router.post("/{approval_id}/decide")
async def decide_approval(approval_id: str, req: ApprovalDecision):
    for a in APPROVALS:
        if a["id"] == approval_id:
            a["status"] = req.decision
            a["decided_at"] = datetime.utcnow().isoformat()
            a["note"] = req.note
            return {"status": "updated", "approval": a}
    raise HTTPException(404, "Approval not found")

@router.post("/")
async def create_approval(title: str, detail: str, risk: str = "low"):
    appr = {
        "id": f"appr-{len(APPROVALS)+1}",
        "title": title,
        "detail": detail,
        "risk": risk,
        "status": "pending",
        "created": datetime.utcnow().isoformat(),
    }
    APPROVALS.append(appr)
    return {"status": "created", "approval": appr}
