"""
DOOM AI — Company Workspace
Real seats, members, invites, roles.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()

# In-memory for now (swap to DB later)
WORKSPACES = {
    "web-shop": {
        "id": "web-shop",
        "name": "Web Shop",
        "owner": "yajat@webshop.local",
        "plan": "pro",
        "seats_total": 3,
        "seats_used": 1,
        "members": [
            {"email": "yajat@webshop.local", "role": "owner", "joined": "2026-01-01"},
        ],
        "invites": [],
    }
}

class InviteRequest(BaseModel):
    email: str
    role: str = "member"
    workspace_id: str = "web-shop"

class JoinRequest(BaseModel):
    token: str
    email: str

@router.get("/")
async def get_workspace(workspace_id: str = "web-shop"):
    ws = WORKSPACES.get(workspace_id)
    if not ws:
        raise HTTPException(404, "Workspace not found")
    return ws

@router.post("/invite")
async def invite_member(req: InviteRequest):
    ws = WORKSPACES.get(req.workspace_id)
    if not ws:
        raise HTTPException(404, "Workspace not found")
    if ws["seats_used"] >= ws["seats_total"]:
        raise HTTPException(400, "No seats left")
    token = f"inv_{req.email.replace('@','_')}_{int(datetime.utcnow().timestamp())}"
    ws["invites"].append({"email": req.email, "role": req.role, "token": token, "status": "pending"})
    return {"status": "invited", "token": token, "email": req.email}

@router.post("/join")
async def join_workspace(req: JoinRequest):
    for ws in WORKSPACES.values():
        for inv in ws["invites"]:
            if inv["token"] == req.token and inv["status"] == "pending":
                inv["status"] = "accepted"
                ws["members"].append({"email": req.email, "role": inv["role"], "joined": datetime.utcnow().isoformat()})
                ws["seats_used"] += 1
                return {"status": "joined", "workspace": ws["name"], "role": inv["role"]}
    raise HTTPException(400, "Invalid or expired invite")

@router.get("/members")
async def list_members(workspace_id: str = "web-shop"):
    ws = WORKSPACES.get(workspace_id)
    if not ws:
        raise HTTPException(404)
    return {"members": ws["members"], "seats": f"{ws['seats_used']}/{ws['seats_total']}"}
