"""
DOOM AI — HR Workspace
Attendance, leave, payroll checks, and 10+ HR tools.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

HR_TOOLS = [
    {"id": "attendance", "name": "Attendance Log"},
    {"id": "leave", "name": "Leave Request"},
    {"id": "payroll", "name": "Payroll Check"},
    {"id": "onboard", "name": "Onboarding Checklist"},
    {"id": "policy", "name": "Policy Lookup"},
    {"id": "performance", "name": "Performance Note"},
    {"id": "headcount", "name": "Headcount Report"},
    {"id": "compliance", "name": "Compliance Check"},
    {"id": "shift", "name": "Shift Planner"},
    {"id": "exit", "name": "Exit Interview"},
    {"id": "benefits", "name": "Benefits Query"},
    {"id": "announcement", "name": "Announcement Draft"},
]

ATTENDANCE = []

class AttendanceMark(BaseModel):
    email: str
    status: str = "present"  # present | remote | leave
    note: Optional[str] = None

class InviteRequest(BaseModel):
    emails: List[str]
    message: str
    invite_link: str = "http://localhost:8000/login"
    role: str = "member"
    set_by: str = "hr"

@router.post("/invite")
async def invite_employees(req: InviteRequest):
    """Send invite and set permissions."""
    from permissions import set_permission, PermissionSet
    results = []
    for email in req.emails:
        # Set permission on invite
        await set_permission(PermissionSet(email=email, role=req.role, set_by=req.set_by))
        results.append({"email": email, "role": req.role, "status": "invited"})

    from connectors import is_connected
    if not is_connected("gmail") and not is_connected("outlook"):
        return {
            "status": "queued",
            "note": "Gmail not connected. Permissions set. Connect Gmail to send emails.",
            "results": results,
        }

    return {"status": "sent", "count": len(results), "results": results}
    tool: str
    command: str
    plan: Optional[str] = "free"

@router.get("/tools")
async def list_tools():
    return {"tools": HR_TOOLS, "count": len(HR_TOOLS)}

@router.post("/attendance")
async def mark_attendance(req: AttendanceMark):
    entry = {
        "email": req.email,
        "status": req.status,
        "note": req.note,
        "time": datetime.utcnow().isoformat(),
    }
    ATTENDANCE.append(entry)
    return {"status": "marked", "entry": entry}

@router.get("/attendance")
async def get_attendance():
    return {"attendance": ATTENDANCE[-50:]}

@router.post("/run")
async def run_hr_tool(req: HRAction):
    tool = next((t for t in HR_TOOLS if t["id"] == req.tool), None)
    if not tool:
        raise HTTPException(404, "Tool not found")

    models = select_models(req.plan or "free", "team_space")
    prompt = f"HR tool: {tool['name']}\nCommand: {req.command}\nRecent attendance: {ATTENDANCE[-5:]}\nGive a precise HR action."

    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(f"[{m}]\n{ans}")

    combined = "\n\n---\n\n".join(answers) if len(answers) > 1 else answers[0]
    output = doom_wrap(combined, "team_space")

    return {
        "tool": req.tool,
        "status": "complete",
        "plan": req.plan or "free",
        "models_used": models,
        "model_count": len(models),
        "output": output,
    }
