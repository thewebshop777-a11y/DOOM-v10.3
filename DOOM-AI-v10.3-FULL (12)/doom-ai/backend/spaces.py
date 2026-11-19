"""
DOOM AI — Team Spaces with expanded tool sets
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from router import select_models, doom_wrap
from openrouter import call_model

router = APIRouter()

SPACE_TOOLS = {
    "engineering": [
        {"id": "code-review", "name": "Code Review"},
        {"id": "architecture", "name": "Architecture Diagram"},
        {"id": "api-design", "name": "API Design"},
        {"id": "bug-analysis", "name": "Bug Analysis"},
        {"id": "deploy-plan", "name": "Deployment Plan"},
        {"id": "refactor", "name": "Refactor Suggestion"},
        {"id": "test-gen", "name": "Test Generation"},
        {"id": "security-scan", "name": "Security Scan"},
        {"id": "perf-audit", "name": "Performance Audit"},
        {"id": "docs", "name": "Docs Generator"},
    ],
    "marketing": [
        {"id": "campaign", "name": "Campaign Planner"},
        {"id": "ad-copy", "name": "Ad Copy"},
        {"id": "social-calendar", "name": "Social Calendar"},
        {"id": "seo-audit", "name": "SEO Audit"},
        {"id": "email-seq", "name": "Email Sequence"},
        {"id": "audience", "name": "Audience Analysis"},
        {"id": "competitor", "name": "Competitor Scan"},
        {"id": "content-angle", "name": "Content Angle"},
        {"id": "hashtag", "name": "Hashtag Research"},
        {"id": "funnel", "name": "Funnel Design"},
    ],
    "product": [
        {"id": "roadmap", "name": "Roadmap Builder"},
        {"id": "user-story", "name": "User Story"},
        {"id": "feature-spec", "name": "Feature Spec"},
        {"id": "prioritize", "name": "Prioritization"},
        {"id": "feedback", "name": "Feedback Synthesis"},
        {"id": "persona", "name": "Persona Update"},
        {"id": "journey", "name": "User Journey"},
        {"id": "metric", "name": "Success Metric"},
        {"id": "release-note", "name": "Release Notes"},
        {"id": "experiment", "name": "Experiment Design"},
    ],
    "operations": [
        {"id": "brief", "name": "Ops Brief"},
        {"id": "triage", "name": "Alert Triage"},
        {"id": "followup", "name": "Follow-up Draft"},
        {"id": "calendar", "name": "Calendar Optimize"},
        {"id": "vendor", "name": "Vendor Check"},
        {"id": "sla", "name": "SLA Monitor"},
        {"id": "report", "name": "Status Report"},
        {"id": "handoff", "name": "Handoff Note"},
        {"id": "risk", "name": "Risk Flag"},
        {"id": "digest", "name": "Daily Digest"},
    ],
}

SPACES = {
    "engineering": {"name": "Engineering", "open_prs": 2, "failed_ci": 0, "deploy": "healthy"},
    "product": {"name": "Product", "active_tasks": 4, "blocked": 1, "roadmap": "Q4"},
    "marketing": {"name": "Marketing", "scheduled": 1, "published_today": 0, "views_30d": 113},
    "operations": {"name": "Operations", "alerts": 3, "approvals": 2, "cadence": "live"},
}

class SpaceAction(BaseModel):
    command: str
    tool: Optional[str] = None
    plan: Optional[str] = "free"

@router.get("/")
async def list_spaces():
    return SPACES

@router.get("/{space_id}/tools")
async def list_tools(space_id: str):
    tools = SPACE_TOOLS.get(space_id, [])
    return {"space": space_id, "tools": tools, "count": len(tools)}

@router.post("/{space_id}/run")
async def run_space_action(space_id: str, req: SpaceAction):
    if space_id not in SPACES:
        return {"error": "Space not found"}

    models = select_models(req.plan or "free", "team_space")
    tool_note = f"Tool: {req.tool}\n" if req.tool else ""
    prompt = f"Team Space: {space_id}\n{tool_note}Command: {req.command}\nCurrent state: {SPACES[space_id]}\nGive a precise action plan."

    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(f"[{m}]\n{ans}")

    combined = "\n\n---\n\n".join(answers) if len(answers) > 1 else answers[0]
    output = doom_wrap(combined, "team_space")

    return {
        "space": space_id,
        "tool": req.tool,
        "status": "complete",
        "plan": req.plan or "free",
        "models_used": models,
        "model_count": len(models),
        "output": output,
    }
