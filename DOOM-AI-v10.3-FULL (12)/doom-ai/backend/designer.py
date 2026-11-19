"""
DOOM AI — Designer Workspace
10+ AI editing and design tools.
Model count by plan: Free 1, Basic 1, Pro 2, Pro Max 3, Elite 4.
Pixabay for free stock assets.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
from router import select_models, doom_wrap
from openrouter import call_model
from main import settings

router = APIRouter()

# Design-specific model pools (best for visual work)
DESIGN_POOLS = {
    "free": ["openrouter/free"],
    "basic": ["google/gemini-3.8-flash"],
    "pro": ["google/gemini-3.8-flash", "openai/gpt-6.1-terra"],
    "pro_max": ["google/gemini-omni-1.2-flash", "openai/gpt-image-2.6-sunburst", "google/gemini-4-argon"],
    "elite": ["openai/gpt-image-2.6-sunburst", "google/gemini-omni-1.2-flash", "google/gemini-4-carbon", "anthropic/claude-fable-5.2"],
}

TOOLS = [
    {"id": "generate", "name": "Generate Image", "desc": "Create image from prompt"},
    {"id": "edit", "name": "Edit / Inpaint", "desc": "Modify regions of an image"},
    {"id": "upscale", "name": "Upscale", "desc": "Increase resolution"},
    {"id": "remove-bg", "name": "Remove Background", "desc": "Isolate subject"},
    {"id": "color-grade", "name": "Color Grade", "desc": "Adjust tones and mood"},
    {"id": "typography", "name": "Typography Overlay", "desc": "Add styled text"},
    {"id": "layout", "name": "Layout Compose", "desc": "Arrange elements"},
    {"id": "logo", "name": "Logo Design", "desc": "Generate logo concepts"},
    {"id": "resize", "name": "Social Resize", "desc": "Adapt for platforms"},
    {"id": "thumbnail", "name": "Thumbnail", "desc": "Create video thumbnail"},
    {"id": "style", "name": "Style Transfer", "desc": "Apply visual style"},
    {"id": "mockup", "name": "Mockup", "desc": "Place design in context"},
    {"id": "stock", "name": "Stock Search", "desc": "Pixabay images, video, music"},
]

class DesignRequest(BaseModel):
    tool: str
    prompt: str
    plan: Optional[str] = "free"
    extra: Optional[dict] = None

class StockRequest(BaseModel):
    query: str
    type: str = "image"  # image | video | music
    per_page: int = 10

def get_design_models(plan: str) -> List[str]:
    plan = (plan or "free").lower()
    pool = DESIGN_POOLS.get(plan, DESIGN_POOLS["free"])
    # Enforce the exact counts requested
    counts = {"free": 1, "basic": 1, "pro": 2, "pro_max": 3, "elite": 4}
    return pool[:counts.get(plan, 1)]

@router.get("/tools")
async def list_tools():
    return {"tools": TOOLS, "count": len(TOOLS)}

@router.post("/run")
async def run_design_tool(req: DesignRequest):
    tool = next((t for t in TOOLS if t["id"] == req.tool), None)
    if not tool:
        raise HTTPException(404, "Tool not found")

    models = get_design_models(req.plan or "free")
    prompt = f"Design tool: {tool['name']}\nTask: {req.prompt}\nGive a precise visual direction and parameters."

    answers = []
    for m in models:
        ans = await call_model(m, prompt)
        answers.append(f"[{m}]\n{ans}")

    combined = "\n\n---\n\n".join(answers) if len(answers) > 1 else answers[0]
    output = doom_wrap(combined, "content")

    return {
        "tool": req.tool,
        "status": "complete",
        "plan": req.plan or "free",
        "models_used": models,
        "model_count": len(models),
        "output": output,
    }

@router.post("/stock")
async def search_stock(req: StockRequest):
    """Search Pixabay for free stock images, videos, or music."""
    if not hasattr(settings, "pixabay_api_key") or not settings.pixabay_api_key:
        return {
            "status": "demo",
            "note": "Add PIXABAY_API_KEY to .env",
            "results": [],
        }

    endpoint = "https://pixabay.com/api/"
    if req.type == "video":
        endpoint = "https://pixabay.com/api/videos/"
    elif req.type == "music":
        endpoint = "https://pixabay.com/api/music/"  # Pixabay music endpoint if available

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            endpoint,
            params={
                "key": settings.pixabay_api_key,
                "q": req.query,
                "per_page": req.per_page,
            },
        )
        if resp.status_code != 200:
            return {"status": "error", "detail": resp.text}
        data = resp.json()
        return {
            "status": "ok",
            "type": req.type,
            "total": data.get("totalHits", 0),
            "results": data.get("hits", [])[:req.per_page],
        }
