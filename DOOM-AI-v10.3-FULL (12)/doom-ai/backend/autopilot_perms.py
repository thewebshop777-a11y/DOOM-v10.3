"""
DOOM AI — Autopilot permissions
45+ permissions. Select all or manual.
Sends emails according to role.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

AUTOPILOT_PERMISSIONS = [
    "send_founder_brief", "send_team_digest", "send_approval_reminder",
    "send_blocker_alert", "send_content_ready", "send_deploy_notice",
    "send_finance_alert", "send_hr_attendance", "send_risk_flag",
    "run_ops_brief", "run_content_draft", "run_predictor_30d",
    "run_website_check", "run_engineering_scan", "run_marketing_calendar",
    "triage_slack", "triage_email", "update_notion",
    "create_followup", "schedule_meeting", "post_linkedin_draft",
    "check_vercel", "check_github_prs", "check_hubspot",
    "generate_report", "generate_ppt_outline", "product_review_note",
    "competitor_scan", "share_market_note", "health_forecast",
    "invite_reminder", "permission_audit", "roll_call_prompt",
    "autopilot_workflow_check", "memory_learn_trigger", "pbe_sync",
    "warning_acknowledge", "approval_escalate", "day_close_summary",
    "weekly_pack", "monthly_review", "okrs_check",
    "brand_vision_refresh", "capital_note", "hiring_signal",
    "culture_pulse", "succession_check",
    "prompt_builder_access",  # always recommended on
    "ai_employees_access",    # founder choice — recommended off
]

SELECTED = set()

class SelectRequest(BaseModel):
    permissions: List[str]
    select_all: bool = False
    set_by: str = "founder"

@router.get("/list")
async def list_permissions():
    return {"permissions": AUTOPILOT_PERMISSIONS, "count": len(AUTOPILOT_PERMISSIONS), "selected": list(SELECTED)}

@router.post("/select")
async def select_permissions(req: SelectRequest):
    global SELECTED
    if req.select_all:
        SELECTED = set(AUTOPILOT_PERMISSIONS)
    else:
        SELECTED = set(req.permissions)
    return {"status": "updated", "selected_count": len(SELECTED), "selected": list(SELECTED)}

@router.post("/run")
async def run_autopilot_with_permissions(plan: str = "free"):
    """Runs selected autopilot actions and prepares emails by role."""
    if not SELECTED:
        raise HTTPException(400, "No permissions selected")

    emails = []
    for perm in SELECTED:
        if perm.startswith("send_"):
            emails.append({
                "permission": perm,
                "to": "founder" if "founder" in perm else "team",
                "subject": perm.replace("_", " ").title(),
                "body": f"Autopilot action: {perm}",
                "time": datetime.utcnow().isoformat(),
            })

    return {
        "status": "executed",
        "permissions_run": len(SELECTED),
        "emails_prepared": len(emails),
        "emails": emails[:10],
        "note": "Emails sent via connected Gmail when authenticated.",
    }
