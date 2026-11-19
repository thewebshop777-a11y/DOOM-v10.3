"""
DOOM AI — Permission system
Role-based access. Founder and HR control what each employee can see.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

router = APIRouter()

# Default permission templates
ROLE_TEMPLATES: Dict[str, List[str]] = {
    "founder": ["*"],
    "hr": [
        "dashboard", "inquiry", "hr", "workspace", "settings",
        "connectors", "prompt_builder",
    ],
    "marketing": [
        "dashboard", "inquiry", "marketing", "content", "designer",
        "media", "connectors", "prompt_builder",
    ],
    "engineering": [
        "dashboard", "inquiry", "eng", "website", "connectors",
        "workflowpage", "prompt_builder",
    ],
    "product": [
        "dashboard", "inquiry", "product", "predictor", "connectors",
        "prompt_builder",
    ],
    "operations": [
        "dashboard", "inquiry", "ops", "automations", "connectors",
        "warning", "prompt_builder",
    ],
    "finance": [
        "dashboard", "inquiry", "finance", "analytics", "connectors",
        "prompt_builder",
    ],
    "mid_management": [
        "dashboard", "inquiry", "mid", "ops", "product", "connectors",
        "prompt_builder",
    ],
    "high_management": [
        "dashboard", "inquiry", "high", "finance", "analytics",
        "workspace", "connectors", "prompt_builder",
    ],
    "member": [
        "dashboard", "inquiry", "prompt_builder",
    ],
}

# Restricted — never given by default
RESTRICTED = {"founder", "settings", "core", "modules", "customization", "employees"}

# Founder can explicitly grant "employees" if desired (not recommended)
RECOMMENDED_OFF = {"employees"}

# In-memory store (swap to SQLite later)
PERMISSIONS: Dict[str, dict] = {}

class PermissionSet(BaseModel):
    email: str
    role: str = "member"
    allowed: Optional[List[str]] = None
    set_by: str = "founder"

class PermissionUpdate(BaseModel):
    email: str
    allowed: List[str]
    set_by: str

def get_allowed(email: str) -> List[str]:
    rec = PERMISSIONS.get(email)
    if not rec:
        return ROLE_TEMPLATES["member"]
    return rec.get("allowed", ROLE_TEMPLATES["member"])

def can_access(email: str, view: str) -> bool:
    allowed = get_allowed(email)
    if "*" in allowed:
        return True
    if view in RESTRICTED and view not in allowed:
        return False
    return view in allowed

@router.get("/templates")
async def list_templates():
    return {"templates": ROLE_TEMPLATES, "restricted": list(RESTRICTED)}

@router.post("/set")
async def set_permission(req: PermissionSet):
    allowed = req.allowed or ROLE_TEMPLATES.get(req.role, ROLE_TEMPLATES["member"])
    # Never auto-grant restricted unless explicitly listed
    if req.role != "founder":
        allowed = [a for a in allowed if a not in RESTRICTED or a in (req.allowed or [])]
    PERMISSIONS[req.email] = {
        "email": req.email,
        "role": req.role,
        "allowed": allowed,
        "set_by": req.set_by,
        "updated": datetime.utcnow().isoformat(),
    }
    return PERMISSIONS[req.email]

@router.post("/update")
async def update_permission(req: PermissionUpdate):
    if req.email not in PERMISSIONS:
        raise HTTPException(404, "Employee not found")
    PERMISSIONS[req.email]["allowed"] = req.allowed
    PERMISSIONS[req.email]["set_by"] = req.set_by
    PERMISSIONS[req.email]["updated"] = datetime.utcnow().isoformat()
    return PERMISSIONS[req.email]

@router.get("/{email}")
async def get_permission(email: str):
    if email not in PERMISSIONS:
        return {"email": email, "role": "member", "allowed": ROLE_TEMPLATES["member"]}
    return PERMISSIONS[email]

@router.get("/")
async def list_permissions():
    return {"permissions": list(PERMISSIONS.values())}

@router.get("/check/{email}/{view}")
async def check_access(email: str, view: str):
    return {"email": email, "view": view, "allowed": can_access(email, view)}
